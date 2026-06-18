from datetime import datetime, timezone
import logging
import uuid

from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlmodel import Session, select
from pymysql import IntegrityError
from sqlalchemy.exc import SQLAlchemyError

from .auth import AuthService
from .user import UserService
from ..models.tutor import TutorPublic, TutorInDB, TutorCreate, TutorUpdate
from ..utils.validators import normalize_email
from ..exceptions.exceptions import (
    DuplicateEmailError, 
    DatabaseError, 
    TutorNotFoundError, 
    InvalidCurrentPasswordError
)
from ..models.auth import AccessRefreshToken
from ..models.password import ChangePassword


logger = logging.getLogger(__name__)


class TutorService():
    
    def __init__(self, session: Session, auth_service: AuthService, user_service: UserService):
        """Initialize TutorService with a DB session, auth service, and user service."""
        self._db = session
        self.auth_service = auth_service
        self.user_service = user_service
        
    
    def get_tutor_by_email(self, email: EmailStr) -> TutorInDB | None:
        
        normalized_email = normalize_email(email)

        return self._db.exec(
            select(TutorInDB).where(TutorInDB.email == normalized_email)
        ).first()  # first() returns None if nothing is found
    
        
    def get_tutor_by_id(self, id: uuid.UUID) -> TutorPublic | None:
        """Check if tutor exists by id.

        Returns TutorPublic (no hashed_password) because get_current_user() doesn't need it.
        _db.get(Student, id) would also work since id is the primary key.
        
        Please Note: None is fundamental to throw an UnauthorizedRoleError in require_role when a student tries to access a tutor endpoint. 
        Model_validate breaks with a None parameter.
        """
        tutor = self._db.exec(
            select(TutorInDB).where(TutorInDB.tutor_id == id)
        ).first()

        return TutorPublic.model_validate(tutor) if tutor else None
    
    
    def register_tutor(self, tutor: TutorCreate) -> TutorPublic:
        """Register a new tutor after validating email uniqueness.

        Hashes the password before persisting. Returns TutorPublic (no hashed_password).
        """
        # check if an account with the same email already exists
        if self.get_tutor_by_email(tutor.email):
            raise DuplicateEmailError()

        # hash given password
        hashed_password = self.auth_service.get_password_hash(tutor.password)

        # create new TutorInDB model
        # model_dump creates a dict from TutorCreate fields | '**' turns dict keys into model properties
        # 'exclude' removes 'password' (plain) from the dict, replaced by 'hashed_password'
        new_tutor = TutorInDB(
            **tutor.model_dump(exclude={"password"}),
            hashed_password=hashed_password
        )

        logger.debug(f"TUTOR ID before insert in db: {new_tutor.tutor_id}")

        try:
            # add new tutor to db
            self._db.add(new_tutor)
            self._db.flush()
            self._db.refresh(new_tutor)

            logger.debug(f"TUTOR ID after add and model refresh: {new_tutor.tutor_id}")

            # convert TutorInDB into TutorPublic (response model without hashed_password)
            return TutorPublic.model_validate(new_tutor)

        except IntegrityError as e:
            self._db.rollback()

            logger.error(f"Integrity error during tutor registration: {e}", exc_info=True)

            error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

            if "duplicate entry" in error_msg and "email" in error_msg:
                raise DuplicateEmailError()
            else:
                raise DatabaseError("Unable to register tutor due to data conflict")

        except Exception as e:
            self._db.rollback()
            logger.error(f"Integrity error during tutor registration: {e}", exc_info=True)
            raise DatabaseError("Failed to register tutor")
    
    
    def register_and_login(self, tutor: TutorCreate) -> AccessRefreshToken:
        """Register a new tutor and immediately log them in, returning access and refresh tokens."""
        # register new tutor
        new_tutor = self.register_tutor(tutor)

        # create OAuth2PasswordRequestForm instance
        form_data = OAuth2PasswordRequestForm(
            # new tutor email
            username=new_tutor.email,
            # plain pwd before hashing
            password=tutor.password
        )

        # return access token after login
        return self.user_service.login_for_access_token(form_data)
    
    
    def update_tutor(self, current_tutor_id: uuid.UUID, tutor_to_update: TutorUpdate) -> TutorPublic:
        """Update the profile fields of an existing tutor. Only provided fields are changed (exclude_unset)."""
        # get tutor to update from db
        tutor_in_db = self._db.get(TutorInDB, current_tutor_id)

        if not tutor_in_db:
            raise TutorNotFoundError()

        # dump updated info
        updated_info = tutor_to_update.model_dump(exclude_unset=True)

        # update tutor in db
        tutor_in_db.sqlmodel_update(updated_info)

        try:
            self._db.add(tutor_in_db)
            self._db.flush()
            self._db.refresh(tutor_in_db)

            return TutorPublic.model_validate(tutor_in_db)

        except Exception:
            self._db.rollback()
            raise DatabaseError("Failed to update tutor")
    
    
    def change_password(self, current_tutor: TutorPublic, pwd_change: ChangePassword) -> None:
        """Change the tutor's password after verifying the current one.

        Verifies current_password against the stored hash before replacing it with the new hash.
        Also records the change timestamp in pwd_changed_at.
        """
        # retrieve tutor from db
        tutor_in_db = self.get_tutor_by_email(current_tutor.email)

        if not tutor_in_db:
            raise TutorNotFoundError()

        # check if current pwd matches the one saved in db
        if not self.auth_service.verify_password(pwd_change.current_password, tutor_in_db.hashed_password):
            raise InvalidCurrentPasswordError()

        # hash new password
        new_pwd_hash = self.auth_service.get_password_hash(pwd_change.new_pwd)

        # substitute old hashed pwd with new hashed pwd
        tutor_in_db.hashed_password = new_pwd_hash

        # add pwd change datetime
        tutor_in_db.pwd_changed_at = datetime.now(timezone.utc)

        try:
            self._db.add(tutor_in_db)
            self._db.flush()
            self._db.refresh(tutor_in_db)

        except Exception:
            self._db.rollback()
            raise DatabaseError("Failed to change password")
    

    async def delete_tutor(self, tutor: TutorPublic, access_token: str) -> dict[str, str]:
        """Soft delete: sets deleted_at and logs out the tutor."""
        try:
            # retrieve tutor from db
            tutor_in_db = self.get_tutor_by_email(tutor.email)
            # set 'deleted_at' time
            tutor_in_db.deleted_at = datetime.now(timezone.utc)
            tutor_in_db.is_active = False

            # logout
            await self.user_service.logout(tutor.tutor_id, access_token)

            logger.info(f"Tutor {tutor.tutor_id} soft deleted")

            return {"detail": "Account deletion requested. Login within 30 days to recover."}

        except SQLAlchemyError as e:
            logger.error(f"DB delete failed: {e}")
            raise DatabaseError("Delete operation failed")
