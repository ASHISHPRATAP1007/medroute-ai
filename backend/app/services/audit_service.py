import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditAction, AuditLog


async def log_action(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None,
    action: AuditAction,
    entity_type: str,
    entity_id: uuid.UUID | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """
    Adds an AuditLog row to the current session WITHOUT committing —
    callers commit as part of their own transaction so the audit entry
    is atomic with the action it records.
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
