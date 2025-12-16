from typing import TYPE_CHECKING, Annotated, List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date

if TYPE_CHECKING:
    from .student import Student

# -- COURSE -- modello unico => tabella (con id) & GET Course (anche qui serve id)

class Course(SQLModel, table=True):
    # default=None con tipo int | None permette a SQLModel di non richiedere il valore all’inserimento (lo lascia al DB)
    # L’auto-increment è abilitato automaticamente quando la colonna è intera, chiave primaria e ha default None
    course_id: Annotated[int | None, Field(default=None, primary_key=True)]
    # Field(index=True) tells SQLModel that it should create a SQL index for this column
    name: Annotated[str, Field(index=True, unique=True)]
    full_name: Annotated[str, Field()]
    course_type: Annotated[str, Field()] 
    schedule: Annotated[str, Field()]
    schedule_type: Annotated[str, Field()] 
    total_hours: Annotated[int, Field()] 
    internship_total_hours: Annotated[int, Field()] 
    start_date: Annotated[date, Field()]
    location: Annotated[str, Field()]
    is_active: Annotated[bool, Field()] 
    
     
    # Relazione inversa: lista studenti iscritti => si tratta solo di una relazione VIRTUALE, non di una vera proprietà
    # la proprietà 'students' è collegata alla proprietà 'course' della classe Student
    # permette da Course di accedere alla lista di studenti collegati al corso
    students: List["Student"] = Relationship(back_populates="course")

