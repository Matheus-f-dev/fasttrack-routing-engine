from uuid import UUID
from pydantic import BaseModel, Field

_EXAMPLE_ID = "a3bb189e-8bf9-3888-9912-ace4e6543002"

_EXAMPLE_PACKAGE = {
    "recipient_name": "Maria Silva",
    "destination_x": 8.0,
    "destination_y": 6.0,
    "weight": 3.5,
    "access_cost": 12.0,
}


class PackageBase(BaseModel):
    recipient_name: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Full name of the package recipient.",
        examples=["Maria Silva"],
    )
    destination_x: float = Field(
        ...,
        description="X coordinate of the delivery destination on the routing map.",
        examples=[8.0],
    )
    destination_y: float = Field(
        ...,
        description="Y coordinate of the delivery destination on the routing map.",
        examples=[6.0],
    )
    weight: float = Field(
        ...,
        gt=0,
        description="Package weight in kilograms. Must be greater than 0. "
                    "The sum of all package weights in a route cannot exceed the vehicle's `max_weight`.",
        examples=[3.5],
    )
    access_cost: float = Field(
        ...,
        ge=0,
        description="Cost to access the delivery point (tolls, restricted area fees, etc.). "
                    "Used by the `economic` strategy to minimise total delivery cost. Must be ≥ 0.",
        examples=[12.0],
    )


class PackageCreate(PackageBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Standard parcel",
                    "value": _EXAMPLE_PACKAGE,
                },
                {
                    "summary": "Lightweight, expensive access area",
                    "value": {
                        "recipient_name": "João Pereira",
                        "destination_x": -3.0,
                        "destination_y": 14.0,
                        "weight": 0.5,
                        "access_cost": 80.0,
                    },
                },
            ]
        }
    }


class PackageUpdate(BaseModel):
    recipient_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
        description="Updated recipient name.",
        examples=["Ana Costa"],
    )
    destination_x: float | None = Field(
        default=None,
        description="Updated X coordinate.",
        examples=[5.0],
    )
    destination_y: float | None = Field(
        default=None,
        description="Updated Y coordinate.",
        examples=[5.0],
    )
    weight: float | None = Field(
        default=None,
        gt=0,
        description="Updated weight in kilograms.",
        examples=[2.0],
    )
    access_cost: float | None = Field(
        default=None,
        ge=0,
        description="Updated access cost.",
        examples=[5.0],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Update destination only",
                    "value": {"destination_x": 10.0, "destination_y": 3.0},
                },
                {
                    "summary": "Update weight and access cost",
                    "value": {"weight": 5.0, "access_cost": 20.0},
                },
            ]
        }
    }


class PackageResponse(PackageBase):
    id: UUID = Field(
        description="Unique package identifier (UUID v4), assigned on creation.",
        examples=[_EXAMPLE_ID],
    )

    model_config = {"from_attributes": True}
