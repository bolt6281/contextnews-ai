from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=2, max_length=20)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str


class AuthResponse(UserResponse):
    session_token: str


class InterestCreateRequest(BaseModel):
    keyword: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=10, max_length=300)
    lookback_days: int = Field(default=3, ge=1, le=30)


class InterestResponse(BaseModel):
    id: int
    keyword: str
    description: str
    lookback_days: int
    created_at: str
    ai_job_id: int | None = None
    ai_job_status: str | None = None


class RefreshRequest(BaseModel):
    limit_per_interest: int = Field(default=10, ge=1, le=20)


class ScrapCreateRequest(BaseModel):
    candidate_article_id: int


class ClaimRequest(BaseModel):
    worker_id: str
    limit: int = Field(default=1, ge=1, le=5)


class CompleteJobRequest(BaseModel):
    worker_id: str
    result: dict


class FailJobRequest(BaseModel):
    worker_id: str
    error_message: str


class HeartbeatRequest(BaseModel):
    worker_id: str
    status: str = "online"
