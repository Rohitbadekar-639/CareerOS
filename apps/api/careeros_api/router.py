from fastapi import APIRouter

from careeros_api.application_routes import applications_router
from careeros_api.identity_routes import identity_router
from careeros_api.jobs_routes import jobs_router
from careeros_api.notification_routes import notifications_router
from careeros_api.profile_routes import profile_router

# Feature routers mount here. Health stays on the app root.
api_router = APIRouter()
api_router.include_router(identity_router)
api_router.include_router(jobs_router)
api_router.include_router(applications_router)
api_router.include_router(profile_router)
api_router.include_router(notifications_router)
