from datetime import datetime, timedelta, timezone
import logging
import uuid

from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlmodel import Session, select

from .auth import AuthService
from ..models.student import StudentInDB
from ..models.tutor import TutorInDB
from ..models.user import UserRole
from ..models.auth import AccessRefreshToken
from ..utils.validators import normalize_email
from ..exceptions.exceptions import (
    AccountExpiredError, 
    InvalidCredentialsError,
    DatabaseError
)
from ..core.settings import settings

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
    