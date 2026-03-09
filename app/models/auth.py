from datetime import datetime
from typing import TYPE_CHECKING, Optional
import uuid

from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, DateTime, func
from sqlmodel import SQLModel, Relationship, Field


if TYPE_CHECKING:
    from .student import StudentInDB
    


# -- ACCESS (& REFRESH) TOKEN PUBLIC -- returned to the user
class AccessRefreshToken(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str 
    

# -- TOKEN DATA -- extracted from decoded token, used in get_student_by_id
class AccessTokenData(BaseModel):
    # student id taken from token is returned as string
    student_id: Optional[str] = None
    # define method that turns id, if exists, from str to UUID
    def get_uuid(self) -> uuid.UUID | None:
       
        return uuid.UUID(self.student_id) if self.student_id else None
        
    
    
    
# -- RESET TOKEN -- table that saves temporary tokens used for pwd reset (combines email & reset token)
class ResetTokenInDB(SQLModel, table=True):
    reset_token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True) 
    email: str = Field(max_length=320, index=True)
    token_hash: str = Field(max_length=255, index=True)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True))) # timezone=True configures the column to accept timezone-aware datetime

    


# -- REFRESH TOKEN -- token per refresh access token
class RefreshTokenInDB(SQLModel, table=True):
    refresh_token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True) 
    student_id: uuid.UUID = Field(foreign_key="studentindb.student_id")
    token_hash:  str = Field(max_length=255, index=True)
    created_at: datetime = Field(sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    revoked_at: Optional[datetime] = Field(default=None, index=True)
    
    student: "StudentInDB" = Relationship(back_populates="refresh_tokens")


class RefreshRequest(BaseModel):
    refresh_token: str
    
    model_config = ConfigDict(
        extra="ignore"
    )
