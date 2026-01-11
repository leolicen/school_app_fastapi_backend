from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import create_engine, SQLModel, Session, delete
from .settings import settings
from contextlib import asynccontextmanager 
from ..models.auth import RefreshTokenInDB
from datetime import datetime, timezone, timedelta
from fastapi_utilities import repeat_every
from ..models.student import StudentInDB

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


# -- funzione ELIMINA REFRESH TOKEN SCADUTI --
def delete_expired_refresh_tokens(session: Session) -> int:
   
    delete_stmt = delete(RefreshTokenInDB).where(
        RefreshTokenInDB.expires_at <= datetime.now(timezone.utc)
    )
    result = session.exec(delete_stmt)
    session.commit()
    
    return result.rowcount


# -- funzione ELIMINA ACCOUNT SCADUTI --
def delete_expired_accounts(session: Session) -> int:
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    
    delete_stmt = delete(StudentInDB).where(
        StudentInDB.deleted_at.is_Not(None),
        StudentInDB.deleted_at <= cutoff
    )
    
    result = session.exec(delete_stmt)
    session.commit()
    
    return result.rowcount


# -- funzione LIFESPAN app -- da inserire dentro a istanza app FastAPI()
@asynccontextmanager
async def lifespan(app: FastAPI):
    # codice startup (prima di yield)
    create_db_and_tables() 
      
    yield 
      
    # codice shutdown app (dopo yield, opzionale) per pulizia risorse, chiusura db, etc
    

# -- CRON JOB => ELIMINA REFRESH TOKEN SCADUTI ogni ora --
@repeat_every(seconds=3600)
def hourly_refresh_token_cleanup() -> None:
    with Session(engine) as session:
        try:
            deleted = delete_expired_refresh_tokens(session)
            print(f"Deleted {deleted} expired refresh tokens")
        except Exception as e:
            print(f"Refresh token cleanup failed: {e}")
            

# -- CRON JOB => ELIMINA ACCOUNT DOPO 30 GIORNI DA SOFT DELETE --
@repeat_every(seconds=3600 * 6)
def hourly_deleted_accounts_cleanup() -> None:
    with Session(engine) as session:
        try:
            deleted = delete_expired_accounts(session)
            print(f"Deleted {deleted} expired accounts")
        except Exception as e:
            print(f"Deleted accounts cleanup failed: {e}")
        