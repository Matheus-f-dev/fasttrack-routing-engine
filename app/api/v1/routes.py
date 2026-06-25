from fastapi import APIRouter
from app.api.v1 import packages, vehicles, hubs

router = APIRouter()
router.include_router(packages.router)
router.include_router(vehicles.router)
router.include_router(hubs.router)
