from fastapi import Depends
from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    UUIDIDMixin,
)  # user können so gemanaget werden
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from sql_app.database import get_user_db

SECRET = "mysupersecret"


class UserManager(UUIDIDMixin, BaseUserManager):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


cookie_transport = CookieTransport(cookie_httponly=True, cookie_secure=True)


def get_jwt_strategy():
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt", transport=cookie_transport, get_strategy=get_jwt_strategy
)

fastapi_users = FastAPIUsers(get_user_manager, [auth_backend])

active_user = fastapi_users.current_user(active=True)
