from typing import Annotated, TYPE_CHECKING, List
from sqlmodel import Relationship, SQLModel, Field
from datetime import date
from decimal import Decimal
from sqlalchemy import UniqueConstraint
import uuid
from sqlalchemy.dialects.mysql import BINARY # dialetto MySQL specifico
from sqlalchemy import Column


if TYPE_CHECKING:
    from .student import StudentInDB
    from .company import CompanyInDB
    from .internship_entry import InternshipEntryInDB


class InternshipAgreementBase(SQLModel):
    total_hours: Annotated[int, Field(max_digits=4)] 
    attended_hours: Annotated[Decimal | None, Field(max_digits=5, decimal_places=2)] 
    start_date: date 
    is_active: bool 


class InternshipAgreementInDB(InternshipAgreementBase, table=True):
    agreement_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    student_id: Annotated[int, Field(foreign_key="studentindb.student_id", index=True)]
    company_id: Annotated[int, Field(foreign_key="companyindb.company_id")]
    
    
    # attributo speciale di SQLAlchemy (declarative class attribute) per definire configurazioni avanzate della tabella
    # accetta argomenti posizionali e keyword che devono essere specificati o come Dictionary (opzioni tabella) o come Tupla (constraints)
    __table_args__ = (
        UniqueConstraint("student_id", "company_id", name="unique_student_company"), # => la virgola rende il valore una TUPLA
    )
    
    student: StudentInDB = Relationship(back_populates="internship_agreements")
    
    company: CompanyInDB = Relationship(back_populates="internship_agreements")
    
    internship_entries: List["InternshipEntryInDB"] | None = Relationship(back_populates="internship_agreement")
    

class InternshipAgreementPublic(InternshipAgreementBase):
    agreement_id: uuid.UUID