from pydantic import BaseModel, EmailStr, Field


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
