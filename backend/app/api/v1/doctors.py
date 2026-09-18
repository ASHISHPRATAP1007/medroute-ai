import uuid

from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_approved_mr, get_current_user, require_admin
from app.models.directory_mixins import EntityStatus
from app.models.user import User, UserRole
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.doctor import DoctorCreate, DoctorOut, DoctorUpdate
from app.schemas.place_enrichment import PlaceEnrichmentOut
from app.services import bulk_import_service, doctor_service, external_data_service

router = APIRouter(prefix="/doctors", tags=["Doctors"])


async def _resolve_area_restriction(db: AsyncSession, user: User) -> list[str] | None:
    """Admins/Super Admins see everything; MRs are restricted to their territories."""
    if user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN):
        return None
    return await doctor_service.get_mr_authorized_area_names(db, user.id)


@router.get("", response_model=ApiResponse[PaginatedData[DoctorOut]])
async def list_doctors_admin(
    search: str | None = None,
    specialization_id: uuid.UUID | None = None,
    city: str | None = None,
    area: str | None = None,
    status_filter: EntityStatus | None = Query(default=None, alias="status"),
    source: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="name"),
    sort_order: str = Query(default="asc"),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Admin-only: unrestricted doctor list with full filters (status/source included)."""
    items, total = await doctor_service.list_doctors(
        db, search=search, specialization_id=specialization_id, city=city, area=area,
        status_filter=status_filter, source=source, page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order, restrict_to_areas=None,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(data=PaginatedData(
        items=[DoctorOut.model_validate(d) for d in items], page=page, page_size=page_size,
        total_items=total, total_pages=total_pages,
    ))


@router.get("/mine", response_model=ApiResponse[PaginatedData[DoctorOut]])
async def list_doctors_for_mr(
    search: str | None = None,
    specialization_id: uuid.UUID | None = None,
    city: str | None = None,
    area: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="name"),
    sort_order: str = Query(default="asc"),
    db: AsyncSession = Depends(get_db),
    mr: User = Depends(get_current_approved_mr),
):
    """MR-facing doctor discovery — always territory-restricted server-side,
    regardless of any city/area query params the client sends."""
    restrict = await doctor_service.get_mr_authorized_area_names(db, mr.id)
    items, total = await doctor_service.list_doctors(
        db, search=search, specialization_id=specialization_id, city=city, area=area,
        status_filter=EntityStatus.ACTIVE, source=None, page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order, restrict_to_areas=restrict,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    return ApiResponse(data=PaginatedData(
        items=[DoctorOut.model_validate(d) for d in items], page=page, page_size=page_size,
        total_items=total, total_pages=total_pages,
    ))


@router.get("/export")
async def export_doctors(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)):
    """Downloads the full doctor directory as CSV. Registered before /{doctor_id}
    so the literal path "export" is never mistaken for a doctor UUID."""
    csv_text = await bulk_import_service.export_doctors_csv(db)
    return StreamingResponse(
        iter([csv_text]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=doctors_export.csv"},
    )


@router.post("/import")
async def import_doctors(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
):
    """
    Bulk-creates doctors from a CSV. Required columns: full_name,
    specialization (must match an existing specialization name),
    address, city, state. Bad rows are skipped and reported —
    the whole file is never rejected for one bad row.
    """
    raw = await file.read()
    try:
        csv_text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return ApiResponse(success=False, message="File must be UTF-8 encoded CSV.", errors=["Invalid encoding."])

    result = await bulk_import_service.import_doctors_csv(db, csv_text, admin.id)
    return ApiResponse(
        message=f"Imported {result['created']} doctor(s), skipped {result['skipped']}.",
        data=result,
    )


@router.get("/{doctor_id}", response_model=ApiResponse[DoctorOut])
async def get_doctor(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """Accessible to Admin (unrestricted) and approved MR (territory-restricted)."""
    if user.role == UserRole.MR and user.status.value != "APPROVED":
        from fastapi import HTTPException, status as http_status
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Your MR account is not yet approved.")
    restrict = await _resolve_area_restriction(db, user)
    doctor = await doctor_service.get_doctor(db, doctor_id, restrict_to_areas=restrict)
    return ApiResponse(data=DoctorOut.model_validate(doctor))


@router.post("", response_model=ApiResponse[DoctorOut], status_code=201)
async def create_doctor(payload: DoctorCreate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    doctor = await doctor_service.create_doctor(db, payload, admin.id)
    return ApiResponse(message="Doctor created.", data=DoctorOut.model_validate(doctor))


@router.put("/{doctor_id}", response_model=ApiResponse[DoctorOut])
async def update_doctor(doctor_id: uuid.UUID, payload: DoctorUpdate, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    doctor = await doctor_service.update_doctor(db, doctor_id, payload, admin.id)
    return ApiResponse(message="Doctor updated.", data=DoctorOut.model_validate(doctor))


@router.post("/{doctor_id}/deactivate", response_model=ApiResponse[DoctorOut])
async def deactivate_doctor(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    doctor = await doctor_service.set_doctor_status(db, doctor_id, EntityStatus.INACTIVE, admin.id)
    return ApiResponse(message="Doctor deactivated.", data=DoctorOut.model_validate(doctor))


@router.post("/{doctor_id}/activate", response_model=ApiResponse[DoctorOut])
async def activate_doctor(doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    doctor = await doctor_service.set_doctor_status(db, doctor_id, EntityStatus.ACTIVE, admin.id)
    return ApiResponse(message="Doctor activated.", data=DoctorOut.model_validate(doctor))


# ---------- Phase 2: Google Places enrichment ----------

@router.get("/{doctor_id}/external-data", response_model=ApiResponse[PlaceEnrichmentOut | None])
async def get_doctor_external_data(
    doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)
):
    """
    Returns cached Google Places data if it's ever been synced, or
    data=None if not — never fabricated. Accessible to Admin and
    territory-authorized MRs, same access rule as the doctor record
    itself.
    """
    restrict = await _resolve_area_restriction(db, user)
    await doctor_service.get_doctor(db, doctor_id, restrict_to_areas=restrict)  # 404s if unauthorized
    enrichment = await external_data_service.get_cached_enrichment(db, "Doctor", doctor_id)
    return ApiResponse(data=PlaceEnrichmentOut.model_validate(enrichment) if enrichment else None)


@router.post("/{doctor_id}/sync-external", response_model=ApiResponse[PlaceEnrichmentOut])
async def sync_doctor_external_data(
    doctor_id: uuid.UUID, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)
):
    """
    Admin-triggered, on-demand Google Places sync. Not automatic —
    Google Places has real per-call cost, so this is a deliberate
    action, not something that fires on every profile view.
    """
    doctor = await doctor_service.get_doctor(db, doctor_id)
    enrichment = await external_data_service.sync_place_details(
        db, entity_type="Doctor", entity_id=doctor.id,
        search_name=doctor.full_name, address=doctor.address, city=doctor.city,
        admin_id=admin.id,
    )
    return ApiResponse(message="Google Places data synced.", data=PlaceEnrichmentOut.model_validate(enrichment))
