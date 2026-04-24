from datetime import datetime, timedelta, timezone
import logging
import uuid

from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy import delete
from sqlmodel import Session, select

from .auth import AuthService
from ..models.student import StudentInDB
from ..models.tutor import TutorInDB
from ..models.user import UserRole
from ..models.auth import AccessRefreshToken, ResetTokenInDB
from ..utils.validators import normalize_email
from ..exceptions.exceptions import (
    AccountExpiredError, 
    InvalidCredentialsError,
    DatabaseError, UserNotFoundError
)
from ..core.settings import settings
from .email import EmailService


logger = logging.getLogger(__name__)

class UserService():
    
    def __init__(self, session: Session, auth_service: AuthService):
        """ Initialize UserService with a DB session and auth service."""
        self._db = session
        self.auth_service = auth_service
        
        
    def _find_user_by_email(self, email: EmailStr) -> tuple[StudentInDB | TutorInDB, UserRole] | None:
        """ Retrieve user (if exists) & role from email. Used internally for unified login."""
        student = self._db.exec(select(StudentInDB).where(StudentInDB.email == email)).first()
        if student:
            return student, UserRole.STUDENT
        
        tutor = self._db.exec(select(TutorInDB).where(TutorInDB.email == email)).first()
        if tutor:
            return tutor, UserRole.TUTOR
        
        return None
    
    
    def login_for_access_token(self, form_data: OAuth2PasswordRequestForm) -> AccessRefreshToken:
        """Unified login for active & inactive users (specific endpoints check 'role' & 'is_active' separately)."""
        normalized_email = normalize_email(form_data.username)
        
        # retrieve user (if exists) & user role by email 
        result = self._find_user_by_email(normalized_email)
        if not result:
            raise InvalidCredentialsError()
        
        user, role = result
        
        # validate user password
        if not self.auth_service.verify_password(form_data.password, user.hashed_password):
            raise InvalidCredentialsError()
        
        # retrieve user id with correct property name (student_id or tutor_id)
        user_id: uuid.UUID = getattr(user, f"{role.value}_id")

        # check account expiry BEFORE the try block to avoid AppError being swallowed by except Exception
        if user.deleted_at:
            delta = datetime.now(timezone.utc) - user.deleted_at.replace(tzinfo=timezone.utc)

            if delta.days >= 30:
                raise AccountExpiredError()

            user.deleted_at = None
            user.is_active = True

        try:
            # if user is authenticated, create access token with their id
            access_token = self.auth_service.create_access_token(
                user_id,
                role,
                timedelta(minutes=settings.access_token_expire_minutes)
            )

            # create refresh token (token hash saved in db + raw token returned)
            refresh_token = self.auth_service.create_refresh_token(user_id, role, self._db)

            return AccessRefreshToken(access_token=access_token, token_type="Bearer", refresh_token=refresh_token)

        except Exception:
            self._db.rollback()
            raise DatabaseError("Login failed")
    
    
    def request_password_reset(self, email: EmailStr, background_tasks: BackgroundTasks) -> dict[str, str]:
        """Request password reset via email.
        
        Internal error handling for security reasons (no info leaked to client)."""
        try:
            # create one-time reset token (if email not valid raise ValueError)
            token = self.auth_service.create_reset_token(email=email, session=self._db)

            # attempt email transmission
            background_tasks.add_task(EmailService.send_reset_email, email, token)

            logger.info(f"Reset queued for {email}")

        except ValueError:
            logger.warning(f"Invalid reset request: {email}")
            pass

        return {"detail": "If email is valid, request was sent"}
    
    
    def reset_password(self, reset_token: ResetTokenInDB, new_password: str) -> dict[str, str]:
        """Apply a new password using a validated reset token, then delete the token from the DB.

        Records the reset timestamp in pwd_reset_at.
        """
        result = self._find_user_by_email(reset_token.email)
        if not result:
            raise UserNotFoundError()
        
        user_in_db, _ = result # role is not necessary

        # create new pwd hash
        new_pwd_hash = self.auth_service.get_password_hash(new_password)

        # substitute old pwd hash with new one
        user_in_db.hashed_password = new_pwd_hash

        # add pwd reset datetime
        user_in_db.pwd_reset_at = datetime.now(timezone.utc)

        try:
            # delete reset token
            self._db.exec(delete(ResetTokenInDB).where(ResetTokenInDB.reset_token_id == reset_token.reset_token_id))
            self._db.add(user_in_db)
            self._db.flush()
            self._db.refresh(user_in_db)

            return {"detail": "Password reset successfully"}

        except Exception:
            self._db.rollback()
            raise DatabaseError("Failed to reset password")


    def confirm_password_reset(self, raw_reset_token: str, new_password: str) -> dict[str, str]:
        """Validate the raw reset token and delegate to reset_password to apply the new password."""
        # validate reset token
        valid_reset_token = self.auth_service.validate_reset_token(raw_reset_token, self._db)

        # reset password
        return self.reset_password(valid_reset_token, new_password)
    
    
    async def logout(self, user_id: uuid.UUID, access_token: str):
        """Log out the user by revoking their refresh token and blacklisting the access token in Redis."""
        # revoke refresh token
        self.auth_service.revoke_refresh_token(user_id, self._db)

        # blacklist access token in Redis
        await self.auth_service.blacklist_access_token(access_token)

        logger.info(f"User {user_id} logged out")

        return