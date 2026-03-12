from pydantic import BaseModel
from uuid import UUID

class Post(BaseModel):
    id : UUID
    title: str
    content: str

class PostCreate(BaseModel):
    title: str
    content: str
