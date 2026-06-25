from fastapi import FastAPI
from app.core.config import settings
from app.api.v1 import router as v1_router

_DESCRIPTION = """
FastTrack Routing Engine is a logistics API that calculates optimised delivery routes
using interchangeable routing strategies.

## Modules

- **Packages** — manage parcels to be delivered, including coordinates, weight and access cost
- **Vehicles** — manage the fleet, each with a license plate and maximum load capacity
- **Hubs** — manage dispatch points on the map; one main hub at (0, 0) is always present
- **Routes** — calculate and compare delivery routes using one or all available strategies

## Routing Strategies

| Strategy | Algorithm | Optimises for |
|---|---|---|
| `express` | Nearest-neighbor greedy | Minimum total distance |
| `economic` | Weighted nearest-neighbor | Minimum distance + access cost |
| `strategic_hub` | Hub-cluster | Regional consolidation via secondary hubs |

## Workflow

1. Register one or more **Vehicles**
2. Register one or more **Packages**
3. (Optional) Register secondary **Hubs** for regional routing
4. Call `POST /routes/calculate/all` to compare all strategies at once
"""

_TAGS = [
    {
        "name": "packages",
        "description": (
            "Manage delivery packages. "
            "Each package has a destination point on the map, a weight and an access cost "
            "that affects economic routing decisions."
        ),
    },
    {
        "name": "vehicles",
        "description": (
            "Manage the delivery fleet. "
            "Each vehicle has a unique license plate and a maximum weight capacity "
            "that is enforced by all routing strategies."
        ),
    },
    {
        "name": "hubs",
        "description": (
            "Manage dispatch hubs on the routing map. "
            "The **main hub** at (0, 0) is created automatically and serves as the route origin. "
            "Secondary hubs enable the `strategic_hub` strategy to consolidate regional deliveries."
        ),
    },
    {
        "name": "routes",
        "description": (
            "Calculate optimised delivery routes. "
            "Use `POST /routes/calculate` for a single strategy "
            "or `POST /routes/calculate/all` to run all strategies in parallel "
            "and receive an automatic comparison and recommendation."
        ),
    },
]

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description=_DESCRIPTION,
    contact={
        "name": "FastTrack Engineering",
        "email": "engineering@fasttrack.example.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=_TAGS,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"], summary="Health check", include_in_schema=True)
def health():
    """Returns `200 OK` when the service is running. Used by Docker and load balancers."""
    return {"status": "ok"}
