from uuid import UUID
from pydantic import BaseModel, Field


class HubBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Hub display name",
        examples=["Central Warehouse"],
    )
    x: float = Field(
        ...,
        description="Hub X coordinate on the routing map",
        examples=[0.0],
    )
    y: float = Field(
        ...,
        description="Hub Y coordinate on the routing map",
        examples=[0.0],
    )


class HubCreate(HubBase):
    pass


class HubUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Hub display name",
        examples=["Central Warehouse"],
    )
    x: float | None = Field(
        default=None,
        description="Hub X coordinate on the routing map",
        examples=[10.0],
    )
    y: float | None = Field(
        default=None,
        description="Hub Y coordinate on the routing map",
        examples=[5.0],
    )


class HubResponse(HubBase):
    id: UUID = Field(
        description="Unique hub identifier",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    is_main: bool = Field(
        description="Whether this hub is the main dispatch hub",
        examples=[False],
    )

    model_config = {"from_attributes": True}
