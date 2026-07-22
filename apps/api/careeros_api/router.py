from fastapi import APIRouter

from careeros_api.identity_routes import identity_router

# Feature routers mount here. Health stays on the app root.
api_router = APIRouter()
api_router.include_router(identity_router)
