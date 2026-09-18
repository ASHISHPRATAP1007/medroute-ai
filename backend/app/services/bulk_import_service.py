"""
Phase 5 — bulk import/export for the doctor directory.

Export produces a real CSV from the current DB rows. Import parses a
real CSV (Python's stdlib csv module, no external dependency), matches
each row's "specialization" column to an existing Specialization by
name (case-insensitive), and reports per-row errors rather than
failing the whole batch on one bad row. Imported doctors get
source=IMPORT (an EntitySource value Phase 1 already defined for
exactly this purpose) so they're distinguishable from admin-entered or
Phase 2 externally-synced records.
"""
import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.directory_mixins import EntitySource
from app.models.doctor import Doctor
from app.models.specialization import Specialization
from app.models.audit_log import AuditAction
from app.services.audit_service import log_action

EXPORT_COLUMNS = [
    "full_name", "specialization", "qualification", "phone", "email",
    "clinic_name", "hospital_name", "address", "area", "city", "state",
    "pincode", "latitude", "longitude", "status",
]

REQUIRED_IMPORT_COLUMNS = ["full_name", "specialization", "address", "city", "state"]


async def export_doctors_csv(db: AsyncSession) -> str:
    result = await db.execute(select(Doctor))
    doctors = list(result.scalars().all())

    spec_result = await db.execute(select(Specialization))
    spec_names = {s.id: s.name for s in spec_result.scalars().all()}

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS)
    writer.writeheader()
    for doctor in doctors:
        writer.writerow({
            "full_name": doctor.full_name,
            "specialization": spec_names.get(doctor.specialization_id, ""),
            "qualification": doctor.qualification or "",
            "phone": doctor.phone or "",
            "email": doctor.email or "",
            "clinic_name": doctor.clinic_name or "",
            "hospital_name": doctor.hospital_name or "",
            "address": doctor.address,
            "area": doctor.area or "",
            "city": doctor.city,
            "state": doctor.state,
            "pincode": doctor.pincode or "",
            "latitude": doctor.latitude if doctor.latitude is not None else "",
            "longitude": doctor.longitude if doctor.longitude is not None else "",
            "status": doctor.status.value,
        })
    return buffer.getvalue()


async def import_doctors_csv(db: AsyncSession, csv_text: str, admin_id: uuid.UUID) -> dict:
    spec_result = await db.execute(select(Specialization))
    spec_by_name = {s.name.strip().lower(): s for s in spec_result.scalars().all()}

    reader = csv.DictReader(io.StringIO(csv_text))

    missing_columns = [c for c in REQUIRED_IMPORT_COLUMNS if c not in (reader.fieldnames or [])]
    if missing_columns:
        return {"created": 0, "skipped": 0, "errors": [f"Missing required column(s): {', '.join(missing_columns)}"]}

    created = 0
    skipped = 0
    errors: list[str] = []

    for row_number, row in enumerate(reader, start=2):  # header is row 1
        full_name = (row.get("full_name") or "").strip()
        specialization_name = (row.get("specialization") or "").strip()
        address = (row.get("address") or "").strip()
        city = (row.get("city") or "").strip()
        state = (row.get("state") or "").strip()

        if not (full_name and specialization_name and address and city and state):
            skipped += 1
            errors.append(f"Row {row_number}: missing a required field (full_name/specialization/address/city/state).")
            continue

        specialization = spec_by_name.get(specialization_name.lower())
        if specialization is None:
            skipped += 1
            errors.append(f"Row {row_number}: unknown specialization '{specialization_name}'.")
            continue

        try:
            latitude = float(row["latitude"]) if row.get("latitude") else None
            longitude = float(row["longitude"]) if row.get("longitude") else None
        except ValueError:
            skipped += 1
            errors.append(f"Row {row_number}: latitude/longitude must be numeric.")
            continue

        doctor = Doctor(
            full_name=full_name, specialization_id=specialization.id,
            qualification=row.get("qualification") or None, phone=row.get("phone") or None,
            email=row.get("email") or None, clinic_name=row.get("clinic_name") or None,
            hospital_name=row.get("hospital_name") or None, address=address,
            area=row.get("area") or None, city=city, state=state,
            pincode=row.get("pincode") or None, latitude=latitude, longitude=longitude,
            source=EntitySource.IMPORT, created_by=admin_id, updated_by=admin_id,
        )
        db.add(doctor)
        created += 1

    if created:
        await log_action(
            db, user_id=admin_id, action=AuditAction.DOCTOR_CREATED, entity_type="Doctor",
            description=f"Bulk import created {created} doctor(s), skipped {skipped}.",
        )
        await db.commit()

    return {"created": created, "skipped": skipped, "errors": errors}
