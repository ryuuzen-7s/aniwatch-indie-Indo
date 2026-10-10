"""
security/models.py — Pydantic schemas untuk auth.
"""
from typing import Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=200)


class LoginResponse(BaseModel):
    token: str
    user: dict
    expires_in: int = 86400


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=200)
    email: str = ""


class GetKeyRequest(BaseModel):
    name: str = Field("default", max_length=100)
    username: Optional[str] = Field(None, description="Username (kalau punya akun)")
    password: Optional[str] = Field(None, description="Password (kalau punya akun)")
    rate_limit: int = Field(100, ge=10, le=10000)
    expires_days: Optional[int] = Field(None, ge=1, le=3650)
    role: str = Field("user", pattern="^(user|admin)$")
    max_requests: Optional[int] = Field(None, ge=1)



class ApiKeyResponse(BaseModel):
    key: str = Field(..., description="⚠️ Simpan! Hanya muncul sekali")
    info: dict