from fastapi import APIRouter
from app.api.v1 import packages

router = APIRouter()
router.include_router(packages.router)
