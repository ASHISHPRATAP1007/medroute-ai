"""refresh tokens: switch to indexed HMAC-SHA256 lookup

Revision ID: 0005_refresh_token_hmac
Revises: 0004_phase5_notifications
Create Date: 2026-10-17

Refresh tokens used to be stored as bcrypt hashes, which forced
/auth/refresh to scan and bcrypt-verify every live token (O(n)). They are
now stored as a deterministic HMAC-SHA256 so the row can be found with an
indexed equality lookup.

Existing bcrypt-hashed rows can never match the new scheme, so they are
revoked here. Effect for users: anyone logged in before this migration is
asked to log in once more when their access token expires. No passwords
are affected.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "0005_refresh_token_hmac"
down_revision: Union[str, None] = "0004_phase5_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "UPDATE refresh_tokens SET revoked = true, revoked_at = now() "
        "WHERE revoked = false AND token_hash LIKE '$2%'"
    )
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
