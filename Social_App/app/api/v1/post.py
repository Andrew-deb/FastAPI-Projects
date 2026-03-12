from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import get_async_session
from core.auth_backend import current_active_user
from models.models import User
from services.post import upload_post, get_feed, delete_post as delete_post_service

post_router = APIRouter()


@post_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await upload_post(file, caption, user, session)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@post_router.get("/feed")
async def feed(
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        posts = await get_feed(session, user)
        return {"posts": posts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@post_router.delete("/post/{post_id}")
async def remove_post(
    post_id: str,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        return await delete_post_service(post_id, session)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
