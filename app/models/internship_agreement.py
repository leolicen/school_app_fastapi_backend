from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Relationship, SQLModel, Field
from datetime import date, datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Column, ForeignKey, UniqueConstraint, text, event, DDL
import uuid

from .guid import GUID


if TYPE_CHECKING:
    from .student import StudentInDB
    from .company import CompanyInDB
    from .internship_entry import InternshipEntryInDB


class InternshipAgreementBase(SQLModel):
    total_hours: int = Field(gt=0)
    attended_hours: Optional[Decimal] = Field(default=None, max_digits=5, decimal_places=2)
    start_date: date 
    is_active: bool = Field(
        default=False, # Python-side 
        sa_column=Column(
            "is_active",
            Boolean,
            nullable=False,
            server_default=text("0") # MySql uses tinyint(1) for Boolean 
        )
        ) # False because an agreement is created before its start_date 
    # and is_active is checked by some endpoints(entry creation and deletion) in order to allow students to modify data


class InternshipAgreementInDB(InternshipAgreementBase, table=True):
    agreement_id: uuid.UUID = Field(
        sa_column=Column(
            "agreement_id",
            GUID(), # sets CHAR(32) as column type, converts CHAR(32) back to Python uuid.UUID
            primary_key=True,
            default=uuid.uuid4 # just in case the record was created Python-side
        )
        )
    student_id: uuid.UUID = Field(
        sa_column=Column(
            "student_id",
            GUID(),
            ForeignKey("studentindb.student_id"),
            index=True,
            nullable=False
        )
        )
    company_id: uuid.UUID = Field(
        sa_column=Column(
            "company_id",
            GUID(),
            ForeignKey("companyindb.company_id"),
            nullable=False
        )
        )
    # date & time for log/audit
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False
        )
        ) 
    
    
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
    
    
    

agreement_trigger_ddl = DDL(
    """ 
    CREATE TRIGGER IF NOT EXISTS before_insert_internshipagreementindb
    BEFORE INSERT ON internshipagreementindb FOR EACH ROW
    BEGIN
        IF NEW.agreement_id IS NULL OR NEW.agreement_id = '' THEN
            SET NEW.agreement_id = REPLACE(UUID(), '-', '');
        END IF;
    END
    """
)

@event.listens_for(InternshipAgreementInDB.__table__, "after_create")
def create_agreement_trigger(target, connection, **kw):
    
    print(f"Tabella: {target.name}")  
    print(f"Dialect: {connection.dialect.name}")
    
    if connection.dialect.name == "mysql":
        connection.execute(agreement_trigger_ddl)
    
    
    