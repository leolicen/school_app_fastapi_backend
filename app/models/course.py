from typing import TYPE_CHECKING, Annotated, List, Optional
from sqlmodel import SQLModel, Field, Relationship
from datetime import date
import uuid
from sqlalchemy.dialects.mysql import BINARY # dialetto MySQL specifico
from sqlalchemy import Column

if TYPE_CHECKING:
    from .student import Student

# -- modello COURSE -- modello unico => tabella (con id) & modello 'Public' per utenti app (anche qui serve id)

class CourseInDB(SQLModel, table=True):
    # UUID come ID per i modelli per garantire maggior sicurezza (id unico e non prevedibile, che non fornisce informazioni sulla app)
    course_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))] # forza BINARY(16) in MySQL
    # Field(index=True) tells SQLModel that it should create a SQL index for this column
    name: Annotated[str, Field(max_length=100, index=True, unique=True)]
    # full_name: Annotated[str, Field(max_length=150)]
    course_type: Annotated[str, Field(max_length=50)] 
    schedule: Annotated[str | None, Field(max_length=100)]
    schedule_type: Annotated[str | None, Field(max_length=100)] 
    total_hours: Annotated[int, Field(max_digits=4)] 
    internship_total_hours: Annotated[int, Field(max_digits=4)] 
    start_date: date
    location: Annotated[str, Field(max_length=100)]
    is_active: Annotated[bool, Field(default=True)]
    
     
    # Relazione inversa: lista studenti iscritti => si tratta solo di una relazione VIRTUALE, non di una vera proprietà
    # la proprietà 'students' è collegata alla proprietà 'course' della classe Student
    # permette da Course di accedere alla lista di studenti collegati al corso
    students: List["Student"] = Relationship(back_populates="course")







# default=None con tipo int | None permette a SQLModel di non richiedere il valore all’inserimento (lo lascia al DB)
    # L’auto-increment è abilitato automaticamente quando la colonna è intera, chiave primaria e ha default None
    # course_id: Annotated[int | None, Field(default=None, primary_key=True)]