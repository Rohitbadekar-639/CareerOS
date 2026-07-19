from fastapi import APIRouter

# Root router placeholder. Feature routers are mounted here from M1 onward;
# health/readiness endpoints arrive in T12. No endpoints in the M0 skeleton.
api_router = APIRouter()
