from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Relationship, SQLModel, Field
import uuid
from sqlalchemy import Column, DateTime, func


if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreementInDB

# -- COMPANY IN DB -- (table)
# useful to simulate a real-world data management scenario by a admin/tutor
# + to retrieve the company name from InternshipAgreement table with a 'join' query 
class CompanyInDB(SQLModel, table=True):
    company_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(max_length=50, unique=True, index=True)
    city: str = Field(max_length=50, index=True)
    address: str = Field(max_length=50)
    tutor: Optional[str] = Field(max_length=40, default=None)
    # creation date & time for log/audit
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now())) 
    
    internship_agreements: List["InternshipAgreementInDB"] = Relationship(back_populates="company")