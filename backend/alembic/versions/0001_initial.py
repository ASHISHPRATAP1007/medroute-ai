"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-13

NOTE: This migration was written by hand to mirror app/models exactly,
because this development environment has no network access to run
PostgreSQL and generate it via `alembic revision --autogenerate`. It
has NOT been executed against a real database. Before relying on it,
run it against a real Postgres instance and fix anything that
`alembic upgrade head` reports.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = postgresql.ENUM("SUPER_ADMIN", "ADMIN", "MR", name="user_role")
    user_status = postgresql.ENUM("PENDING", "APPROVED", "REJECTED", "SUSPENDED", "INACTIVE", name="user_status")
    entity_status = postgresql.ENUM("ACTIVE", "INACTIVE", name="entity_status")
    entity_source = postgresql.ENUM("ADMIN", "IMPORT", "EXTERNAL", name="entity_source")
    territory_status = postgresql.ENUM("ACTIVE", "INACTIVE", name="territory_status")
    audit_action = postgresql.ENUM(
        "USER_REGISTERED", "MR_APPROVED", "MR_REJECTED", "MR_SUSPENDED", "MR_ACTIVATED",
        "DOCTOR_CREATED", "DOCTOR_UPDATED", "DOCTOR_DEACTIVATED", "DOCTOR_ACTIVATED",
        "SHOP_CREATED", "SHOP_UPDATED", "SHOP_DEACTIVATED",
        "STOCKIST_CREATED", "STOCKIST_UPDATED", "STOCKIST_DEACTIVATED",
        "TERRITORY_CREATED", "TERRITORY_UPDATED", "MR_ASSIGNED_TO_TERRITORY", "MR_REMOVED_FROM_TERRITORY",
        name="audit_action",
    )

    bind = op.get_bind()
    for enum_type in (user_role, user_status, entity_status, entity_source, territory_status, audit_action):
        enum_type.create(bind, checkfirst=True)

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')  # for gen_random_uuid() default, if needed

    # ---------- users ----------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("status", user_status, nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("phone", name="uq_users_phone"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_status", "users", ["status"])

    # ---------- mr_profiles ----------
    op.create_table(
        "mr_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("company_name", sa.String(150), nullable=False),
        sa.Column("employee_id", sa.String(50), nullable=False),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("assigned_area", sa.String(150), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("user_id", name="uq_mr_profiles_user_id"),
        sa.UniqueConstraint("employee_id", "company_name", name="uq_mr_profiles_employee_company"),
    )

    # ---------- refresh_tokens ----------
    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])

    # ---------- specializations ----------
    op.create_table(
        "specializations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", name="uq_specializations_name"),
    )

    # ---------- cities ----------
    op.create_table(
        "cities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("state", sa.String(100), nullable=False),
        sa.Column("country", sa.String(100), nullable=False, server_default="India"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("name", "state", "country", name="uq_city_name_state_country"),
    )

    # ---------- areas ----------
    op.create_table(
        "areas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("pincode", sa.String(10), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("city_id", "name", name="uq_area_city_name"),
    )
    op.create_index("ix_areas_city_id", "areas", ["city_id"])

    # ---------- territories ----------
    op.create_table(
        "territories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("area_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("areas.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("status", territory_status, nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("area_id", "name", name="uq_territory_area_name"),
    )
    op.create_index("ix_territories_area_id", "territories", ["area_id"])

    # ---------- territory_mrs ----------
    op.create_table(
        "territory_mrs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("territory_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("territories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("mr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.UniqueConstraint("territory_id", "mr_id", name="uq_territory_mr"),
    )
    op.create_index("ix_territory_mrs_territory_id", "territory_mrs", ["territory_id"])
    op.create_index("ix_territory_mrs_mr_id", "territory_mrs", ["mr_id"])

    # ---------- shared columns for doctors / medical_shops / stockists ----------
    def directory_columns():
        return [
            sa.Column("address", sa.String(500), nullable=False),
            sa.Column("area", sa.String(150), nullable=True),
            sa.Column("city", sa.String(100), nullable=False),
            sa.Column("state", sa.String(100), nullable=False),
            sa.Column("pincode", sa.String(10), nullable=True),
            sa.Column("latitude", sa.Numeric(9, 6), nullable=True),
            sa.Column("longitude", sa.Numeric(9, 6), nullable=True),
            sa.Column("status", entity_status, nullable=False, server_default="ACTIVE"),
            sa.Column("source", entity_source, nullable=False, server_default="ADMIN"),
            sa.Column("external_provider", sa.String(50), nullable=True),
            sa.Column("external_place_id", sa.String(255), nullable=True),
            sa.Column("last_external_sync", sa.String(50), nullable=True),
            sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("updated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        ]

    # ---------- doctors ----------
    op.create_table(
        "doctors",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("full_name", sa.String(150), nullable=False),
        sa.Column("specialization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("specializations.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("qualification", sa.String(150), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("clinic_name", sa.String(200), nullable=True),
        sa.Column("hospital_name", sa.String(200), nullable=True),
        *directory_columns(),
        sa.CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_doctor_lat_range"),
        sa.CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_doctor_lng_range"),
    )
    for col in ("full_name", "city", "area", "status", "specialization_id"):
        op.create_index(f"ix_doctors_{col}", "doctors", [col])

    # ---------- medical_shops ----------
    op.create_table(
        "medical_shops",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("contact_person", sa.String(150), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        *directory_columns(),
        sa.CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_shop_lat_range"),
        sa.CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_shop_lng_range"),
    )
    for col in ("name", "city", "area", "status"):
        op.create_index(f"ix_shops_{col}", "medical_shops", [col])

    # ---------- stockists ----------
    op.create_table(
        "stockists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("company_name", sa.String(200), nullable=True),
        sa.Column("contact_person", sa.String(150), nullable=True),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("coverage_area", sa.String(255), nullable=True),
        *directory_columns(),
        sa.CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)", name="ck_stockist_lat_range"),
        sa.CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)", name="ck_stockist_lng_range"),
    )
    for col in ("name", "city", "area", "status"):
        op.create_index(f"ix_stockists_{col}", "stockists", [col])

    # ---------- audit_logs ----------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", audit_action, nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("ip_address", postgresql.INET, nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("stockists")
    op.drop_table("medical_shops")
    op.drop_table("doctors")
    op.drop_table("territory_mrs")
    op.drop_table("territories")
    op.drop_table("areas")
    op.drop_table("cities")
    op.drop_table("specializations")
    op.drop_table("refresh_tokens")
    op.drop_table("mr_profiles")
    op.drop_table("users")

    bind = op.get_bind()
    for enum_name in ("audit_action", "territory_status", "entity_source", "entity_status", "user_status", "user_role"):
        postgresql.ENUM(name=enum_name).drop(bind, checkfirst=True)
