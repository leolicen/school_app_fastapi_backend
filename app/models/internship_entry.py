from typing import Annotated, TYPE_CHECKING
from pydantic import field_validator
from sqlmodel import Relationship, SQLModel, Field
from datetime import date, datetime, time, timedelta, timezone
from enum import Enum
import uuid
from sqlalchemy.dialects.mysql import BINARY # dialetto MySQL specifico
from sqlalchemy import CheckConstraint, Column, DateTime, UniqueConstraint, func

if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreementInDB


class ShiftType(str, Enum):
    IN_SEDE = "In sede"
    DA_REMOTO = "Da remoto"
    

# -- MODELLO INTERNSHIP ENTRY BASE -- 
class InternshipEntryBase(SQLModel):
    date: date
    start_time: time 
    end_time: time 
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time deve essere successiva a start_time')
        return v
    
    shift_type: ShiftType
    description: Annotated[str, Field(max_length=150)]
    
    
    
# -- MODELLO INTERNSHIP IN DB -- (tabella)
class InternshipEntryInDB(InternshipEntryBase, table=True):
    entry_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    agreement_id: Annotated[int, Field(foreign_key="internshipagreementindb.agreement_id", index=True)]
    # le date dei turni inseribili non possono essere successive alla data di inserimento
    # né anteriori a 7 giorni dalla stessa
    date: Annotated[date, Field(le=date.today(), ge=date.today()-timedelta(days=7))] # Pydantic check
    # data e ora creazione per log/audit
    created_at: Annotated[datetime | None, Field(default=None, sa_column=Column(DateTime(timezone=True), server_default=func.now()))] 
    
   
    __table_args__ = (
    UniqueConstraint("agreement_id", "start_time", "end_time", "date"), # blocca duplicati perfetti
    CheckConstraint("date <= CURRENT_DATE", name="check_date_le_today"), # SQL check (ripete il pydantic check)
    CheckConstraint("date >= DATE_SUB(CURRENT_DATE, INTERVAL 7 DAY)", name="check_date_ge_7days") # SQL check (ripete il pydantic check)
)

    
    internship_agreement: InternshipAgreementInDB = Relationship(back_populates="internship_entries")
    
    

# -- MODELLO CREA INTERNSHIP ENTRY -- (input utente)
class InternshipEntryCreate(InternshipEntryBase):
    agreement_id: uuid.UUID 
    date: Annotated[date, Field(le=date.today(), ge=date.today()-timedelta(days=7))]
    
# -- MODELLO INTERNSHIP ENTRY PUBBLICO -- (lettura utenti in app)
class InternshipEntryPublic(InternshipEntryBase):
    entry_id: uuid.UUID
    