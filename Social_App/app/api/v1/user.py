from fastapi import APIRouter, Depends, HTTPException, status
from core.auth_backend import current_active_user
from models.models import User
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from schemas.user import UserProfileRead, UserProfileUpdate
from services.user import get_profile_payload, update_profile_payload

user_router = APIRouter()


@user_router.get("/me")
async def get_me(user: User = Depends(current_active_user)):
    return user

@user_router.get("/profile", response_model=UserProfileRead)
async def get_profile(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await get_profile_payload(user, session)
    except HTTPException:
        raise HTTPException(status_code= status.HTTP_404_NOT_FOUND)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load profile: {exc}",
        ) from exc


@user_router.patch("/profile", response_model=UserProfileRead)
async def update_profile(
    data: UserProfileUpdate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await update_profile_payload(user, data, session)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {exc}",
        ) from exc