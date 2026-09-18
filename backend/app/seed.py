"""
Development seed script.

Usage (after `alembic upgrade head`):
    python -m app.seed

Creates clearly-fake demo data only. Never run this against production.
"""
import asyncio
import uuid

from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.area import Area
from app.models.city import City
from app.models.doctor import Doctor
from app.models.medical_shop import MedicalShop
from app.models.mr_profile import MRProfile
from app.models.specialization import DEFAULT_SPECIALIZATIONS, Specialization
from app.models.stockist import Stockist
from app.models.territory import Territory
from app.models.territory_mr import TerritoryMR
from app.models.user import User, UserRole, UserStatus

DEMO_PASSWORD = "Demo@1234"  # development only — never use in production


async def seed():
    async with AsyncSessionLocal() as db:
        # ---------- Specializations ----------
        existing = (await db.execute(select(Specialization.name))).scalars().all()
        specs_by_name: dict[str, Specialization] = {}
        for name in DEFAULT_SPECIALIZATIONS:
            if name not in existing:
                spec = Specialization(name=name)
                db.add(spec)
        await db.commit()
        result = await db.execute(select(Specialization))
        for s in result.scalars().all():
            specs_by_name[s.name] = s

        # ---------- Cities / Areas / Territories ----------
        city = City(name="Lucknow", state="Uttar Pradesh", country="India")
        db.add(city)
        await db.flush()

        area_gomti = Area(city_id=city.id, name="Gomti Nagar", pincode="226010")
        area_indira = Area(city_id=city.id, name="Indira Nagar", pincode="226016")
        area_aliganj = Area(city_id=city.id, name="Aliganj", pincode="226024")
        db.add_all([area_gomti, area_indira, area_aliganj])
        await db.flush()

        territory_north = Territory(area_id=area_gomti.id, name="Gomti North Territory", description="Northern Gomti Nagar sector")
        territory_south = Territory(area_id=area_gomti.id, name="Gomti South Territory", description="Southern Gomti Nagar sector")
        territory_indira = Territory(area_id=area_indira.id, name="Indira Nagar Territory")
        db.add_all([territory_north, territory_south, territory_indira])
        await db.flush()
        await db.commit()

        # ---------- Users: Super Admin + Admin ----------
        super_admin = User(
            full_name="Super Admin", email="superadmin@medroute.dev", phone="9000000001",
            password_hash=hash_password(DEMO_PASSWORD), role=UserRole.SUPER_ADMIN, status=UserStatus.APPROVED,
        )
        admin = User(
            full_name="Admin User", email="admin@medroute.dev", phone="9000000002",
            password_hash=hash_password(DEMO_PASSWORD), role=UserRole.ADMIN, status=UserStatus.APPROVED,
        )
        db.add_all([super_admin, admin])
        await db.flush()

        # ---------- MRs: 2 approved, 2 pending, 1 suspended ----------
        mr_defs = [
            ("Rahul Verma", "mr1.approved@medroute.dev", "9111111111", UserStatus.APPROVED, "MR001"),
            ("Priya Singh", "mr2.approved@medroute.dev", "9111111112", UserStatus.APPROVED, "MR002"),
            ("Aman Gupta", "mr3.pending@medroute.dev", "9111111113", UserStatus.PENDING, "MR003"),
            ("Neha Sharma", "mr4.pending@medroute.dev", "9111111114", UserStatus.PENDING, "MR004"),
            ("Vikas Yadav", "mr5.suspended@medroute.dev", "9111111115", UserStatus.SUSPENDED, "MR005"),
        ]
        mrs: list[User] = []
        for full_name, email, phone, mr_status, emp_id in mr_defs:
            mr = User(
                full_name=full_name, email=email, phone=phone,
                password_hash=hash_password(DEMO_PASSWORD), role=UserRole.MR, status=mr_status,
            )
            db.add(mr)
            await db.flush()
            db.add(MRProfile(
                user_id=mr.id, company_name="Acme Pharma", employee_id=emp_id,
                city="Lucknow", state="Uttar Pradesh", assigned_area="Gomti Nagar",
            ))
            mrs.append(mr)
        await db.commit()

        # Assign the two approved MRs to territories so their dashboards aren't empty.
        db.add(TerritoryMR(territory_id=territory_north.id, mr_id=mrs[0].id, assigned_by=admin.id))
        db.add(TerritoryMR(territory_id=territory_south.id, mr_id=mrs[1].id, assigned_by=admin.id))
        await db.commit()

        # ---------- 20 demo doctors ----------
        spec_list = list(specs_by_name.values())
        areas_cycle = [area_gomti.name, area_indira.name, area_aliganj.name]
        # Rough real-world coordinates around Lucknow so Phase 4's route
        # optimization has something meaningful to order.
        base_coords = [(26.8548, 81.0104), (26.8760, 81.0080), (26.8890, 80.9310)]
        for i in range(1, 21):
            lat_base, lng_base = base_coords[i % len(base_coords)]
            db.add(Doctor(
                full_name=f"Dr. Demo Doctor {i}",
                specialization_id=spec_list[i % len(spec_list)].id,
                qualification="MBBS, MD",
                phone=f"90000000{i:02d}",
                email=f"doctor{i}@example.dev",
                clinic_name=f"Demo Clinic {i}",
                hospital_name=f"Demo Hospital {i % 3 + 1}",
                address=f"{i} Demo Street",
                area=areas_cycle[i % len(areas_cycle)],
                city="Lucknow", state="Uttar Pradesh", pincode="226010",
                latitude=lat_base + (i * 0.001), longitude=lng_base + (i * 0.001),
                created_by=admin.id, updated_by=admin.id,
            ))

        # ---------- 10 demo medical shops ----------
        for i in range(1, 11):
            db.add(MedicalShop(
                name=f"Demo Medical Store {i}", contact_person=f"Contact Person {i}",
                phone=f"91000000{i:02d}", email=f"shop{i}@example.dev",
                address=f"{i} Shop Lane", area=areas_cycle[i % len(areas_cycle)],
                city="Lucknow", state="Uttar Pradesh", pincode="226010",
                created_by=admin.id, updated_by=admin.id,
            ))

        # ---------- 5 demo stockists ----------
        for i in range(1, 6):
            db.add(Stockist(
                name=f"Demo Stockist {i}", company_name=f"Demo Distributors {i}",
                contact_person=f"Stockist Contact {i}", phone=f"92000000{i:02d}",
                email=f"stockist{i}@example.dev", address=f"{i} Distributor Road",
                area=areas_cycle[i % len(areas_cycle)], city="Lucknow", state="Uttar Pradesh",
                pincode="226010", coverage_area="Lucknow Central",
                created_by=admin.id, updated_by=admin.id,
            ))

        await db.commit()
        print("Seed complete.")
        print(f"Super Admin: superadmin@medroute.dev / {DEMO_PASSWORD}")
        print(f"Admin:       admin@medroute.dev / {DEMO_PASSWORD}")
        print(f"MR (approved): mr1.approved@medroute.dev / {DEMO_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
