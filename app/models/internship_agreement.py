from typing import Annotated, TYPE_CHECKING, List
from sqlmodel import Relationship, SQLModel, Field
from datetime import date
from decimal import Decimal


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
    # agreement_id: Annotated[int | None, Field(default=None, primary_key=True)]
    student_id: Annotated[int, Field(foreign_key="student.student_id", primary_key=True, index=True)]
    company_id: Annotated[int, Field(foreign_key="company.company_id", primary_key=True)]
    
    student: Student = Relationship(back_populates="internship_agreements")
    
    company: Company = Relationship(back_populates="internship_agreements")
    
    internship_entries: List["InternshipEntry"] | None = Relationship(back_populates="internship_agreement")
    

class InternshipAgreementPublic(InternshipAgreementBase):
    agreement_id: int 