# Authentication Pattern

## Public Endpoints

No authentication required.

* `POST /auth/signup`
* `POST /auth/login`

---

## Protected Endpoints

Require `Authorization: Bearer <token>` header.

* `GET /libraries`
* `POST /libraries`
* `DELETE /libraries/{id}`
* `GET /sessions`
* `POST /sessions`
* `DELETE /sessions/{id}`
* `GET /sessions/{id}/messages`
* `POST /search`
* `GET /analytics`
* `POST /upload/{library_id}` (planned)
* `POST /chat` (planned)

---

## Authorization Header Format

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Obtain token via:
1. `POST /auth/signup` — returns `access_token`
2. `POST /auth/login` — returns `access_token`

---

## Error Responses

| Situation | Status | Response Body |
|-----------|--------|---------------|
| Missing Authorization header | 401 | `{"detail": "Not authenticated"}` |
| Expired JWT | 401 | `{"detail": "Token expired"}` |
| Invalid JWT | 403 | `{"detail": "Invalid credentials"}` |

---

## Route Template

Every new protected endpoint follows this pattern:

```python
from fastapi import APIRouter, Depends
from app.deps import get_current_user
from app.services import some_service

router = APIRouter(prefix="/example", tags=["example"])

@router.post("/action")
def do_something(
    request: SomeRequest,
    current_user = Depends(get_current_user)
):
    return some_service.handle(
        user_id=current_user["user_id"],
        email=current_user["email"],
        request=request
    )
```

Rules:
1. Router validates input schema
2. `current_user` obtained via `Depends(get_current_user)`
3. Service receives `user_id` and `email` separately
4. Router returns response — no business logic

---

## JWT Lifecycle

1. User signs up or logs in
2. Server returns `access_token` (12h expiry)
3. Client stores token (localStorage, secure store)
4. Client sends token in `Authorization` header on every request
5. Server validates and returns 401/403 on failure
6. Client discards token on logout

---

## Adding New Routes

1. Define request/response schemas in `app/schemas.py`
2. Implement business logic in `app/services/`
3. Create thin router in `app/routers/`
4. Use `Depends(get_current_user)` for protected routes
5. Register router in `app/main.py`

Do NOT:
* Put business logic in routers
* Import `core/` modules from routers
* Use session-based auth — JWT only
