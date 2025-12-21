from typing import Annotated, TYPE_CHECKING, List
from sqlmodel import Relationship, SQLModel, Field
from datetime import date
from decimal import Decimal
from sqlalchemy import UniqueConstraint


if TYPE_CHECKING:
    from .student import Student
    from .company import Company
    from .internship_entry import InternshipEntry


class InternshipAgreementBase(SQLModel):
    total_hours: Annotated[int, Field(max_digits=4)] 
    attended_hours: Annotated[Decimal | None, Field(max_digits=5, decimal_places=2)] 
    start_date: date 
    is_active: bool 


class InternshipAgreement(InternshipAgreementBase, table=True):
    agreement_id: Annotated[int | None, Field(default=None, primary_key=True)]
    student_id: Annotated[int, Field(foreign_key="student.student_id", index=True)]
    company_id: Annotated[int, Field(foreign_key="company.company_id")]
    
    
    # attributo speciale di SQLAlchemy (declarative class attribute) per definire configurazioni avanzate della tabella
    # accetta argomenti posizionali e keyword che devono essere specificati o come Dictionary (opzioni tabella) o come Tupla (constraints)
    __table_args__ = (
        UniqueConstraint("student_id", "company_id", name="unique_student_company"), # => la virgola rende il valore una TUPLA
    )
    
    student: Student = Relationship(back_populates="internship_agreements")
    
    company: Company = Relationship(back_populates="internship_agreements")
    
    internship_entries: List["InternshipEntry"] | None = Relationship(back_populates="internship_agreement")
    

class InternshipAgreementPublic(InternshipAgreementBase):
    agreement_id: int 