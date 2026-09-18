"""phase 2: google places enrichment cache

Revision ID: 0002_phase2_places
Revises: 0001_initial
Create Date: 2026-09-14

Same caveat as 0001_initial: hand-written (no live Postgres available
to autogenerate against), not yet applied to a real database.

Adding values to an existing Postgres ENUM type cannot run inside the
same transaction as other DDL in older Postgres versions, so the enum
ALTER is wrapped in an autocommit block, separate from the table create.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002_phase2_places"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New audit_action enum values (Postgres requires ADD VALUE to run
    # outside a transaction block on versions before PG 12's improved
    # handling — the autocommit_block keeps this safe across versions).
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'EXTERNAL_SYNC_SUCCEEDED'")
        op.execute("ALTER TYPE audit_action ADD VALUE IF NOT EXISTS 'EXTERNAL_SYNC_FAILED'")

    op.create_table(
        "place_enrichments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("place_id", sa.String(255), nullable=False),
        sa.Column("rating", sa.Float, nullable=True),
        sa.Column("user_ratings_total", sa.Integer, nullable=True),
        sa.Column("opening_hours", postgresql.JSONB, nullable=True),
        sa.Column("photos", postgresql.JSONB, nullable=True),
        sa.Column("reviews", postgresql.JSONB, nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_sync_status", sa.String(20), nullable=False, server_default="SUCCESS"),
        sa.Column("last_sync_error", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("entity_type", "entity_id", name="uq_place_enrichment_entity"),
    )
    op.create_index("ix_place_enrichments_entity", "place_enrichments", ["entity_type", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_place_enrichments_entity", table_name="place_enrichments")
    op.drop_table("place_enrichments")
    # Postgres does not support removing individual enum values without
    # recreating the type; left as a manual step if a true downgrade is
    # ever needed (rare in practice for additive enum values).
