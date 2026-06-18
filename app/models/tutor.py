from datetime import datetime
from typing import Optional
import uuid

from pydantic import EmailStr, field_validator
from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Field

from .user import UserPublic, UserRole
from ..utils.validators import normalize_email, strong_password_validator


class TutorBase(SQLModel):
    name: str = Field(max_length=40)
    surname: str = Field(max_length=40)
    email: EmailStr = Field(max_length=40)  # Pydantic string type for email validation
    phone: Optional[str] = Field(max_length=10, default=None)
    address: Optional[str] = Field(max_length=50, default=None)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return normalize_email(v)
    

class TutorInDB(TutorBase, table=True):
    tutor_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)  # default_factory creates a UUID Python-side before sending to db
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field(max_length=255, index=True)

    tutor_updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            onupdate=func.now()
        )
    )  # automatically adds time when model is updated
    pwd_changed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    pwd_reset_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))

    is_active: bool = Field(default=True)
    # creation date & time for log/audit
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    # account soft delete field
    deleted_at: Optional[datetime] = Field(default=None, index=True)


class TutorCreate(TutorBase):
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return strong_password_validator(v)


class TutorPublic(TutorBase, UserPublic):
    """ Inherits from both TutorBase and UserPublic models.
    
    Role property has a default of 'TUTOR'.
    """
    tutor_id: uuid.UUID
    role: UserRole = UserRole.TUTOR


class TutorUpdate(SQLModel):
    name: Optional[str] = Field(max_length=40, default=None)
    surname: Optional[str] = Field(max_length=40, default=None)
    email: Optional[EmailStr] = Field(max_length=40, default=None)
    phone: Optional[str] = Field(max_length=10, default=None)
    address: Optional[str] = Field(max_length=50, default=None)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return normalize_email(v)
