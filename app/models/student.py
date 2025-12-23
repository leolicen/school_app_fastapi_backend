from typing import TYPE_CHECKING, Annotated, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr # tipo di stringa Pydantic per validazione email
import uuid
from sqlalchemy.dialects.mysql import BINARY # dialetto MySQL specifico
from sqlalchemy import Column

if TYPE_CHECKING:
    from .course import Course
    from .company import Company
    from .internship_agreement import InternshipAgreement
    from .internship_entry import InternshipEntry

# -- modello STUDENTE BASE -- (campi comuni a tutti i modelli)
class StudentBase(SQLModel):
    name: Annotated[str, Field(max_length=40)]
    surname: Annotated[str, Field(max_length=40)]
    email: Annotated[EmailStr, Field(max_length=50)]
    course_id: uuid.UUID
    phone: Annotated[str | None, Field(max_length=10)] 
    address: Annotated[str | None, Field(max_length=50)]
    


# -- modello STUDENTE IN DB -- (TABELLA)
# contiene id (generato automaticamente) e password hashata
class Student(StudentBase, table=True):
    student_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    hashed_password: Annotated[str, Field(max_length=255, index=True)]
    email: Annotated[EmailStr, Field(max_length=50,unique=True, index=True)]
    course_id: Annotated[uuid.UUID, Field(foreign_key="course.course_id")]
    phone: Annotated[str | None, Field(max_length=10)]
    is_active: Annotated[bool, Field(default=True)]
    
    course: Course = Relationship(back_populates="students")
    
    internship_agreements: List["InternshipAgreement"] = Relationship(back_populates="student")
    

# -- modello CREA STUDENTE -- (input registrazione)
# password con min 8 caratteri per eventuali bypass della UI Flutter
class StudentCreate(StudentBase):
    password: Annotated[str, Field(max_length=50, min_length=8)]


# -- modello STUDENTE PUBBLICO -- (dato in lettura per utenti)
class StudentPublic(StudentBase):
    student_id: uuid.UUID
    is_active: bool