import uuid
from fastapi import BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import jwt
import logging
from pymysql import IntegrityError
import redis.asyncio as redis
from pydantic import EmailStr
from sqlalchemy import delete, update
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session, select

from app.core.settings import settings
from ..models.auth import AccessRefreshToken, ResetTokenInDB, RefreshTokenInDB
from ..models.password import ChangePassword
from ..utils.validators import normalize_email
from .email import EmailService
from datetime import datetime, timedelta, timezone
from ..exceptions.exceptions import (InvalidCredentialsError, AccountExpiredError, DuplicateEmailError, DatabaseError, 
                                     StudentNotFoundError, InvalidCurrentPasswordError, CourseNotFoundError)

from ..models.student import StudentCreate, StudentPublic, StudentInDB, StudentUpdate
from ..models.course import CourseInDB
from .auth import AuthService



logger = logging.getLogger(__name__)


class StudentService():
    
    
    def __init__(self, session: Session, auth_service: AuthService, redis_client: redis.Redis): 
        self._db = session
        self.auth_service = auth_service
        self.redis = redis_client
        
    
    # --  GET STUDENT BY EMAIL -- 
    # checks if student exists by email
    # returns StudentInDB (table model) because authenticate_student() needs to access 'hashed_password' field
    def get_student_by_email(self, email: EmailStr) -> StudentInDB | None:
        
        normalized_email = normalize_email(email)
        
        return self._db.exec(
            select(StudentInDB).where(StudentInDB.email == normalized_email)
        ).first() # first() returns None if nothing is found
        
        
        
    # --  GET STUDENT BY ID -- 
    # checks if student exists by id
    # returns StudentPublic because get_current_student(), where the function is called, doesn't need to access 'hashed_password' field + it's safer
    # _db.get(Student, id) would work as well because id is Student's PK (primary key)
    def get_student_by_id(self, id: uuid.UUID) -> StudentPublic | None:
        
        student = self._db.exec(
            select(StudentInDB).where(StudentInDB.student_id == id)
        ).first()
        
        return StudentPublic.model_validate(student)
        
        
        
    # --  AUTHENTICATE STUDENT -- during login
    # returns StudentInDB (table model) because the function needs to access 'hashed_password' field + in login function, where the function will be called, only the Token will be returned
    def authenticate_student(self, email: EmailStr, password: str) -> StudentInDB | None:
        
        if not (student:= self.get_student_by_email(email)): # walrus operator ':='
            return None 
        
        if not self.auth_service.verify_password(password, student.hashed_password):
            return None
        
        return student
    
      
      
    # --  LOGIN FOR ACCESS TOKEN -- 
    # login for ACTIVE & INACTIVE students (gives access to the app), specific endpoints will check for 'is_active' field as well
    def login_for_access_token(self, form_data: OAuth2PasswordRequestForm) -> AccessRefreshToken:
        
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

        except Exception as e:
            self._db.rollback()
            raise DatabaseError("Login failed")
            
            
            
     # -- REGISTER STUDENT -- create new student
    def register_student(self, student: StudentCreate) -> StudentPublic:
        
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
        new_student = StudentInDB(
            **student.model_dump(exclude={"password"}), # model_dump creates a dict with student: StudentCreate fields and values | '**' turns dict keys into model properties | 'exclude' allows to exclude 'password' field (with plain pwd) from the dict, it will be substituted by the 'hashed_password' field
            hashed_password=hashed_password
        )
        
        logger.debug(f"STUDENT ID before insert in db: {new_student.student_id}")
        
        try:
            # add new student to DB
            self._db.add(new_student)
            self._db.flush()
            self._db.refresh(new_student)
            
            logger.debug(f"STUDENT ID after add and model refresh: {new_student.student_id}")
            
            
            # convert StudentInDB model into StudentPublic (user response model without hashed_password)
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
            raise DatabaseError(f"Failed to register student")
        
   
                  
    # -- REGISTER & LOGIN --
    def register_and_login(self, student: StudentCreate) -> AccessRefreshToken:
        
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
    
    
    
    # -- UPDATE STUDENT --
    def update_student(self, current_student_id: uuid.UUID, student_to_update: StudentUpdate) -> StudentPublic:
        
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
    
    
    
    # -- CHANGE PASSWORD -- 
    def change_password(self, current_student: StudentPublic, pwd_change: ChangePassword) -> None:
        
        # retrieve student from db
        student_in_db = self.get_student_by_email(current_student.email)
        
        if not student_in_db:
            raise StudentNotFoundError()
        
        # check if current pwd is equal to pwd saved in db 
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

        except Exception as e:
            self._db.rollback()
            raise DatabaseError(f"Failed to change password")
        
        
        
    # -- RESET PASSWORD REQUEST -- internal error handling for security reasons
    def request_password_reset(self, student_email: EmailStr, background_tasks: BackgroundTasks) -> dict[str, str]:
        
        try:
            # create one-time reset token (if email not valid raise ValueError)
            token = self.auth_service.create_reset_token(email=student_email, session=self._db)
            
            # attempt email transmission
            background_tasks.add_task(EmailService.send_reset_email, student_email, token)
            
            logger.info(f"Reset queued for {student_email}")
            
        except ValueError:
            logger.warning(f"invalid reset request: {student_email}") 
            pass 
        
        return {"detail": "If email is valid, request was sent"}
    
    
    
    def reset_password(self, reset_token: ResetTokenInDB, new_password: str) -> dict[str, str]:
        
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
    
    
    
    # -- CONFIRM PASSWORD RESET -- 
    def confirm_password_reset(self, raw_reset_token: str, new_password: str) -> dict[str, str]:
        
       # validate reset token
       valid_reset_token = self.auth_service.validate_reset_token(raw_reset_token, self._db)
       
       # reset password
       return self.reset_password(valid_reset_token, new_password)
        
     
 
    # -- REVOKE REFRESH TOKEN -- (only when logging out)
    def revoke_refresh_token(self, student_id: uuid.UUID) -> int:
        
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
    
    
    
    # -- BLACKLIST ACCESS TOKEN -- (used in logout())
    async def blacklist_access_token(self, access_token: str):
        
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
            ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))  # tells redis how much time the token must be blacklisted before deletion
            
            if ttl > 0:
                # insert JTI in BLACK LIST REDIS
                await self.redis.setex(f"blacklist:{jti}", int(ttl), "1") 
                # 1 indicates that the inserted key exists in the list (1 because it's the smallest value possible, any other would be potentially accepted in the same way)
                logger.debug(f"Blacklisted access token {jti[:8]}... (TTL: {ttl}s)")
        
        except jwt.InvalidTokenError:
            logger.warning("Invalid access token provided for blacklist")
        
        except Exception as e:
            logger.error(f"Redis blacklist failed: {str(e)}")
    
    
    
    # -- LOGOUT -- 
    async def logout(self, student_id: uuid.UUID, access_token: str):
       
        # REVOKE REFRESH TOKEN
        self.revoke_refresh_token(student_id)
        
        # ACCESS TOKEN IN BLACKLIST REDIS
        await self.blacklist_access_token(access_token)
        
        logger.info(f"Student {student_id} logged out")
        
        return
        
       
       
    # -- DELETE STUDENT -- (soft delete)
    async def delete_student(self, student: StudentPublic, access_token: str) -> dict[str, str]:
        
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
        
        except SQLAlchemyError as e :
            logger.error(f"DB delete failed: {e}")
            
            raise DatabaseError("Delete operation failed")
    
   