import sqlite3

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .database import get_connection, init_db
from .schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from .security import create_session_token, hash_password, verify_password


app = FastAPI(title="ContextNews AI Backend")
bearer_scheme = HTTPBearer(auto_error=False)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


def serialize_user(row: sqlite3.Row) -> UserResponse:
    return UserResponse(id=row["id"], email=row["email"], display_name=row["display_name"])


def get_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    if credentials and credentials.scheme.lower() == "bearer":
        return credentials.credentials

    token = request.cookies.get("session_token")
    if token:
        return token

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def get_current_user(token: str = Depends(get_token)) -> sqlite3.Row:
    with get_connection() as db:
        user = db.execute(
            """
            SELECT users.id, users.email, users.display_name
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ? AND sessions.revoked_at IS NULL
            """,
            (token,),
        ).fetchone()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    return user


@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response) -> AuthResponse:
    token = create_session_token()
    try:
        with get_connection() as db:
            cursor = db.execute(
                "INSERT INTO users (email, display_name, password_hash) VALUES (?, ?, ?)",
                (payload.email.lower(), payload.display_name, hash_password(payload.password)),
            )
            user_id = cursor.lastrowid
            db.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user_id, token))
            user = db.execute(
                "SELECT id, email, display_name FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc

    response.set_cookie("session_token", token, httponly=True, samesite="lax")
    return AuthResponse(token=token, user=serialize_user(user))


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response) -> AuthResponse:
    with get_connection() as db:
        user = db.execute(
            "SELECT id, email, display_name, password_hash FROM users WHERE email = ?",
            (payload.email.lower(),),
        ).fetchone()

        if user is None or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        token = create_session_token()
        db.execute("INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user["id"], token))

    response.set_cookie("session_token", token, httponly=True, samesite="lax")
    return AuthResponse(token=token, user=serialize_user(user))


@app.get("/api/auth/me", response_model=UserResponse)
def me(current_user: sqlite3.Row = Depends(get_current_user)) -> UserResponse:
    return serialize_user(current_user)


@app.post("/api/auth/logout")
def logout(response: Response, token: str = Depends(get_token)) -> dict[str, str]:
    with get_connection() as db:
        db.execute("UPDATE sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token = ?", (token,))

    response.delete_cookie("session_token")
    return {"status": "ok"}
