import asyncio
from typing import Dict

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel


from fastapi_generic_permissions import permission


# A simple example of using fastapi-generic-permissions to check permissions.
#
# Install uvicorn (pip install uvicorn) and launch the server by executing the following
# command in a terminal:
#
# python example.py
#
# Examples of HTTP requests that succeed:
#
# GET http://localhost:8000/users/1?user_id=1
# POST http://localhost:8000/cook?user_id=2
#
# Examples of HTTP requests that fail:
#
# GET http://localhost:8000/users/1?user_id=2
# POST http://localhost:8000/cook?user_id=1


class User(BaseModel):
    user_id: int
    role: str


verify_permission = permission()

# You can define custom error messages for specific status codes
verify_permission.set_default_message(status_code=status.HTTP_403_FORBIDDEN, message="You are not allowed to do this")


USERS = {
    1: User(user_id=1, role="Waiter"),
    2: User(user_id=2, role="Cook")
}


async def get_current_user(user_id: int) -> User:
    # Pretend to wait for some database query to finish
    await asyncio.sleep(0.01)

    if user_id not in USERS:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED)

    return USERS[user_id]


# Only cooks may cook.
async def may_cook(user: User=Depends(get_current_user)) -> bool:
    # Pretend to wait for some database query to finish
    await asyncio.sleep(0.01)

    return user.role == "Cook"


# A user can only view their own details.
async def may_view_user_details(viewed_user_id: int, user: User=Depends(get_current_user)) -> bool:
    # Pretend to wait for some database query to finish
    await asyncio.sleep(0.01)

    print(viewed_user_id, type(viewed_user_id), user.user_id, type(user.user_id))
    return viewed_user_id == user.user_id


app = FastAPI()


# View user details. Users may only view their own details. For security reasons,
# don't tell the user whether the requested user id exists.
@app.get("/users/{viewed_user_id}", dependencies=[verify_permission(may_view_user_details, status_code=404, message="No such user")])
async def view_user(viewed_user_id: int) -> User:
    if viewed_user_id not in USERS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such user")

    return USERS[viewed_user_id]


# Prepare a meal. Only cooks are trusted with this.
@app.post("/cook", dependencies=[verify_permission(may_cook)])
async def cook() -> Dict[str, bool]:
    return {"success": True}


if __name__ == '__main__':
    uvicorn.run(app)
