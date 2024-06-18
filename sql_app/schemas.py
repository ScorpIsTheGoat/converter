from fastapi_users.schemas import BaseUser, BaseUserCreate, BaseUserUpdate


class UserRead(BaseUser):
    username: str
    pass


class UserCreate(BaseUserCreate):
    username: str
    pass


class UserUpdate(BaseUserUpdate):
    username: str
    pass
