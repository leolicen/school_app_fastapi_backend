from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional
import sqlalchemy
from sqlmodel import Relationship, SQLModel, Field
import uuid
from sqlalchemy import Column, DateTime, func, text

from .guid import GUID


if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreementInDB

# -- COMPANY IN DB -- (table)
class CompanyInDB(SQLModel, table=True):
    """ 
    Model that simulates a real-world data management scenario by a admin/tutor.
    It also allows to retrieve the company name from InternshipAgreement table with a 'join' query. 
    
    """
    company_id: uuid.UUID = Field(
        sa_column=Column(
            "company_id",
            GUID(), # sets CHAR(32) as column type, converts CHAR(32) back to Python uuid.UUID
            primary_key=True,
            default=uuid.uuid4, # just in case the record was created Python-side
            server_default=text("(REPLACE(UUID(), '-', ''))") # automatically creates UUID through SQL function UUID() removing '-' (SQL code)
        )
    ) 
    name: str = Field(max_length=50, unique=True, index=True)
    city: str = Field(max_length=50, index=True)
    address: str = Field(max_length=50)
    tutor: Optional[str] = Field(max_length=40, default=None)
    
    # creation date & time for log/audit
    created_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=text("CURRENT_TIMESTAMP"),
            nullable=False
        )
        ) 
  
    # RELATIONSHIPS
    internship_agreements: List["InternshipAgreementInDB"] = Relationship(back_populates="company")