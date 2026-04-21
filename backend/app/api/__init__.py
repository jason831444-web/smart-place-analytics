from fastapi import APIRouter

from app.api import admin, analyses, auth, facilities, uploads

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(facilities.router)
api_router.include_router(uploads.router)
api_router.include_router(analyses.router)
api_router.include_router(admin.router)

