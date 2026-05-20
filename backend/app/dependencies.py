from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.services.auth_service import get_current_user_from_token


def get_current_user(request: Request) -> dict:
    settings = get_settings()
    token = _get_bearer_token(request) or request.cookies.get(settings.session_cookie_name)
    user = get_current_user_from_token(token)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인이 필요합니다.")
    return user


def verify_worker_token(request: Request) -> None:
    expected = get_settings().ai_worker_token
    if not expected:
        return
    actual = request.headers.get("X-AI-Worker-Token")
    if actual != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid worker token")


def _get_bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("Authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()
