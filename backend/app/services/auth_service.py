import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from app.config import get_settings
from app.database import db_session


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000)
    return digest.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    candidate, _ = hash_password(password, salt)
    return hmac.compare_digest(candidate, password_hash)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_user(email: str, password: str, display_name: str) -> dict:
    password_hash, salt = hash_password(password)
    with db_session() as conn:
        try:
            cur = conn.execute(
                """
                INSERT INTO users (email, display_name, password_hash, password_salt)
                VALUES (?, ?, ?, ?)
                """,
                (email.lower(), display_name, password_hash, salt),
            )
        except Exception as exc:
            if "UNIQUE" in str(exc).upper():
                raise ValueError("이미 가입된 이메일입니다.") from exc
            raise
        return get_user_by_id(cur.lastrowid, conn)


def authenticate_user(email: str, password: str) -> dict | None:
    with db_session() as conn:
        row = conn.execute("SELECT * FROM users WHERE email = ?", (email.lower(),)).fetchone()
        if row is None:
            return None
        if not verify_password(password, row["password_hash"], row["password_salt"]):
            return None
        return dict(row)


def create_session(user_id: int) -> tuple[str, str]:
    settings = get_settings()
    token = secrets.token_urlsafe(32)
    token_hash = hash_token(token)
    expires_at = (_utc_now() + timedelta(days=settings.session_expire_days)).isoformat()
    with db_session() as conn:
        conn.execute(
            "INSERT INTO sessions (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
            (user_id, token_hash, expires_at),
        )
    return token, expires_at


def revoke_session(token: str) -> None:
    with db_session() as conn:
        conn.execute(
            "UPDATE sessions SET revoked_at = CURRENT_TIMESTAMP WHERE token_hash = ? AND revoked_at IS NULL",
            (hash_token(token),),
        )


def get_current_user_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    with db_session() as conn:
        row = conn.execute(
            """
            SELECT users.*
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
              AND sessions.revoked_at IS NULL
              AND sessions.expires_at > ?
            """,
            (hash_token(token), _utc_now().isoformat()),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int, conn=None) -> dict:
    if conn is None:
        with db_session() as managed_conn:
            return get_user_by_id(user_id, managed_conn)
    row = conn.execute(
        "SELECT id, email, display_name, created_at, updated_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        raise ValueError("사용자를 찾을 수 없습니다.")
    return dict(row)
