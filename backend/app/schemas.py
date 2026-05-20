from typing import Any

from pydantic import BaseModel, EmailStr, Field, HttpUrl


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    display_name: str = Field(min_length=1, max_length=80)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    display_name: str


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class InterestCreate(BaseModel):
    keyword: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=1000)
    lookback_days: int = Field(default=7, ge=1, le=365)


class InterestResponse(BaseModel):
    id: int
    keyword: str
    description: str
    lookback_days: int
    created_at: str


class ArticleInput(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    url: HttpUrl
    source: str | None = Field(default=None, max_length=200)
    description: str | None = None
    published_at: str | None = None
    summary: str | None = None


class RefreshRequest(BaseModel):
    interest_id: int | None = None
    articles: list[ArticleInput] = Field(default_factory=list)


class RefreshJobResponse(BaseModel):
    id: int
    interest_id: int
    search_terms: list[str]
    candidate_count: int


class RefreshResponse(BaseModel):
    status: str
    pending_ai_jobs: int
    jobs: list[RefreshJobResponse]


class ScrapCreate(BaseModel):
    candidate_article_id: int = Field(gt=0)


class DashboardResponse(BaseModel):
    interests: list[dict[str, Any]]
    articles: list[dict[str, Any]]
    pending_ai_jobs: int
    ai_workers: list[dict[str, Any]]
    scrapped_articles: list[dict[str, Any]]
