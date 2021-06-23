# Generic permission handling for FastAPI

Permission management should be as declarative as possible, making it simple to add and check permissions. At the same time, there are cases where permissions are not straightforward. For example, an article might be editable by a list of authors. Such permissions may need path and query parameters, as well as the currently logged-in user.

As FastAPI does not ship with built-in permission management, this library provides a simple solution. Permissions are handled as a path operation dependency, and the permission logic is implemented in form of functions returning a boolean.

## Alternatives

If your API has a handful of endpoints only, you might not need a permission management library at all, and you could just add whatever logic you need in the path operations' body. Here is a simple example.

```python
from fastapi import FastAPI, HTTPException

app = FastAPI()

@app.get("/articles/{article_id}")
def view_article(article_id: int) -> str:
    if article_id == 42:
        raise HTTPException(403)
    return f"This is article {article_id}."
```

This will generally be a less-than-ideal option, which can hardly be called declarative. Assuming you have resources for which you can easily define a list of permissions and user/group/role identifiers, you should consider using the [fastapi-permissions](https://github.com/holgi/fastapi-permissions) library.

## Usage

The `fastapi-generic-permissions` provides a single function, `permission`, which returns a callable object, called `verify_permission` in the following.

```python
from fastapi_generic_permissions import permission

verify_permission = permission()
```

When called, `verify_permission` accepts a test function as its first argument. This test function must return `True` if permission is granted, and `False` otherwise. Its arguments may use FastAPI's `Depends` function.

You can add `verify_permission` as a path operation dependency. Note that it is *not* used as an argument of FastAPI's `Depends`; if you tried that, you would get a somewhat cryptic error ("A parameter-less dependency must have a callable dependency").

```python
from fastapi import Depends, FastAPI, Path
from pydantic import BaseModel

from fastapi_generic_permissions import permission


verify_permission = permission()


class Article(BaseModel):
    id: int
    title: str
    
    
def get_article(article_id: int) -> Article:
    return Article(id=article_id, title=f"This is article {article_id}")


def may_view_article(article: Article = Depends(get_article)) -> bool:
    return article.id != 42


app = FastAPI()


@app.get("/articles/{article_id}", dependencies=[verify_permission(may_view_article)])
def view_article(article_id: int = Path(..., title="Article identifier")) -> Article:
    return get_article(article_id)
```

If permission is denied, an `HTTPException` with status code 403 and the message `"Forbidden"` is raised. (See below how to change this.)

### A performance caveat

In the previous example both the permission check and the path operation's body call the `get_article` function. So if `get_article` makes a database query, you could end up making the same query twice, which obviously is ineffective.

A solution would be to change the signature of the path operation to use the article rather than the article id.

```python
@app.get("/articles/{article_id}", dependencies=[verify_permission(may_view_article)])
def view_article(article: Article = Depends(get_article)) -> Article:
    return get_article(article_id)
```

As FastAPI is caching when handling dependencies, `get_article` is then called only once. However, the article id's OpenAPI metadata (the `title` in the example above) is then lost.

It might thus be tempting to instead cache the results of the `get_article` using `lru_cache`.

```python
from functools import lru_cache

@lru_cache()  # DON'T DO THIS!
def get_article(article_id: int) -> Article:
    return Article(id=article_id, title=f"This is article {article_id}")
```

**This generally is a bad idea.** The database content of the article might change between calls, but the old, cached article would still be returned.

So if both your permission checks and your path operations make the same database calls, this could be a sign that you should rather use the `fast-permissions` library for your permission management.

### Changing the error message and status code

Sometimes it is not appropriate to return the status code 403 if the user is not allowed to perform a request. For example, if a malicious user `demon` tries to view the personal details for a user `saint`, you might not want to tell `demon` that `saint` actually exists.

Instead you can return a `404 Not Found` error by passing the status code as an argument to the Permission function.

```python
@app.post('/users/{user_id}/password', dependencies=[verify_permission(may_view_user, status_code=404)])
def get_user(user_id: int, password: str) -> User:
    return find_user(user_id)
```

If you aren't happy with the default error message (`"Forbidden"` for status code 403, `"Not Found"` for status code 404, and `"Error"` for any other status code), you can pass another message to the `Permission` function.

```python
@app.delete('/spell', dependencies=[verify_permission(may_create_spell, message="Only wizards are allowed to create a spell.")])
def create_spell() -> None:
    print("Abracadabra!")
```

You can also change the default message for a status code.

```python
verify_permissions.set_default_message(403, "You are not allowed to do this")
verify_permissions.set_default_message(418, "Only tea can be brewed here")
```

## Example

A complete working example can be found in the file `example.py`, which is located in the project;'s root directory. Note you need `uvicorn`, which is not installed automatically when installing `fastapi-generic-permissions`. You can install it as follows.

```shell
pip install uvicorn
```

You can then run the script in `example.py`.

```shell
python example.py
```

This launches a server which provides a GET endpoint `/users/{id}` and a POST endpoint `/cook`. You can use `curl` to test this example API. Here are two examples of successful requests.

```shell
curl -i "http://localhost:8000/users/1?user_id=1"
curl -i -X POST "http://localhost:8000/cook?user_id=2"
```

The following two examples show requests that fails because of pernission checking.

```shell
curl -i "http://localhost:8000/users/1?user_id=2"
curl -i -X POST "http://localhost:8000/cook?user_id=1"
```

## Acknowledgments

While this library has a slightly different approach, it has been inspired by `fastapi-permissions`, and its source code has proven extremely helpful.
