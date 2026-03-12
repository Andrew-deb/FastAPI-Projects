from fastapi import APIRouter
from core.auth_backend import fastapi_users, auth_backend
from schemas.user import UserRead, UserCreate, UserUpdate

auth_router = APIRouter()

auth_router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"],
)

auth_router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

auth_router.include_router(
    fastapi_users.get_reset_password_router(), 
    prefix="/auth",
    tags=["auth"]
)

auth_router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"]
)

auth_router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)