import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi_utilities import repeat_every
from sqlalchemy import func, update
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import create_engine, delete, Session, SQLModel

from .settings import settings
from ..models.auth import RefreshTokenInDB
from ..models.student import StudentInDB
from ..models.internship_agreement import InternshipAgreementInDB


logger = logging.getLogger(__name__)

# create engine
engine = create_engine(settings.db_url, echo=True, pool_pre_ping=True)


def create_db_and_tables():
    """Create all database tables if they do not already exist.

    Note: if models change, it does not migrate existing tables — use Alembic for schema changes.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """Yield a database session with auto-commit on exit."""
    with Session(engine) as session:
        yield session
        session.commit()


# session dependency
SessionDep = Annotated[Session, Depends(get_session)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler.

    Startup (before yield): initializes database tables.
    Shutdown (after yield): placeholder for resource cleanup (db closing, etc.).
    """
    create_db_and_tables()

    yield


def delete_expired_refresh_tokens(session: Session) -> int:
    """Delete all expired refresh tokens. Returns the number of deleted rows."""
    delete_stmt = delete(RefreshTokenInDB).where(
        RefreshTokenInDB.expires_at <= datetime.now(timezone.utc)
    )
    result = session.exec(delete_stmt)
    session.commit()

    return result.rowcount


def delete_expired_accounts(session: Session) -> int:
    """Delete all expired accounts (soft-deleted more than 30 days ago). Returns the number of deleted rows."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    delete_stmt = delete(StudentInDB).where(
        StudentInDB.deleted_at.is_Not(None),
        StudentInDB.deleted_at <= cutoff
    )

    result = session.exec(delete_stmt)
    session.commit()

    return result.rowcount


def activate_agreements(session: Session) -> int:
    """Activate agreements whose start_date has been reached. Returns the number of modified rows.

    Checks for agreements that should have been activated in the past to handle missed
    activations caused by server downtime.
    """
    stmt = update(InternshipAgreementInDB).where(
        InternshipAgreementInDB.start_date <= func.current_date(),
        InternshipAgreementInDB.is_active == False
    ).values(is_active=True)

    result = session.exec(stmt)
    session.commit()

    return result.rowcount


@repeat_every(seconds=3600)
def hourly_refresh_token_cleanup() -> None:
    """Cron job: delete expired refresh tokens every hour."""
    with Session(engine) as session:
        try:
            deleted = delete_expired_refresh_tokens(session)

            logger.info(
                "Refresh tokens cleanup completed",
                deleted_count=deleted,
                operation="cleanup_refresh_tokens",
            )

        except SQLAlchemyError as e:
            logger.error(
                "Refresh token cleanup failed",
                error=str(e),
                operation="cleanup_refresh_tokens",
            )

        except Exception as e:
            logger.critical(
                "Unexpected error in refresh token cleanup",
                error=str(e),
                operation="cleanup_refresh_tokens",
                exc_info=True,
            )


@repeat_every(seconds=3600 * 6)
def hourly_deleted_accounts_cleanup() -> None:
    """Cron job: delete expired accounts (30 days after soft delete) every 6 hours."""
    with Session(engine) as session:
        try:
            deleted = delete_expired_accounts(session)

            logger.info(
                "Deleted accounts cleanup completed",
                deleted_count=deleted,
                operation="cleanup_deleted_accounts",
            )

        except SQLAlchemyError as e:
            logger.error(
                "Deleted accounts cleanup failed",
                error=str(e),
                operation="cleanup_deleted_accounts",
            )

        except Exception as e:
            logger.critical(
                "Unexpected error in deleted accounts cleanup",
                error=str(e),
                operation="cleanup_deleted_accounts",
                exc_info=True,
            )


@repeat_every(seconds=3600 * 8)
def activate_agreements_every_8h() -> None:
    """Cron job: activate agreements every 8 hours."""
    with Session(engine) as session:
        try:
            activated = activate_agreements(session)

            logger.info(
                "Agreements activation completed",
                activated_count=activated,
                operation="agreements_activation_8h",
            )

        except SQLAlchemyError as e:
            logger.error(
                "Agreements activation failed",
                error=str(e),
                operation="agreements_activation_8h",
            )

        except Exception as e:
            logger.critical(
                "Unexpected error in agreements activation",
                error=str(e),
                operation="agreements_activation_8h",
                exc_info=True,
            )
