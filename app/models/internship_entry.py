from datetime import date, datetime, time, timedelta
from enum import Enum
from typing import TYPE_CHECKING, Optional
import uuid

from pydantic import field_validator, ValidationInfo
from sqlalchemy import Column, DateTime, UniqueConstraint, func
from sqlmodel import Relationship, SQLModel, Field

if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreementInDB


class ShiftType(str, Enum):
    IN_OFFICE = "in_office"
    REMOTE = "remote"
    

# -- INTERNSHIP ENTRY BASE -- 
class InternshipEntryBase(SQLModel):
    entry_date: date
    start_time: time 
    end_time: time 
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v, info: ValidationInfo):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time deve essere successiva a start_time')
        return v
    
    shift_type: ShiftType
    description: str = Field(max_length=150)
    
    
    
# -- INTERNSHIP IN DB -- (table)
class InternshipEntryInDB(InternshipEntryBase, table=True):
    entry_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    agreement_id: uuid.UUID = Field(foreign_key="internshipagreementindb.agreement_id", index=True)
    
    # entry date cannot be later than creation date nor 7 days prior to it 
    entry_date: date = Field(le=date.today(), ge=date.today()-timedelta(days=7)) # Pydantic check
    
    # date & time for log/audit
    created_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))
    
   
    __table_args__ = (
    UniqueConstraint("agreement_id", "start_time", "end_time", "entry_date"), # blocca duplicati perfetti
    # CheckConstraint("entry_date <= CURRENT_DATE", name="check_date_le_today"),  SQL check (ripete il pydantic check)
    # CheckConstraint("entry_date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)", name="check_date_ge_7days")  SQL check (ripete il pydantic check)
)

    
    internship_agreement: "InternshipAgreementInDB" = Relationship(back_populates="internship_entries")
    
    

# -- INTERNSHIP ENTRY CREATE -- (user input)
class InternshipEntryCreate(InternshipEntryBase):
    agreement_id: uuid.UUID 
    entry_date: date = Field(le=date.today(), ge=date.today()-timedelta(days=7))
    
    
# -- INTERNSHIP ENTRY PUBLIC -- (read-only for app users)
class InternshipEntryPublic(InternshipEntryBase):
    entry_id: uuid.UUID
    