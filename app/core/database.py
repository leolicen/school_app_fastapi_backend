from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import create_engine, SQLModel, Session
from .settings import settings
from contextlib import asynccontextmanager 

# -- creazione ENGINE --
engine = create_engine(settings.db_url, echo=True,pool_pre_ping=True)


# -- funzione CREA DB & TABELLE -- (se già non esistono) => se cambiano i modelli create_all() 
# NON aggiorna automaticamente le tabelle esistenti, vanno usati tool di migrazione (sposti i dati su struttura nuova)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
# -- funzione CREA SESSION DEPENDENCY -- 
def get_session():
    with Session(engine) as session:
        yield session

# -- creazione ISTANZA SESSION DEPENDENCY --
SessionDep = Annotated[Session, Depends(get_session)]


# -- funzione LIFESPAN app -- da inserire dentro a istanza app FastAPI()
@asynccontextmanager
async def lifespan(app: FastAPI):
    # codice startup (prima di yield)
    create_db_and_tables() 
      
    yield 
      
    # codice shutdown app (dopo yield, opzionale) per pulizia risorse, chiusura db, etc