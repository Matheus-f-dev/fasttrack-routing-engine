from uuid import UUID
from pydantic import BaseModel, Field


class PackageBase(BaseModel):
    recipient_name: str
    destination_x: float
    destination_y: float
    weight: float = Field(..., gt=0)
    access_cost: float = Field(..., ge=0)


class PackageCreate(PackageBase):
    pass


class PackageUpdate(BaseModel):
    recipient_name: str | None = None
    destination_x: float | None = None
    destination_y: float | None = None
    weight: float | None = Field(default=None, gt=0)
    access_cost: float | None = Field(default=None, ge=0)


class PackageResponse(PackageBase):
    id: UUID

    model_config = {"from_attributes": True}
