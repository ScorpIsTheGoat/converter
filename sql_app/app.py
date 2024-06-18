from fastapi import FastAPI, Depends
from sql_app.database import create_db_and_tables, User
from sql_app.schemas import UserCreate, UserRead, UserUpdate
from sql_app.users import auth_backend, active_user, fastapi_users
import os

app = FastAPI()
app.include_router(fastapi_users.get_auth_router(auth_backend), tags=["auth"])
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate), tags=["auth"]
)
app.include_router(fastapi_users.get_reset_password_router(), tags=["auth"])
app.include_router(fastapi_users.get_verify_router(UserRead), tags=["auth"])
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    tags=["users"],
    prefix=("/users"),
)


@app.get("/authenticated-route")
async def authenticated_route(user: User = Depends(active_user)):
    return {"message": f"Hallo von{user.username} mit {user.email}"}


@app.on_event("startup")
async def on_startup():
    await create_db_and_tables()


@app.on_event("shutdown")
async def on_shutdown():
    os.remove("test.db")
