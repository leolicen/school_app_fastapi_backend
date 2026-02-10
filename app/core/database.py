from typing import Annotated
from fastapi import Depends, FastAPI
from sqlalchemy import func, update
from sqlmodel import create_engine, SQLModel, Session, delete
from .settings import settings
from contextlib import asynccontextmanager 
from ..models.auth import RefreshTokenInDB
from datetime import datetime, timezone, timedelta
from fastapi_utilities import repeat_every
from ..models.student import StudentInDB
from ..models.internship_agreement import InternshipAgreementInDB
from sqlalchemy.exc import SQLAlchemyError
import logging



logger = logging.getLogger(__name__)

# -- create ENGINE --
engine = create_engine(settings.db_url, echo=True,pool_pre_ping=True)



# --  CREATE DB & TABLES -- (if they do not already exist) => if models change create_all() 
# DOES NOT automatically update existing tables, migration tools must be used (move data to new db structure)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
    
# -- GET SESSION --  session dependency creation -- 
def get_session():
    with Session(engine) as session:
        yield session

# -- creation SESSION DEPENDENCY INSTANCE --
SessionDep = Annotated[Session, Depends(get_session)]


# -- LIFESPAN -- to be inserted into FastAPI()
@asynccontextmanager
async def lifespan(app: FastAPI):
    # codice startup (prima di yield)
    create_db_and_tables() 
      
    yield 
    
      
    # shutdown app code (after yield, optional) for resources cleanup, db closing, etc
    
    




# --  DELETE EXPIRED REFRESH TOKENS --
def delete_expired_refresh_tokens(session: Session) -> int:
   
    delete_stmt = delete(RefreshTokenInDB).where(
        RefreshTokenInDB.expires_at <= datetime.now(timezone.utc)
    )
    result = session.exec(delete_stmt)
    session.commit()
    
    return result.rowcount


# -- DELETE EXPIRED ACCOUNTS --
def delete_expired_accounts(session: Session) -> int:
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    
    delete_stmt = delete(StudentInDB).where(
        StudentInDB.deleted_at.is_Not(None),
        StudentInDB.deleted_at <= cutoff
    )
    
    result = session.exec(delete_stmt)
    session.commit()
    
    return result.rowcount


# -- ACTIVATE AGREEMENTS --
def activate_agreements(session: Session) -> int:
    
    stmt = update(InternshipAgreementInDB).where(
        InternshipAgreementInDB.start_date <= func.current_date(), # in case of server down, checks for skipped agreements activations
        InternshipAgreementInDB.is_active == False
    ).values(is_active=True)
    
    result = session.exec(stmt)
    
    session.commit()
    
    return result.rowcount





    

# -- CRON JOB => DELETE EXPIRED REFRESH TOKEN hourly --
@repeat_every(seconds=3600)
def hourly_refresh_token_cleanup() -> None:
    
    with Session(engine) as session:
        
        try:
            deleted = delete_expired_refresh_tokens(session)
            
            logger.info(f"Refresh tokens cleanup completed",
                deleted_count=deleted, 
                operation="cleanup_refresh_tokens")
            
        except SQLAlchemyError as e:
             logger.error("Refresh token cleanup failed", 
                        error=str(e), 
                        operation="cleanup_refresh_tokens")
             
        except Exception as e:
             logger.critical("Unexpected error in refresh token cleanup", 
                           error=str(e), 
                           operation="cleanup_refresh_tokens",
                           exc_info=True)
            


# -- CRON JOB => DELETE ACCOUNT AFTER 30 DAYS SINCE SOFT DELETE --
@repeat_every(seconds=3600 * 6)
def hourly_deleted_accounts_cleanup() -> None:
    
    with Session(engine) as session:
        
        try:
            deleted = delete_expired_accounts(session)
            logger.info("Deleted accounts cleanup completed", 
                       deleted_count=deleted, 
                       operation="cleanup_deleted_accounts")
            
        except SQLAlchemyError as e:
            logger.error("Deleted accounts cleanup failed", 
                        error=str(e), 
                        operation="cleanup_deleted_accounts")
            
        except Exception as e:
            logger.critical("Unexpected error in deleted accounts cleanup", 
                           error=str(e), 
                           operation="cleanup_deleted_accounts",
                           exc_info=True)



# -- CRON JOB => ACTIVATE AGREEMENTS EVERY 8 HOUS --
@repeat_every(seconds=3600 * 8)
def activate_agreements_every_8h() -> None:
    
    with Session(engine) as session:
        
        try:
            activated = activate_agreements(session)
            logger.info("Agreements activation completed",
            activated_count=activated,
            operation="agreements_activation_8h" )
        
        except SQLAlchemyError as e:
            logger.error("Agreements activation failed", 
                        error=str(e), 
                        operation="agreements_activation_8h")
        
        except Exception as e:
            logger.critical("Unexpected error in agreements activation", 
                           error=str(e), 
                           operation="agreements_activation_8h",
                           exc_info=True)
            
                       