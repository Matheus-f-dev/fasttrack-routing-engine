from uuid import UUID
from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    vehicle_id: UUID = Field(description="ID of the vehicle to use", examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    package_ids: list[UUID] = Field(
        description="Ordered list of package IDs to deliver",
        examples=[["3fa85f64-5717-4562-b3fc-2c963f66afa6"]],
    )


class DeliveryStop(BaseModel):
    sequence: int = Field(description="Delivery order position (1-based)", examples=[1])
    package_id: UUID = Field(description="ID of the package delivered at this stop", examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"])
    recipient_name: str = Field(description="Package recipient name", examples=["John Doe"])
    destination_x: float = Field(description="Stop X coordinate", examples=[3.0])
    destination_y: float = Field(description="Stop Y coordinate", examples=[4.0])


class RouteResponse(BaseModel):
    route_type: str = Field(description="Strategy used to calculate this route", examples=["express"])
    total_distance: float = Field(description="Total euclidean distance of the route in map units", examples=[12.5])
    delivery_order: list[DeliveryStop] = Field(description="Ordered list of delivery stops")
