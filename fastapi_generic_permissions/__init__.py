from typing import Any, Awaitable, Callable, Optional, Union

from fastapi import Depends, HTTPException, status


class _Permission:
    def __init__(self) -> None:
        self._default_messages = {
            status.HTTP_403_FORBIDDEN: "Forbidden",
            status.HTTP_404_NOT_FOUND: "Not Found",
        }

    def set_default_message(self, status_code: int, message: str) -> None:
        self._default_messages[status_code] = message

    def __call__(
        self,
        is_permitted: Callable[..., Union[bool, Awaitable[bool]]],
        message: Optional[str] = None,
        status_code: int = status.HTTP_403_FORBIDDEN,
    ) -> Any:
        def check_permission(permitted: bool = Depends(is_permitted)) -> None:
            if not permitted:
                error = (
                    message
                    if message
                    else self._default_messages.get(status_code, "Error")
                )
                raise HTTPException(status_code, error)

        return Depends(check_permission)


def permission() -> _Permission:
    return _Permission()
