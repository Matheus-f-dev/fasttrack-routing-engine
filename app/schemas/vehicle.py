from uuid import UUID
from pydantic import BaseModel, Field

_EXAMPLE_ID = "b7e23ec2-9428-4f3e-9e49-a9e9d13bce40"


class VehicleBase(BaseModel):
    plate: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Vehicle license plate. Must be unique across the fleet.",
        examples=["ABC-1234"],
    )
    max_weight: float = Field(
        ...,
        gt=0,
        description="Maximum load capacity in kilograms. "
                    "Routes will be rejected if total package weight exceeds this value.",
        examples=[1500.0],
    )


class VehicleCreate(VehicleBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Medium capacity van",
                    "value": {"plate": "ABC-1234", "max_weight": 1500.0},
                },
                {
                    "summary": "Heavy duty truck",
                    "value": {"plate": "XYZ-9999", "max_weight": 8000.0},
                },
            ]
        }
    }


class VehicleUpdate(BaseModel):
    plate: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
        description="Updated license plate. Must remain unique.",
        examples=["DEF-5678"],
    )
    max_weight: float | None = Field(
        default=None,
        gt=0,
        description="Updated maximum load capacity in kilograms.",
        examples=[2000.0],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Update plate only",
                    "value": {"plate": "NEW-0001"},
                },
                {
                    "summary": "Update capacity only",
                    "value": {"max_weight": 2000.0},
                },
            ]
        }
    }


class VehicleResponse(VehicleBase):
    id: UUID = Field(
        description="Unique vehicle identifier (UUID v4), assigned on creation.",
        examples=[_EXAMPLE_ID],
    )

    model_config = {"from_attributes": True}
