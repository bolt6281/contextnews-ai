from fastapi import APIRouter, Depends, HTTPException, Response, Request, status

from app.config import get_settings
from app.dependencies import get_current_user
from app.schemas import AuthResponse, LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import authenticate_user, create_session, create_user, revoke_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _public_user(user: dict) -> UserResponse:
    return UserResponse(id=user["id"], email=user["email"], display_name=user["display_name"])


def _public_auth(user: dict, session_token: str) -> AuthResponse:
    return AuthResponse(
        id=user["id"],
        email=user["email"],
        display_name=user["display_name"],
        session_token=session_token,
    )


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


@router.post("/register", response_model=AuthResponse)
def register(payload: RegisterRequest, response: Response):
    try:
        user = create_user(payload.email, payload.password, payload.display_name)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    token, expires_at = create_session(user["id"])
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_expire_days * 24 * 60 * 60,
    )
    return _public_auth(user, token)


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response):
    user = authenticate_user(payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="이메일 또는 비밀번호가 올바르지 않습니다.")
    token, expires_at = create_session(user["id"])
    settings = get_settings()
    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        max_age=settings.session_expire_days * 24 * 60 * 60,
    )
    return _public_auth(user, token)


@router.get("/me", response_model=UserResponse)
def me(user: dict = Depends(get_current_user)):
    return _public_user(user)


@router.post("/logout")
def logout(request: Request, response: Response):
    settings = get_settings()
    token = _bearer_token(request) or request.cookies.get(settings.session_cookie_name)
    if token:
        revoke_session(token)
    response.delete_cookie(settings.session_cookie_name)
    return {"ok": True}
