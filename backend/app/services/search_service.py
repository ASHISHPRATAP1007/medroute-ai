"""
Global search (topbar) — one query, grouped results across the directory.

Same access rules as the individual list endpoints:
- Admins search everything, including MR accounts.
- MRs only see ACTIVE doctors/shops/stockists inside their assigned
  territories (server-side, via get_mr_authorized_area_names) and never
  see other users.
"""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.directory_mixins import EntityStatus
from app.models.doctor import Doctor
from app.models.medical_shop import MedicalShop
from app.models.stockist import Stockist
from app.models.user import User, UserRole
from app.services import doctor_service


def _like(term: str) -> str:
    escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


async def global_search(db: AsyncSession, user: User, term: str, limit: int) -> dict:
    like = _like(term.strip())
    is_admin = user.role in (UserRole.ADMIN, UserRole.SUPER_ADMIN)
    restrict = None if is_admin else await doctor_service.get_mr_authorized_area_names(db, user.id)

    empty = {"doctors": [], "medical_shops": [], "stockists": [], "mrs": []}
    if restrict is not None and not restrict:
        return empty  # MR with no territory sees nothing, same as the list pages

    def scoped(query, model):
        if restrict is not None:
            query = query.where(doctor_service.area_matches(model.area, restrict), model.status == EntityStatus.ACTIVE)
        return query

    doctors_q = scoped(
        select(Doctor).where(or_(
            Doctor.full_name.ilike(like, escape="\\"),
            Doctor.clinic_name.ilike(like, escape="\\"),
            Doctor.hospital_name.ilike(like, escape="\\"),
            Doctor.area.ilike(like, escape="\\"),
        )),
        Doctor,
    ).order_by(Doctor.full_name).limit(limit)

    def entity_q(model):
        return scoped(
            select(model).where(or_(
                model.name.ilike(like, escape="\\"),
                model.contact_person.ilike(like, escape="\\"),
                model.area.ilike(like, escape="\\"),
            )),
            model,
        ).order_by(model.name).limit(limit)

    result = {
        "doctors": list((await db.execute(doctors_q)).scalars().all()),
        "medical_shops": list((await db.execute(entity_q(MedicalShop))).scalars().all()),
        "stockists": list((await db.execute(entity_q(Stockist))).scalars().all()),
        "mrs": [],
    }

    if is_admin:
        mrs_q = (
            select(User)
            .where(User.role == UserRole.MR)
            .where(or_(
                User.full_name.ilike(like, escape="\\"),
                User.email.ilike(like, escape="\\"),
                User.phone.ilike(like, escape="\\"),
            ))
            .order_by(User.full_name)
            .limit(limit)
        )
        result["mrs"] = list((await db.execute(mrs_q)).scalars().all())

    return result
