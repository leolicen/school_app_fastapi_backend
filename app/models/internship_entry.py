from typing import Annotated, TYPE_CHECKING, List
from pydantic import field_validator
from sqlmodel import Relationship, SQLModel, Field
from datetime import date, time
from enum import Enum
import uuid
from sqlalchemy.dialects.mysql import BINARY # dialetto MySQL specifico
from sqlalchemy import Column

if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreement


class ShiftType(str, Enum):
    IN_SEDE = "In sede"
    DA_REMOTO = "Da remoto"
    

# -- MODELLO INTERNSHIP ENTRY BASE -- 
class InternshipEntryBase(SQLModel):
    date: Annotated[date, Field(le=date.today())]
    start_time: time 
    end_time: time 
    
    @field_validator('end_time')
    def end_after_start(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time deve essere successiva a start_time')
        return v
    
    shift_type: ShiftType
    description: Annotated[str, Field(max_length=150)]
    
# -- MODELLO INTERNSHIP IN DB -- (tabella)
class InternshipEntryInDB(InternshipEntryBase, table=True):
    entry_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    agreement_id: Annotated[int, Field(foreign_key="internshipagreement.agreement_id", index=True)]
    
    internship_agreement: InternshipAgreement = Relationship(back_populates="internship_entries")
    
    

# -- MODELLO CREA INTERNSHIP ENTRY -- (input utente)
class InternshipEntryCreate(InternshipEntryBase):
    agreement_id: uuid.UUID 
    
# -- MODELLO INTERNSHIP ENTRY PUBBLICO -- (lettura utenti in app)
class InternshipEntryPublic(InternshipEntryBase):
    entry_id: uuid.UUID
    