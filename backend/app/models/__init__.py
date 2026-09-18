"""
Import every model here so that a single `from app.models import *`
(used by alembic/env.py) registers all tables on Base.metadata.
"""
from app.models.user import User, UserRole, UserStatus  # noqa: F401
from app.models.mr_profile import MRProfile  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.specialization import Specialization, DEFAULT_SPECIALIZATIONS  # noqa: F401
from app.models.city import City  # noqa: F401
from app.models.area import Area  # noqa: F401
from app.models.territory import Territory, TerritoryStatus  # noqa: F401
from app.models.territory_mr import TerritoryMR  # noqa: F401
from app.models.doctor import Doctor  # noqa: F401
from app.models.medical_shop import MedicalShop  # noqa: F401
from app.models.stockist import Stockist  # noqa: F401
from app.models.audit_log import AuditLog, AuditAction  # noqa: F401
from app.models.directory_mixins import EntityStatus, EntitySource  # noqa: F401
from app.models.place_enrichment import PlaceEnrichment  # noqa: F401 (Phase 2)
from app.models.visit import Visit, VisitStatus  # noqa: F401 (Phase 4)
from app.models.notification import Notification, NotificationType  # noqa: F401 (Phase 5)
