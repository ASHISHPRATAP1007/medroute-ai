"""phase 4: visits table

Revision ID: 0003_phase4_visits
Revises: 0002_phase2_places
Create Date: 2026-09-14

Same caveat as prior migrations: hand-written, not yet applied to a
real database in this environment.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_phase4_visits"
down_revision: Union[str, None] = "0002_phase2_places"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    visit_status = postgresql.ENUM("PLANNED", "COMPLETED", "CANCELLED", "MISSED", name="visit_status")
    visit_status.create(op.get_bind(), checkfirst=True)

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'VISIT_PLANNED'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'VISIT_COMPLETED'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'VISIT_CANCELLED'")

    op.create_table(
        "visits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("mr_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("doctor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("scheduled_date", sa.Date, nullable=False),
        sa.Column("status", visit_status, nullable=False, server_default="PLANNED"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("outcome", sa.Text, nullable=True),
        sa.Column("follow_up_date", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("mr_id", "doctor_id", "scheduled_date", name="uq_visit_mr_doctor_date"),
    )
    op.create_index("ix_visits_mr_id", "visits", ["mr_id"])
    op.create_index("ix_visits_doctor_id", "visits", ["doctor_id"])
    op.create_index("ix_visits_scheduled_date", "visits", ["scheduled_date"])
    op.create_index("ix_visits_status", "visits", ["status"])
    op.create_index("ix_visits_follow_up_date", "visits", ["follow_up_date"])


def downgrade() -> None:
    op.drop_index("ix_visits_follow_up_date", table_name="visits")
    op.drop_index("ix_visits_status", table_name="visits")
    op.drop_index("ix_visits_scheduled_date", table_name="visits")
    op.drop_index("ix_visits_doctor_id", table_name="visits")
    op.drop_index("ix_visits_mr_id", table_name="visits")
    op.drop_table("visits")
