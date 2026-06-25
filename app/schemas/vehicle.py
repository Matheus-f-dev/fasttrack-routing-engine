from uuid import UUID
from pydantic import BaseModel, Field


class VehicleBase(BaseModel):
    plate: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Vehicle license plate identifier",
        examples=["ABC-1234"],
    )
    max_weight: float = Field(
        ...,
        gt=0,
        description="Maximum load capacity in kilograms",
        examples=[1500.0],
    )


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
        description="Vehicle license plate identifier",
        examples=["ABC-1234"],
    )
    max_weight: float | None = Field(
        default=None,
        gt=0,
        description="Maximum load capacity in kilograms",
        examples=[1500.0],
    )


class VehicleResponse(VehicleBase):
    id: UUID = Field(description="Unique vehicle identifier", examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])

    model_config = {"from_attributes": True}
