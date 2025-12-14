import os
from fastapi import FastAPI, Depends
from typing import Annotated

from sqlmodel import create_engine, SQLModel, Session
from contextlib import asynccontextmanager 


# --- da cancellare ---

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")


DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4&pool_timeout=30"
# il parametro 'echo' serve a stampare su terminale tutte le query SQL eseguite

# --- da cancellare ---

engine = create_engine(DATABASE_URL, echo=True,pool_pre_ping=True)




# creazione db e tabelle (se già non esistono) => se cambiano i modelli create_all() 
# NON aggiorna automaticamente le tabelle esistenti, vanno usati tool di migrazione (sposti i dati su struttura nuova)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# creo una session dependency
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

@asynccontextmanager
async def lifespan(app: FastAPI):
    # codice startup (prima di yield)
    create_db_and_tables() 
      
    yield 
      
    # codice shutdown app (dopo yield, opzionale) per pulizia risorse, chiusura db, etc


# istanza della classe FastAPI
app = FastAPI(title="ITS App API",lifespan=lifespan)
