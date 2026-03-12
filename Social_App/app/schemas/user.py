from pydantic import BaseModel
from fastapi_users import schemas
from uuid import UUID
from datetime import datetime
from typing import Optional

class UserRead(schemas.BaseUser[UUID]):
    username: Optional[str] =None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime

class UserCreate(schemas.BaseUserCreate):
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None

class UserUpdate(schemas.BaseUserUpdate):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None


class UserProfileRead(BaseModel):
    id: UUID
    email: str
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None
    is_active: bool
    is_verified: bool
    created_at: datetime
    post_count: int


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    website: Optional[str] = None
    location: Optional[str] = None