import logging
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from pymysql import IntegrityError
import redis.asyncio as redis
from pydantic import EmailStr
from sqlalchemy import delete, update
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from ..core.settings import settings
from ..exceptions.exceptions import (
    AccountExpiredError,
    CourseNotFoundError,
    DatabaseError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    StudentNotFoundError,
)
from ..models.auth import AccessRefreshToken, RefreshTokenInDB, ResetTokenInDB
from ..models.course import CourseInDB
from ..models.password import ChangePassword
from ..models.student import StudentCreate, StudentInDB, StudentPublic, StudentUpdate
from ..utils.validators import normalize_email
from .auth import AuthService
from .email import EmailService


logger = logging.getLogger(__name__)


class StudentService():

    def __init__(self, session: Session, auth_service: AuthService, redis_client: redis.Redis):
        """Initialize StudentService with a DB session, auth service, and Redis client."""
        self._db = session
        self.auth_service = auth_service
        self.redis = redis_client


    def get_student_by_email(self, email: EmailStr) -> StudentInDB | None:
        """Check if student exists by email.

        Returns StudentInDB (table model) because authenticate_student() needs access to 'hashed_password'.
        """
        normalized_email = normalize_email(email)

        return self._db.exec(
            select(StudentInDB).where(StudentInDB.email == normalized_email)
        ).first()  # first() returns None if nothing is found


    def get_student_by_id(self, id: uuid.UUID) -> StudentPublic | None:
        """Check if student exists by id.

        Returns StudentPublic (no hashed_password) because get_current_student() doesn't need it.
        _db.get(Student, id) would also work since id is the primary key.
        """
        student = self._db.exec(
            select(StudentInDB).where(StudentInDB.student_id == id)
        ).first()

        return StudentPublic.model_validate(student)


    def authenticate_student(self, email: EmailStr, password: str) -> StudentInDB | None:
        """Authenticate student during login.

        Returns StudentInDB because the login function only returns a token, not the student object.
        """
        if not (student := self.get_student_by_email(email)):  # walrus operator ':='
            return None

        if not self.auth_service.verify_password(password, student.hashed_password):
            return None

        return student


    def login_for_access_token(self, form_data: OAuth2PasswordRequestForm) -> AccessRefreshToken:
        """Login for active & inactive students (specific endpoints check 'is_active' separately)."""
        # authenticate student by email & password
        student = self.authenticate_student(form_data.username, form_data.password)

        if not student:
            raise InvalidCredentialsError()

        # check account expiry BEFORE the try block to avoid AppError being swallowed by except Exception
        if student.deleted_at:
            delta = datetime.now(timezone.utc) - student.deleted_at.replace(tzinfo=timezone.utc)

            if delta.days >= 30:
                raise AccountExpiredError()

            student.deleted_at = None
            student.is_active = True

        try:
            # if student is authenticated, create access token with their id
            access_token = self.auth_service.create_access_token(
                student.student_id,
                timedelta(minutes=settings.access_token_expire_minutes)
            )

            # create refresh token (token hash saved in db + raw token returned)
            refresh_token = self.auth_service.create_refresh_token(student.student_id, self._db)

            return AccessRefreshToken(access_token=access_token, token_type="Bearer", refresh_token=refresh_token)

        except Exception:
            self._db.rollback()
            raise DatabaseError("Login failed")


    def register_student(self, student: StudentCreate) -> StudentPublic:
        """Register a new student after validating email uniqueness and course existence.

        Hashes the password before persisting. Returns StudentPublic (no hashed_password).
        """
        # check if an account with the same email already exists
        if self.get_student_by_email(student.email):
            raise DuplicateEmailError()

        # check if inserted course_id is an existing active course
        course = self._db.exec(
            select(CourseInDB).where(
                CourseInDB.course_id == student.course_id,
                CourseInDB.is_active == True
            )
        ).first()

        if not course:
            raise CourseNotFoundError()

        # hash given password
        hashed_password = self.auth_service.get_password_hash(student.password)

        # create new StudentInDB model
        # model_dump creates a dict from StudentCreate fields | '**' turns dict keys into model properties
        # 'exclude' removes 'password' (plain) from the dict, replaced by 'hashed_password'
        new_student = StudentInDB(
            **student.model_dump(exclude={"password"}),
            hashed_password=hashed_password
        )

        logger.debug(f"STUDENT ID before insert in db: {new_student.student_id}")

        try:
            # add new student to db
            self._db.add(new_student)
            self._db.flush()
            self._db.refresh(new_student)

            logger.debug(f"STUDENT ID after add and model refresh: {new_student.student_id}")

            # convert StudentInDB into StudentPublic (response model without hashed_password)
            return StudentPublic.model_validate(new_student)

        except IntegrityError as e:
            self._db.rollback()

            logger.error(f"Integrity error during student registration: {e}", exc_info=True)

            error_msg = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()

            if "duplicate entry" in error_msg and "email" in error_msg:
                raise DuplicateEmailError()
            else:
                raise DatabaseError("Unable to register student due to data conflict")

        except Exception as e:
            self._db.rollback()
            logger.error(f"Integrity error during student registration: {e}", exc_info=True)
            raise DatabaseError("Failed to register student")


    def register_and_login(self, student: StudentCreate) -> AccessRefreshToken:
        """Register a new student and immediately log them in, returning access and refresh tokens."""
        # register new student
        new_student = self.register_student(student)

        # create OAuth2PasswordRequestForm instance
        form_data = OAuth2PasswordRequestForm(
            # new student email
            username=new_student.email,
            # plain pwd before hashing
            password=student.password
        )

        # return access token after login
        return self.login_for_access_token(form_data)


    def update_student(self, current_student_id: uuid.UUID, student_to_update: StudentUpdate) -> StudentPublic:
        """Update the profile fields of an existing student. Only provided fields are changed (exclude_unset)."""
        # get student to update from db
        student_in_db = self._db.get(StudentInDB, current_student_id)

        if not student_in_db:
            raise StudentNotFoundError()

        # dump updated info
        updated_info = student_to_update.model_dump(exclude_unset=True)

        # update student in db
        student_in_db.sqlmodel_update(updated_info)

        try:
            self._db.add(student_in_db)
            self._db.flush()
            self._db.refresh(student_in_db)

            return StudentPublic.model_validate(student_in_db)

        except Exception:
            self._db.rollback()
            raise DatabaseError("Failed to update student")


    def change_password(self, current_student: StudentPublic, pwd_change: ChangePassword) -> None:
        """Change the student's password after verifying the current one.

        Verifies current_password against the stored hash before replacing it with the new hash.
        Also records the change timestamp in pwd_changed_at.
        """
        # retrieve student from db
        student_in_db = self.get_student_by_email(current_student.email)

        if not student_in_db:
            raise StudentNotFoundError()

        # check if current pwd matches the one saved in db
        if not self.auth_service.verify_password(pwd_change.current_password, student_in_db.hashed_password):
            raise InvalidCurrentPasswordError()

        # hash new password
        new_pwd_hash = self.auth_service.get_password_hash(pwd_change.new_pwd)

        # substitute old hashed pwd with new hashed pwd
        student_in_db.hashed_password = new_pwd_hash

        # add pwd change datetime
        student_in_db.pwd_changed_at = datetime.now(timezone.utc)

        try:
            self._db.add(student_in_db)
            self._db.flush()
            self._db.refresh(student_in_db)

        except Exception:
            self._db.rollback()
            raise DatabaseError("Failed to change password")


    def request_password_reset(self, student_email: EmailStr, background_tasks: BackgroundTasks) -> dict[str, str]:
        """Internal error handling for security reasons (no info leaked to client)."""
        try:
            # create one-time reset token (if email not valid raise ValueError)
            token = self.auth_service.create_reset_token(email=student_email, session=self._db)

            # attempt email transmission
            background_tasks.add_task(EmailService.send_reset_email, student_email, token)

            logger.info(f"Reset queued for {student_email}")

        except ValueError:
            logger.warning(f"Invalid reset request: {student_email}")
            pass

        return {"detail": "If email is valid, request was sent"}


    def reset_password(self, reset_token: ResetTokenInDB, new_password: str) -> dict[str, str]:
        """Apply a new password using a validated reset token, then delete the token from the DB.

        Records the reset timestamp in pwd_reset_at.
        """
        # retrieve student from db
        student_in_db = self.get_student_by_email(reset_token.email)

        # unnecessary check (token already validated), only for 100% security
        if not student_in_db:
            raise StudentNotFoundError()

        # create new pwd hash
        new_pwd_hash = self.auth_service.get_password_hash(new_password)

        # substitute old pwd hash with new one
        student_in_db.hashed_password = new_pwd_hash

        # add pwd reset datetime
        student_in_db.pwd_reset_at = datetime.now(timezone.utc)

        try:
            # delete reset token
            self._db.exec(delete(ResetTokenInDB).where(ResetTokenInDB.reset_token_id == reset_token.reset_token_id))
            self._db.add(student_in_db)
            self._db.flush()
            self._db.refresh(student_in_db)

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


    def revoke_refresh_token(self, student_id: uuid.UUID) -> int:
        """Revoke active refresh tokens for this student. Used only during logout."""
        try:
            # query to update refresh token "revoked_at" field
            revoke_refresh_token = update(RefreshTokenInDB).where(
                RefreshTokenInDB.student_id == student_id,
                RefreshTokenInDB.revoked_at.is_(None),
                RefreshTokenInDB.expires_at > datetime.now(timezone.utc)
            ).values(revoked_at=datetime.now(timezone.utc))

            result = self._db.exec(revoke_refresh_token)

            rowcount = result.rowcount

            if rowcount == 0:
                logger.debug(f"No active refresh token for student {student_id}")
            else:
                logger.info(f"Revoked {rowcount} refresh token(s) for student {student_id}")

            return rowcount

        except SQLAlchemyError as e:
            self._db.rollback()
            logger.error(f"Failed to revoke refresh tokens for {student_id}: {str(e)}")
            raise DatabaseError("Failed to revoke refresh tokens")


    async def blacklist_access_token(self, access_token: str):
        """Blacklist the access token jti in Redis. Used only during logout."""
        try:
            # decode received token
            payload = jwt.decode(
                access_token,
                settings.secret_key,
                algorithms=[settings.algorithm],
                options={"verify_exp": False}
            )

            # extract jti
            jti = payload["jti"]
            # extract expiration
            exp = payload["exp"]
            # calculate time to live
            ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))  # tells redis how long the token must be blacklisted before deletion

            if ttl > 0:
                # insert JTI in Redis blacklist
                await self.redis.setex(f"blacklist:{jti}", int(ttl), "1")
                # 1 indicates key exists in the list (smallest possible value)
                logger.debug(f"Blacklisted access token {jti[:8]}... (TTL: {ttl}s)")

        except jwt.InvalidTokenError:
            logger.warning("Invalid access token provided for blacklist")

        except Exception as e:
            logger.error(f"Redis blacklist failed: {str(e)}")


    async def logout(self, student_id: uuid.UUID, access_token: str):
        """Log out the student by revoking their refresh token and blacklisting the access token in Redis."""
        # revoke refresh token
        self.revoke_refresh_token(student_id)

        # blacklist access token in Redis
        await self.blacklist_access_token(access_token)

        logger.info(f"Student {student_id} logged out")

        return


    async def delete_student(self, student: StudentPublic, access_token: str) -> dict[str, str]:
        """Soft delete: sets deleted_at and logs out the student."""
        try:
            # retrieve student from db
            student_in_db = self.get_student_by_email(student.email)
            # set 'deleted_at' time
            student_in_db.deleted_at = datetime.now(timezone.utc)
            student_in_db.is_active = False

            # logout
            await self.logout(student.student_id, access_token)

            logger.info(f"Student {student.student_id} soft deleted")

            return {"detail": "Account deletion requested. Login within 30 days to recover."}

        except SQLAlchemyError as e:
            logger.error(f"DB delete failed: {e}")
            raise DatabaseError("Delete operation failed")
