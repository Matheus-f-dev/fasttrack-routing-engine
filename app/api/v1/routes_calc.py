import asyncio
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.algorithms.base import RouteStrategy, VehicleCapacityExceededError
from app.algorithms.models import RouteInput, RouteResult
from app.algorithms.registry import RouteStrategyRegistry, StrategyNotFoundError
from app.models.package import Package
from app.models.vehicle import Vehicle
from app.repositories.hub_repository import HubRepository
from app.repositories.package_repository import PackageRepository
from app.repositories.vehicle_repository import VehicleRepository
from app.schemas.route import (
    AllRoutesResponse,
    DeliveryStop,
    RouteRequest,
    RouteResponse,
    VisitedHubResponse,
)
from app.services.route_comparison import RouteComparisonService

router = APIRouter(prefix="/routes", tags=["routes"])

_hub_repo = HubRepository()
_package_repo = PackageRepository()
_vehicle_repo = VehicleRepository()
_registry = RouteStrategyRegistry()
_executor = ThreadPoolExecutor()
_comparison_service = RouteComparisonService()

_400 = {"description": "Total package weight exceeds vehicle `max_weight`"}
_404 = {"description": "Vehicle or package not found"}
_422 = {"description": "Unknown strategy name"}

_STRATEGY_TABLE = (
    "| Strategy | Algorithm | Optimises for | Considers `access_cost` |\n"
    "|---|---|---|---|\n"
    "| `express` | Nearest-neighbor greedy | Minimum total distance | No |\n"
    "| `economic` | Weighted nearest-neighbor | Minimum distance + cost | Yes |\n"
    "| `strategic_hub` | Hub-cluster | Regional consolidation | Yes |\n"
)

_CAPACITY_NOTE = (
    "> **Capacity rule:** the sum of `weight` across all requested packages "
    "must not exceed the vehicle's `max_weight`. Returns `400` otherwise."
)

_REQUEST_EXAMPLES = {
    "express_single": {
        "summary": "Two packages — express strategy",
        "value": {
            "vehicle_id": "b7e23ec2-9428-4f3e-9e49-a9e9d13bce40",
            "package_ids": [
                "a3bb189e-8bf9-3888-9912-ace4e6543002",
                "d290f1ee-6c54-4b01-90e6-d701748f0851",
            ],
        },
    },
    "economic_single": {
        "summary": "Three packages — economic strategy",
        "value": {
            "vehicle_id": "b7e23ec2-9428-4f3e-9e49-a9e9d13bce40",
            "package_ids": [
                "a3bb189e-8bf9-3888-9912-ace4e6543002",
                "d290f1ee-6c54-4b01-90e6-d701748f0851",
                "c1a2b3c4-d5e6-7890-abcd-ef1234567890",
            ],
        },
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_vehicle(vehicle_id: UUID) -> Vehicle:
    vehicle = _vehicle_repo.get_by_id(vehicle_id)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


def _resolve_packages(package_ids: list[UUID]) -> list[Package]:
    packages = []
    for pid in package_ids:
        pkg = _package_repo.get_by_id(pid)
        if not pkg:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Package {pid} not found")
        packages.append(pkg)
    return packages


def _build_route_input(vehicle: Vehicle, packages: list[Package]) -> RouteInput:
    return RouteInput(
        packages=packages,
        vehicle=vehicle,
        origin=_hub_repo.get_main(),
        available_hubs=_hub_repo.get_all(),
    )


def _build_response(result: RouteResult) -> RouteResponse:
    return RouteResponse(
        route_type=result.strategy_name,
        total_distance=result.total_distance,
        total_cost=result.total_cost,
        delivery_order=[
            DeliveryStop(
                sequence=stop.sequence,
                package_id=stop.packages[0].id,
                recipient_name=stop.packages[0].recipient_name,
                destination_x=stop.packages[0].destination_x,
                destination_y=stop.packages[0].destination_y,
            )
            for stop in result.stops
        ],
        extra_package_collected=result.extra_package_collected,
        visited_hub=VisitedHubResponse(
            id=result.visited_hub.id,
            name=result.visited_hub.name,
            x=result.visited_hub.x,
            y=result.visited_hub.y,
        ) if result.visited_hub else None,
    )


def _run_strategy(strategy: RouteStrategy, route_input: RouteInput) -> RouteResult:
    return strategy.calculate_route(route_input)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/calculate",
    response_model=RouteResponse,
    summary="Calculate a route with a single strategy",
    description=(
        "Calculates a delivery route for the given vehicle and packages "
        "using the strategy selected via the `strategy` query parameter.\n\n"
        f"{_STRATEGY_TABLE}\n"
        f"{_CAPACITY_NOTE}\n\n"
        "The route always departs from the **main hub at (0, 0)**.\n\n"
        "Use `POST /routes/calculate/all` to run all strategies at once and compare results."
    ),
    responses={
        200: {"description": "Route calculated successfully"},
        400: _400,
        404: _404,
        422: _422,
    },
    openapi_extra={"requestBody": {"content": {"application/json": {"examples": _REQUEST_EXAMPLES}}}},
)
def calculate_route(
    body: RouteRequest,
    strategy: str = Query(
        default="express",
        description=(
            "Routing strategy to apply. One of: `express`, `economic`, `strategic_hub`.\n\n"
            "Defaults to `express` if omitted."
        ),
        examples=["express"],
    ),
) -> RouteResponse:
    vehicle = _resolve_vehicle(body.vehicle_id)
    packages = _resolve_packages(body.package_ids)

    try:
        route_strategy = _registry.get(strategy)
    except StrategyNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    try:
        result = route_strategy.calculate_route(_build_route_input(vehicle, packages))
    except VehicleCapacityExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return _build_response(result)


@router.post(
    "/calculate/all",
    response_model=AllRoutesResponse,
    summary="Calculate and compare all strategies simultaneously",
    description=(
        "Runs **all three routing strategies in parallel** for the same vehicle and package list.\n\n"
        "Returns a unified response with:\n\n"
        "- `express_route` — result of the Express strategy\n"
        "- `economic_route` — result of the Economic strategy\n"
        "- `strategic_route` — result of the Strategic Hub strategy\n"
        "- `comparison` — automatic cross-strategy analysis including:\n"
        "  - `shortest_route` — strategy with lowest `total_distance`\n"
        "  - `cheapest_route` — strategy with lowest `total_cost`\n"
        "  - `highest_utilization_route` — strategy with most packages per distance unit\n"
        "  - `distance_saved` — distance units gained over the worst route\n"
        "  - `cost_saved` — cost units gained over the most expensive route\n"
        "  - `recommended` — best balanced strategy with human-readable justification\n\n"
        f"{_STRATEGY_TABLE}\n"
        f"{_CAPACITY_NOTE}"
    ),
    responses={
        200: {"description": "All routes calculated and compared successfully"},
        400: _400,
        404: _404,
    },
    openapi_extra={"requestBody": {"content": {"application/json": {"examples": _REQUEST_EXAMPLES}}}},
)
async def calculate_all_routes(body: RouteRequest) -> AllRoutesResponse:
    vehicle = _resolve_vehicle(body.vehicle_id)
    packages = _resolve_packages(body.package_ids)
    route_input = _build_route_input(vehicle, packages)

    loop = asyncio.get_event_loop()
    strategies = {
        "express":       _registry.get("express"),
        "economic":      _registry.get("economic"),
        "strategic_hub": _registry.get("strategic_hub"),
    }

    try:
        express_result, economic_result, strategic_result = await asyncio.gather(
            loop.run_in_executor(_executor, _run_strategy, strategies["express"],       route_input),
            loop.run_in_executor(_executor, _run_strategy, strategies["economic"],      route_input),
            loop.run_in_executor(_executor, _run_strategy, strategies["strategic_hub"], route_input),
        )
    except VehicleCapacityExceededError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    express_response  = _build_response(express_result)
    economic_response = _build_response(economic_result)
    strategic_response = _build_response(strategic_result)

    return AllRoutesResponse(
        express_route=express_response,
        economic_route=economic_response,
        strategic_route=strategic_response,
        comparison=_comparison_service.compare(
            express=express_response,
            economic=economic_response,
            strategic=strategic_response,
        ),
    )
