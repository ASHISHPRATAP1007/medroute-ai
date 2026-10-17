"""
Idempotent first-run bootstrap — safe to run on every container start.

    python -m app.bootstrap

1. Ensures the default specializations exist.
2. If there is no SUPER_ADMIN yet and INITIAL_ADMIN_EMAIL +
   INITIAL_ADMIN_PASSWORD are set, creates that super admin.
3. If SEED_DEMO_DATA=true (and APP_ENV is not production), loads the demo
   dataset from app/seed.py — the same one `python -m app.seed` creates.

Unlike the old Dockerfile command (which ran the demo seed on every
start), this never creates the public Demo@1234 accounts unless you
explicitly ask for them.
"""
import asyncio

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStatus
from app.seed import ensure_specializations, seed


async def bootstrap() -> None:
    settings = get_settings()
    async with AsyncSessionLocal() as db:
        await ensure_specializations(db)

        has_super_admin = (
            await db.execute(select(User.id).where(User.role == UserRole.SUPER_ADMIN).limit(1))
        ).scalar_one_or_none() is not None

        if not has_super_admin and settings.INITIAL_ADMIN_EMAIL and settings.INITIAL_ADMIN_PASSWORD:
            if len(settings.INITIAL_ADMIN_PASSWORD) < 8:
                print("bootstrap: INITIAL_ADMIN_PASSWORD must be at least 8 characters — admin not created.")
            else:
                email = settings.INITIAL_ADMIN_EMAIL.strip().lower()
                taken = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
                if taken is not None:
                    taken.role = UserRole.SUPER_ADMIN
                    taken.status = UserStatus.APPROVED
                    taken.is_active = True
                    print(f"bootstrap: promoted existing user {email} to SUPER_ADMIN.")
                else:
                    db.add(User(
                        full_name=settings.INITIAL_ADMIN_NAME,
                        email=email,
                        phone=settings.INITIAL_ADMIN_PHONE,
                        password_hash=hash_password(settings.INITIAL_ADMIN_PASSWORD),
                        role=UserRole.SUPER_ADMIN,
                        status=UserStatus.APPROVED,
                    ))
                    print(f"bootstrap: created SUPER_ADMIN {email}.")
                await db.commit()

    if settings.SEED_DEMO_DATA:
        if settings.is_production:
            print("bootstrap: SEED_DEMO_DATA ignored because APP_ENV=production.")
        else:
            await seed()

    print("bootstrap: done.")


if __name__ == "__main__":
    asyncio.run(bootstrap())
