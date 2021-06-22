from typing import Dict

from fastapi import FastAPI, status
from fastapi.testclient import TestClient

from fastapi_generic_permissions import permission


def test_raises_an_error_if_permission_is_denied() -> None:
    app = FastAPI()

    verify_permission = permission()

    @app.get("/", dependencies=[verify_permission(lambda: False)])
    def home() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "Forbidden"


def test_raises_no_error_if_permission_is_granted() -> None:
    app = FastAPI()

    verify_permission = permission()

    @app.get("/", dependencies=[verify_permission(lambda: True)])
    def home() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["success"] is True


def test_query_parameters_can_be_used_in_permission_check() -> None:
    # The permission check is handled as part of FastAPI's dependency chain. Hence the
    # function for checking permission has access to all the query, path etc.
    # parameters.
    app = FastAPI()

    verify_permission = permission()

    def is_permitted(permitted: bool) -> bool:
        return permitted

    @app.get("/", dependencies=[verify_permission(is_permitted)])
    def home() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response_permitted = client.get("/", params={"permitted": True})
    assert response_permitted.status_code == status.HTTP_200_OK

    response_forbidden = client.get("/", params={"permitted": False})
    assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN


def test_async_functions_are_allowed() -> None:
    # The permission check is handled as part of FastAPI's dependency chain. Hence an
    # async function can be used for checking permissions.
    app = FastAPI()

    verify_permission = permission()

    async def is_permitted(permitted: bool) -> bool:
        return permitted

    @app.get("/", dependencies=[verify_permission(is_permitted)])
    def home() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response_permitted = client.get("/", params={"permitted": True})
    assert response_permitted.status_code == status.HTTP_200_OK

    response_forbidden = client.get("/", params={"permitted": False})
    assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN


def test_the_error_message_can_be_changed() -> None:
    app = FastAPI()

    verify_permission = permission()

    @app.get(
        "/",
        dependencies=[verify_permission(lambda: False, message="This is not allowed")],
    )
    def home() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()["detail"] == "This is not allowed"


def test_the_status_code_can_be_changed() -> None:
    app = FastAPI()

    verify_permission = permission()

    @app.get(
        "/",
        dependencies=[
            verify_permission(lambda: False, status_code=status.HTTP_404_NOT_FOUND)
        ],
    )
    def home() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response = client.get("/")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Not Found"


def test_the_default_error_message_can_be_changed() -> None:
    app = FastAPI()

    verify_permission = permission()
    verify_permission.set_default_message(
        status.HTTP_403_FORBIDDEN, "This action is forbidden"
    )
    verify_permission.set_default_message(
        status.HTTP_404_NOT_FOUND, "The resource does not exist"
    )
    verify_permission.set_default_message(
        status.HTTP_418_IM_A_TEAPOT, "Only tea may be brewed"
    )

    @app.get(
        "/",
        dependencies=[
            verify_permission(lambda: False, status_code=status.HTTP_403_FORBIDDEN)
        ],
    )
    def forbidden() -> Dict[str, bool]:
        return {"success": True}

    @app.get(
        "/not-found",
        dependencies=[
            verify_permission(lambda: False, status_code=status.HTTP_404_NOT_FOUND)
        ],
    )
    def not_found() -> Dict[str, bool]:
        return {"success": True}

    @app.get(
        "/teapot",
        dependencies=[
            verify_permission(lambda: False, status_code=status.HTTP_418_IM_A_TEAPOT)
        ],
    )
    def teapot() -> Dict[str, bool]:
        return {"success": True}

    client = TestClient(app)

    response_forbidden = client.get("/")
    assert response_forbidden.json()["detail"] == "This action is forbidden"

    response_not_found = client.get("/not-found")
    assert response_not_found.json()["detail"] == "The resource does not exist"

    response_teapot = client.get("/teapot")
    assert response_teapot.json()["detail"] == "Only tea may be brewed"
