from datetime import datetime
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field

from .user import UserRole


class AccessRefreshToken(BaseModel):
    """Returned to the user after a successful login or token refresh."""
    access_token: str
    token_type: str
    refresh_token: str


class AccessTokenData(BaseModel):
    """Extracted from a decoded access token and returned by validate_access_token()."""
    # user id taken from token is returned as string
    user_id: Optional[str] = None
    role: Optional[UserRole] = None

    # turns id, if exists, from str to UUID
    def get_uuid(self) -> uuid.UUID | None:
        return uuid.UUID(self.user_id) if self.user_id else None


class ResetTokenInDB(SQLModel, table=True):
    """Table storing temporary tokens for password reset (combines email, role & reset token)."""
    reset_token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(max_length=320, index=True)
    role: UserRole
    token_hash: str = Field(max_length=255, index=True)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))  # timezone=True accepts timezone-aware datetime


class RefreshTokenInDB(SQLModel, table=True):
    """Token used to refresh user's access token."""
    refresh_token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID 
    role: UserRole
    token_hash: str = Field(max_length=255, index=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    revoked_at: Optional[datetime] = Field(default=None, index=True)


class RefreshRequest(BaseModel):
    refresh_token: str

    model_config = ConfigDict(
        extra="ignore"
    )
