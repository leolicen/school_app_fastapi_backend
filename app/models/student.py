from datetime import datetime
from typing import TYPE_CHECKING, Annotated, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr, field_validator # tipo di stringa Pydantic per validazione email
import uuid
from sqlalchemy.dialects.mysql import BINARY # dialetto MySQL specifico
from sqlalchemy import Column, DateTime, func
from ..utils.validators import strong_password_validator, normalize_email

if TYPE_CHECKING:
    from .course import CourseInDB
    from .internship_agreement import InternshipAgreementInDB
    from .auth import RefreshTokenInDB


# -- modello STUDENTE BASE -- (campi comuni a tutti i modelli)
class StudentBase(SQLModel):
    name: Annotated[str, Field(max_length=40)]
    surname: Annotated[str, Field(max_length=40)]
    email: Annotated[EmailStr, Field(max_length=50)]
    course_id: uuid.UUID
    phone: Annotated[str | None, Field(max_length=10)] 
    address: Annotated[str | None, Field(max_length=50)]
    
    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return normalize_email(v)
    
    


# -- modello STUDENTE IN DB -- (TABELLA)
# contiene id (generato automaticamente) e password hashata
class StudentInDB(StudentBase, table=True):
    student_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    hashed_password: Annotated[str, Field(max_length=255, index=True)]
    email: Annotated[EmailStr, Field(max_length=50,unique=True, index=True)]
    course_id: Annotated[uuid.UUID, Field(foreign_key="courseindb.course_id")]
    phone: Annotated[str | None, Field(max_length=10)]
    is_active: Annotated[bool, Field(default=True)]
    # data e ora creazione per log/audit
    created_at: Annotated[datetime | None, Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))] 
    # campo per soft delete account
    deleted_at: Annotated[datetime, Field(default=None, index=True)]
    
    course: CourseInDB = Relationship(back_populates="students")
    
    # è già gestito il caso di lista vuota iniziale
    internship_agreements: List["InternshipAgreementInDB"] = Relationship(back_populates="student")
    
    refresh_tokens: List["RefreshTokenInDB"] = Relationship(back_populates="student")
    

# -- modello CREA STUDENTE -- (input registrazione)
# password con min 8 caratteri per eventuali bypass della UI Flutter
class StudentCreate(StudentBase):
    password: Annotated[str, Field(max_length=50, min_length=8)]
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return strong_password_validator(v)

# -- modello STUDENTE PUBBLICO -- (dato in lettura per utenti)
class StudentPublic(StudentBase):
    student_id: uuid.UUID
    is_active: bool


# modello AGGIORNA STUDENTE -- 
class StudentUpdate(SQLModel):
    name: Annotated[str | None, Field(max_length=40)]
    surname: Annotated[str | None, Field(max_length=40)]
    email: Annotated[EmailStr | None, Field(max_length=50)]
    phone: Annotated[str | None, Field(max_length=10)] 
    address: Annotated[str | None, Field(max_length=50)]