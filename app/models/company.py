from typing import Annotated, TYPE_CHECKING, List
from sqlmodel import Relationship, SQLModel, Field


if TYPE_CHECKING:
    from .internship_agreement import InternshipAgreement

# -- modello AZIENDA IN DB -- (tabella)
# utile a fini di simulazione di gestione reale da parte di admin/tutor 
# e per recuperare tramite join da InternshipAgreeement il nome dell'azienda
# sulla app studenti
class Company(SQLModel, table=True):
    # tutti i campi sono opzionali, la tabella verrà riempita successivamente
    company_id: Annotated[int | None, Field(default=None, primary_key=True)]
    name: Annotated[str, Field(max_length=50, unique=True, index=True)]
    city: Annotated[str, Field(max_length=50, index=True)]
    address: Annotated[str, Field(max_length=50)]
    tutor: Annotated[str | None, Field(max_length=40)]
    
    internship_agreements: List["InternshipAgreement"] = Relationship(back_populates="company")