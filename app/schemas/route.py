from uuid import UUID
from pydantic import BaseModel, Field


class RouteRequest(BaseModel):
    vehicle_id: UUID = Field(
        description="ID of the vehicle assigned to this route",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    package_ids: list[UUID] = Field(
        min_length=1,
        description="List of package IDs to deliver. At least one package is required.",
        examples=[["3fa85f64-5717-4562-b3fc-2c963f66afa6"]],
    )


class DeliveryStop(BaseModel):
    sequence: int = Field(description="Delivery order position (1-based)", examples=[1])
    package_id: UUID = Field(
        description="ID of the package delivered at this stop",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    recipient_name: str = Field(description="Package recipient name", examples=["John Doe"])
    destination_x: float = Field(description="Stop X coordinate", examples=[3.0])
    destination_y: float = Field(description="Stop Y coordinate", examples=[4.0])


class VisitedHubResponse(BaseModel):
    id: UUID = Field(
        description="Hub unique identifier",
        examples=["3fa85f64-5717-4562-b3fc-2c963f66afa6"],
    )
    name: str = Field(description="Hub name", examples=["North Warehouse"])
    x: float = Field(description="Hub X coordinate", examples=[5.0])
    y: float = Field(description="Hub Y coordinate", examples=[5.0])


class RouteResponse(BaseModel):
    route_type: str = Field(
        description="Strategy used to calculate this route",
        examples=["express"],
    )
    total_distance: float = Field(
        description="Total euclidean distance of the route in map units",
        examples=[12.5],
    )
    total_cost: float = Field(
        description="Sum of access_cost of all delivered packages",
        examples=[30.0],
    )
    delivery_order: list[DeliveryStop] = Field(
        description="Ordered list of delivery stops produced by this strategy",
    )
    extra_package_collected: bool = Field(
        default=False,
        description="Whether a secondary hub was used to collect an additional package en route",
        examples=[True],
    )
    visited_hub: VisitedHubResponse | None = Field(
        default=None,
        description="Secondary hub visited during the route, if any (strategic_hub only)",
    )


class AllRoutesResponse(BaseModel):
    express_route: RouteResponse = Field(
        description=(
            "Route produced by **ExpressRouteStrategy**: nearest-neighbor greedy algorithm. "
            "Minimizes total euclidean distance. Ignores access_cost. "
            "Best choice when delivery speed is the only priority."
        ),
    )
    economic_route: RouteResponse = Field(
        description=(
            "Route produced by **EconomicRouteStrategy**: weighted nearest-neighbor algorithm. "
            "Minimizes distance + access_cost at each step. "
            "May travel a longer path to avoid expensive stops. "
            "Best choice when minimizing total delivery cost matters."
        ),
    )
    strategic_route: RouteResponse = Field(
        description=(
            "Route produced by **StrategicHubRouteStrategy**: hub-cluster algorithm. "
            "Detours through the nearest secondary hub to group regional packages. "
            "Respects vehicle max_weight when building the regional cluster. "
            "Best choice when secondary hubs are available and regional consolidation is desired."
        ),
    )
