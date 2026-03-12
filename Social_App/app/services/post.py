import os
import uuid
import tempfile
import shutil

from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.models import Post, User
from services.images import imagekit


async def upload_post(
    file: UploadFile,
    caption: str,
    user: User,
    session: AsyncSession,
) -> Post:
    """Save uploaded file to ImageKit and persist post record."""
    temp_file_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False, 
            suffix=os.path.splitext(file.filename or "")[1]
        ) as temp_file:
            temp_file_path = temp_file.name
            shutil.copyfileobj(file.file, temp_file)

        safe_file_name = file.filename or f"upload-{uuid.uuid4().hex}"

        with open(temp_file_path, "rb") as f:
            upload_result = await run_in_threadpool(
                imagekit.files.upload,
                file=f,
                file_name=safe_file_name,
                use_unique_file_name=True,
                tags=["backend-upload"],
            )

        if not upload_result.url:
            raise ValueError("Upload succeeded but URL missing")

        post = Post(
            user_id=user.id,
            caption=caption,
            url=upload_result.url,
            file_type="video" if (file.content_type or "").startswith("video/") else "image",
            file_name=upload_result.name,
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        file.file.close()


async def get_feed(session: AsyncSession, current_user: User) -> list[dict]:
    """Return all posts ordered by most recent first with author details."""
    result = await session.execute(
        select(Post, User)
        .join(User, Post.user_id == User.id)
        .order_by(Post.created_at.desc())
    )
    post_rows = result.all()

    return [
        {
            "id": str(post.id),
            "caption": post.caption,
            "url": post.url,
            "file_type": post.file_type,
            "file_name": post.file_name,
            "created_at": post.created_at.isoformat(),
            "username": author.username,
            "email": author.email,
            "is_owner": str(post.user_id) == str(current_user.id),
        }
        for post, author in post_rows
    ]


async def delete_post(post_id: str, session: AsyncSession) -> dict:
    """Delete a post by its UUID string. Raises ValueError if not found."""
    post_uuid = uuid.UUID(post_id)

    result = await session.execute(select(Post).where(Post.id == post_uuid))
    post = result.scalars().first()

    if not post:
        raise ValueError("Post Not Found")

    await session.delete(post)
    await session.commit()

    return {"success": True, "message": "Post deleted successfully"}
