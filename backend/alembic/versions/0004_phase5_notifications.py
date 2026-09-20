"""phase 5: notifications table

Revision ID: 0004_phase5_notifications
Revises: 0003_phase4_visits
Create Date: 2026-09-16

Same caveat as prior migrations: hand-written, not yet applied to a
real database in this environment.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0004_phase5_notifications"
down_revision: Union[str, None] = "0003_phase4_visits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # notification_type ENUM
    # ---------------------------------------------------------
    notification_type = postgresql.ENUM(
        "INFO",
        "SUCCESS",
        "WARNING",
        name="notification_type",
        create_type=False,
    )

    notification_type.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ---------------------------------------------------------
    # notifications table
    # ---------------------------------------------------------
    op.create_table(
        "notifications",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),

        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey(
                "users.id",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),

        sa.Column(
            "title",
            sa.String(200),
            nullable=False,
        ),

        sa.Column(
            "message",
            sa.Text,
            nullable=False,
        ),

        sa.Column(
            "type",
            notification_type,
            nullable=False,
            server_default="INFO",
        ),

        sa.Column(
            "is_read",
            sa.Boolean,
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # ---------------------------------------------------------
    # Indexes
    # ---------------------------------------------------------
    op.create_index(
        "ix_notifications_user_id",
        "notifications",
        ["user_id"],
    )

    op.create_index(
        "ix_notifications_is_read",
        "notifications",
        ["is_read"],
    )


def downgrade() -> None:
    # ---------------------------------------------------------
    # Drop indexes
    # ---------------------------------------------------------
    op.drop_index(
        "ix_notifications_is_read",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notifications_user_id",
        table_name="notifications",
    )

    # ---------------------------------------------------------
    # Drop notifications table
    # ---------------------------------------------------------
    op.drop_table("notifications")

    # ---------------------------------------------------------
    # Drop notification_type ENUM
    # ---------------------------------------------------------
    postgresql.ENUM(
        name="notification_type"
    ).drop(
        op.get_bind(),
        checkfirst=True,
    )
