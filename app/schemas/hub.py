from uuid import UUID
from pydantic import BaseModel, Field

_EXAMPLE_ID = "c1a2b3c4-d5e6-7890-abcd-ef1234567890"


class HubBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Hub display name. Must be unique across all hubs.",
        examples=["North Warehouse"],
    )
    x: float = Field(
        ...,
        description="Hub X coordinate on the routing map. "
                    "The main hub is always at (0, 0).",
        examples=[15.0],
    )
    y: float = Field(
        ...,
        description="Hub Y coordinate on the routing map.",
        examples=[20.0],
    )


class HubCreate(HubBase):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Northern distribution point",
                    "value": {"name": "North Warehouse", "x": 0.0, "y": 30.0},
                },
                {
                    "summary": "Eastern sorting facility",
                    "value": {"name": "East Sorting", "x": 40.0, "y": 5.0},
                },
            ]
        }
    }


class HubUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated hub name. Must remain unique.",
        examples=["North Warehouse v2"],
    )
    x: float | None = Field(
        default=None,
        description="Updated X coordinate.",
        examples=[12.0],
    )
    y: float | None = Field(
        default=None,
        description="Updated Y coordinate.",
        examples=[28.0],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "summary": "Rename hub",
                    "value": {"name": "North Warehouse v2"},
                },
                {
                    "summary": "Reposition hub",
                    "value": {"x": 12.0, "y": 28.0},
                },
            ]
        }
    }


class HubResponse(HubBase):
    id: UUID = Field(
        description="Unique hub identifier (UUID v4), assigned on creation.",
        examples=[_EXAMPLE_ID],
    )
    is_main: bool = Field(
        description="Whether this hub is the main dispatch origin. "
                    "The main hub cannot be modified or deleted.",
        examples=[False],
    )

    model_config = {"from_attributes": True}
