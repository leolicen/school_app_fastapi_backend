from typing import TYPE_CHECKING, Annotated, List
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

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
    course_id: int
    phone: Annotated[str | None, Field(max_length=10)] 
    address: Annotated[str | None, Field(max_length=50)]


# -- modello STUDENTE IN DB -- (TABELLA)
# contiene id (generato automaticamente) e password hashata
class Student(StudentBase, table=True):
    student_id: Annotated[int | None, Field(default=None, primary_key=True)]
    hashed_password: Annotated[str, Field(max_length=255, index=True)]
    email: Annotated[EmailStr, Field(max_length=50,unique=True, index=True)]
    course_id: Annotated[int, Field(foreign_key="course.course_id")]
    phone: Annotated[str | None, Field(max_length=10)] 
    
    course: Course = Relationship(back_populates="students")
    
    internship_agreements: List["InternshipAgreement"] = Relationship(back_populates="student")
    

# -- modello CREA STUDENTE -- (input registrazione)
# password con min 8 caratteri per eventuali bypass della UI Flutter
class StudentCreate(StudentBase):
    password: Annotated[str, Field(max_length=50, min_length=8)]


# -- modello STUDENTE PUBBLICO -- (dato in lettura per utenti)
class StudentPublic(StudentBase):
    student_id: int