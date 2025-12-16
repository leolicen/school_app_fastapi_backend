from typing import TYPE_CHECKING, Annotated, List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date

if TYPE_CHECKING:
    from .course import Course

# modello studente BASE (campi comuni a tutti i modelli)
class StudentBase(SQLModel):
    name: Annotated[str, Field(max_length=40)]
    surname: Annotated[str, Field(max_length=40)]
    email: Annotated[str, Field(max_length=50)]
    course_id: int
    phone: Annotated[str | None, Field(default=None, max_length=10)] 
    address: Annotated[str | None, Field(default=None, max_length=50)]

# modello studente in DB (tabella)
# contiene id (generato automaticamente) e password hashata
class Student(StudentBase, table=True):
    student_id: Annotated[int | None, Field(default=None, primary_key=True)]
    hashed_password: Annotated[str, Field(max_length=255)]
    email: Annotated[str, Field(max_length=50,unique=True, index=True)]
    course_id: Annotated[int, Field(foreign_key="course.course_id")]
    phone: Annotated[str | None, Field(default=None, max_length=10, unique=True)] 
    
    course: Course = Relationship(back_populates="students")


# modello studente in INPUT (registrazione)
# password con min 8 caratteri per eventuali bypass della UI Flutter
class StudentCreate(StudentBase):
    password: Annotated[str, Field(max_length=255, min_length=8)]


class StudentPublic(StudentBase):
    student_id: int