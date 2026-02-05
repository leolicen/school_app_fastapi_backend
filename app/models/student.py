from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr, field_validator
import uuid
from sqlalchemy import Column, DateTime, func
from ..utils.validators import strong_password_validator, normalize_email

if TYPE_CHECKING: # only static type check, does not work at runtime (errors with imports of code like services)
    from .course import CourseInDB
    from .internship_agreement import InternshipAgreementInDB
    from .auth import RefreshTokenInDB



# -- STUDENT BASE -- (fields shared by all models)
class StudentBase(SQLModel):
    name: str = Field(max_length=40)
    surname: str = Field(max_length=40)
    email: EmailStr = Field(max_length=40) # Pydantic string type for email validation
    course_id: uuid.UUID
    phone: Optional[str] =  Field(max_length=10, default=None)
    address: Optional[str] = Field(max_length=50, default=None)
     
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return normalize_email(v)
    
    


# -- STUDENT IN DB -- (table)
# with id (automatically generated) and hashed password
class StudentInDB(StudentBase, table=True):
    student_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: str = Field(unique=True, index=True)
    hashed_password: str = Field(max_length=255, index=True)
    course_id: uuid.UUID = Field(foreign_key="courseindb.course_id")
    
    student_updated_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), onupdate=func.now())) # automatically adds time when model is updated
    pwd_changed_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    pwd_reset_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
   
    is_active: bool = Field(default=True)
    # creation date & time for log/audit
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    # account soft delete field
    deleted_at: Optional[datetime] = Field(default=None, index=True)
    
    course: "CourseInDB" = Relationship(back_populates="students")
    
    # case of possible empty List is already handled 
    internship_agreements: List["InternshipAgreementInDB"] = Relationship(back_populates="student")
    
    refresh_tokens: List["RefreshTokenInDB"] = Relationship(back_populates="student")
    



# -- STUDENT CREATE -- (registration input)
# pwd with 8 chars min to prevent potential UI Flutter bypass 
class StudentCreate(StudentBase):
    password: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return strong_password_validator(v)
    



# -- STUDENT PUBLIC -- (read-only model for users)
class StudentPublic(StudentBase):
    student_id: uuid.UUID
    is_active: bool




# -- STUDENT UPDATE -- 
class StudentUpdate(SQLModel):
    name: Optional[str] = Field(max_length=40, default=None)
    surname: Optional[str] = Field(max_length=40, default=None)
    email: Optional[EmailStr] = Field(max_length=40, default=None) 
    phone: Optional[str] = Field(max_length=10, default=None)
    address: Optional[str] = Field(max_length=50, default=None)
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return normalize_email(v)
    