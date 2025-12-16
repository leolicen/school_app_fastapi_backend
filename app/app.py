import os
from fastapi import FastAPI, Depends
from typing import Annotated

from sqlmodel import create_engine, SQLModel, Session
from contextlib import asynccontextmanager 




# engine = create_engine(DATABASE_URL, echo=True,pool_pre_ping=True)




# creazione db e tabelle (se già non esistono) => se cambiano i modelli create_all() 
# NON aggiorna automaticamente le tabelle esistenti, vanno usati tool di migrazione (sposti i dati su struttura nuova)
# def create_db_and_tables():
#     SQLModel.metadata.create_all(engine)


# creo una session dependency
# def get_session():
#     with Session(engine) as session:
#         yield session

# SessionDep = Annotated[Session, Depends(get_session)]

# @asynccontextmanager
# async def lifespan(app: FastAPI):
    # codice startup (prima di yield)
    # create_db_and_tables() 
      
    # yield 
      
    # codice shutdown app (dopo yield, opzionale) per pulizia risorse, chiusura db, etc


# istanza della classe FastAPI
app = FastAPI(title="ITS App API") #,lifespan=lifespan

@app.get("/{user_msg}")
async def root(user_msg: str, limit: int = 10):
    return{user_msg[:limit]}
