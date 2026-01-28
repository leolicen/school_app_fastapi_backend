from typing import TYPE_CHECKING, List, Optional
from pydantic import BaseModel
from sqlmodel import Relationship, SQLModel, Field
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import DateTime, UniqueConstraint, func
import uuid
from sqlalchemy import Column


if TYPE_CHECKING:
    from .student import StudentInDB
    from .company import CompanyInDB
    from .internship_entry import InternshipEntryInDB


class InternshipAgreementBase(SQLModel):
    total_hours: int = Field(gt=0)
    attended_hours: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=2)
    start_date: date 
    is_active: bool = Field(default=False) # False because an agreement is created before its start_date 
    # and is_active is checked by some endpoints(entry creation and deletion) in order to allow students to modify data


class InternshipAgreementInDB(InternshipAgreementBase, table=True):
    agreement_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    student_id: int = Field(foreign_key="studentindb.student_id", index=True)
    company_id: int = Field(foreign_key="companyindb.company_id")
    # date & time for log/audit
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    
    
    # attributo speciale di SQLAlchemy (declarative class attribute) per definire configurazioni avanzate della tabella
    # accetta argomenti posizionali e keyword che devono essere specificati o come Dictionary (opzioni tabella) o come Tupla (constraints)
    __table_args__ = (
        UniqueConstraint("student_id", "company_id", name="unique_student_company"), # => la virgola rende il valore una TUPLA
    )
    
    student: "StudentInDB" = Relationship(back_populates="internship_agreements")
    
    company: "CompanyInDB" = Relationship(back_populates="internship_agreements")
    
    internship_entries: List["InternshipEntryInDB"] | None = Relationship(back_populates="internship_agreement")
    

class InternshipAgreementPublic(InternshipAgreementBase):
    agreement_id: uuid.UUID
    company_name: str 