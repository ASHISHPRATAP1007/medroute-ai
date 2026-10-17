from pydantic import BaseModel

from app.schemas.auth import UserPublic
from app.schemas.doctor import DoctorOut
from app.schemas.medical_shop import MedicalShopOut
from app.schemas.stockist import StockistOut


class GlobalSearchOut(BaseModel):
    doctors: list[DoctorOut]
    medical_shops: list[MedicalShopOut]
    stockists: list[StockistOut]
    mrs: list[UserPublic]  # always empty for MR callers
