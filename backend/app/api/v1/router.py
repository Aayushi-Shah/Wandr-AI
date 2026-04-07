from fastapi import APIRouter

from app.api.v1 import auth, trip

v1_router = APIRouter()
v1_router.include_router(trip.router, prefix="/trips", tags=["trips"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
