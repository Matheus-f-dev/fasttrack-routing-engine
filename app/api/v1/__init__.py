from fastapi import APIRouter
from app.api.v1 import routes

router = APIRouter()
router.include_router(routes.router)
