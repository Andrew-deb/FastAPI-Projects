from fastapi import FastAPI
from core.db import create_db_and_tables
from contextlib import asynccontextmanager
from api.v1.post import post_router
from api.v1.auth_routes import auth_router
from api.v1.user import user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(post_router,prefix="/posts", tags=["Posts"])
app.include_router(auth_router, prefix="/api")
app.include_router(user_router, prefix="/users", tags=["Users"])