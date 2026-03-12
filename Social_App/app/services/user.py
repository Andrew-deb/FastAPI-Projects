from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.models import Post, User
from schemas.user import UserProfileRead, UserProfileUpdate
from datetime import datetime


async def get_profile_payload(user: User, session: AsyncSession) -> UserProfileRead:
    """Build a profile payload for the currently authenticated user."""
    post_count_result = await session.execute(
        select(func.count(Post.id)).where(Post.user_id == user.id)
    )
    post_count = post_count_result.scalar_one()

    return UserProfileRead(
        id=user.id,
        email=user.email,
        username=getattr(user, "username", None) or user.email.split("@")[0],
        full_name=getattr(user, "full_name", None),
        bio=getattr(user, "bio", None),
        profile_image_url=getattr(user, "profile_image_url", None),
        cover_image_url=getattr(user, "cover_image_url", None),
        website=getattr(user, "website", None),
        location=getattr(user, "location", None),
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=getattr(user, "created_at", datetime.utcnow()),
        post_count=post_count,
    )


async def update_profile_payload(
    user: User,
    data: UserProfileUpdate,
    session: AsyncSession,
) -> UserProfileRead:
    """Apply partial profile updates to the authenticated user and return updated profile."""
    update_fields = data.model_dump(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(user, field, value)

    session.add(user)
    await session.commit()
    await session.refresh(user)

    return await get_profile_payload(user, session)
