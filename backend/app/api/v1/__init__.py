"""API v1 router aggregation."""

from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.kiosk import router as kiosk_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.field import router as field_router
from app.api.v1.travel import router as travel_router
from app.api.v1.admin import router as admin_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(kiosk_router)
api_v1_router.include_router(attendance_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(field_router)
api_v1_router.include_router(travel_router)
api_v1_router.include_router(admin_router)
