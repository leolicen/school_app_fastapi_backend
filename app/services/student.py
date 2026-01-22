import uuid
from fastapi import HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from pydantic import EmailStr
from sqlalchemy import delete, update
from sqlmodel import Session, select
from app.core.settings import settings
from ..models.student import StudentCreate, StudentPublic, StudentInDB, StudentUpdate
from .auth import AuthService
from ..models.auth import AccessRefreshToken, ResetTokenInDB, RefreshTokenInDB
from ..models.password import ChangePassword
from ..utils.validators import normalize_email
from .email import EmailService
from datetime import datetime, timedelta, timezone
from ..core.redis import rdb
import logging

logger = logging.getLogger(__name__)



class StudentService():
    def __init__(self, session: Session): 
        self._db = session
        
        # creo HTTP exception in caso di errore di validazione token
        self.invalid_token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    
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
    def authenticate_student(self, email: EmailStr, password: str) -> StudentInDB | False:
        student = self.get_student_by_email(email)
        
        if not student:
            return False 
        
        if not AuthService.verify_password(password, student.hashed_password):
            return False
        
        return student
    
      
      
      
    # --  LOGIN FOR ACCESS TOKEN -- 
    # login for ACTIVE & INACTIVE students (gives access to the app), specific endpoints will check for 'is_active' field as well
    def login_for_access_token(self, form_data: OAuth2PasswordRequestForm) -> AccessRefreshToken:
        
        # authenticate student by email & password
        student = self.authenticate_student(form_data.username, form_data.password)
        
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # if 'deleted_at' field is not None (account SOFT DELETE) + <= 30 days (hard delete after), delete 'deleted_at' value and reactivate student account
        if student.deleted_at:
            delta = datetime.now(timezone.utc) - student.deleted_at
            if delta.days >= 30:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Account retrieval period expired")
            
            student.deleted_at = None
            self._db.commit()
            self._db.refresh(student)
        
        # if student is authenticated, create access token with their id
        access_token = AuthService.create_access_token(
            student.student_id, 
            timedelta(minutes=settings.access_token_expire_minutes)
            )
        
        # create refresh token (token hash saved in db + raw token returned)
        refresh_token = AuthService.create_refresh_token(student.student_id, self._db)
        
        
        return AccessRefreshToken(access_token=access_token, token_type="bearer", refresh_token=refresh_token) 
    
    
    
    
     # -- REGISTER STUDENT -- create new student
    def register_student(self, student: StudentCreate) -> StudentPublic:
        
        try:
            # check if an account with the same email already exists 
            if self.get_student_by_email(student.email):
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            
            # if not, hash given password
            hashed_password = AuthService.get_password_hash(student.password)
            
            # create new StudentInDB model
            # model_dump creates a dict with student: StudentCreate fields and values
            # '**' turns dict keys into model properties
            # 'exclude' allows to exclude 'password' field (with plain pwd) from the dict, it will be substituted by the 'hashed_password' field
            new_student = StudentInDB(
                **student.model_dump(exclude={"password"}),
                hashed_password=hashed_password
            )
            # add new student to DB
            self._db.add(new_student)
            self._db.commit()
            self._db.refresh(new_student)
            
            # convert StudentInDB model into StudentPublic (user response model without hashed_password)
            return StudentPublic.model_validate(new_student)
            
            
        except HTTPException:
            raise
        
        except Exception:
            self._db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error"
            )
            
            
            
              
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
            raise HTTPException(status_code=404, detail="Student not found")
        
        # dump updated info
        updated_info = student_to_update.model_dump(exclude_unset=True)
        # update student in db 
        student_in_db.sqlmodel_update(updated_info)
        
        self._db.add(student_in_db)
        self._db.commit()
        self._db.refresh(student_in_db)
        
        return StudentPublic.model_validate(student_in_db)
    
    
    # -- CHANGE PASSWORD -- 
    def change_password(self, current_student: StudentPublic, pwd_change: ChangePassword) -> None:
        # retrieve student from db
        student_in_db = self.get_student_by_email(current_student.email)
        
        if not student_in_db:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # check if current pwd is equal to pwd saved in db 
        if not AuthService.verify_password(pwd_change.current_password, student_in_db.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is not correct")
        
        # hash new password
        new_pwd_hash = AuthService.get_password_hash(pwd_change.new_pwd)
        
        # substitute old hashed pwd with new hashed pwd
        student_in_db.hashed_password = new_pwd_hash
        
        self._db.commit()
        self._db.refresh(student_in_db)
        
        
    
        # -- RESET PASSWORD REQUEST --
    def request_password_reset(self, student_email: EmailStr, background_tasks: BackgroundTasks) -> dict[str, str]:
        
        try:
            # create one-time reset token (if email not valid raise ValueError)
            token = AuthService.create_reset_token(email=student_email, student_service=self, session=self._db)
            
            # attempt email transmission
            background_tasks.add_task(EmailService.send_reset_email, student_email, token)
            
            # logger.info(f"Reset queued for {student_email}")
            
        except ValueError:
            #  logger.warning(f"Reset request invalid: {student_email}") ??
            pass 
        
        return {"detail": "If email is valid, request was sent"}
    
    
    
    
    def reset_password(self, reset_token: ResetTokenInDB, new_password: str) -> dict[str, str]:
        
        # retrieve student from db
        student_in_db = self.get_student_by_email(reset_token.email)
        
        # create new pwd hash
        new_pwd_hash = AuthService.get_password_hash(new_password)
        
        # substitute old pwd hash with new one
        student_in_db.hashed_password = new_pwd_hash
        
        # delete reset token 
        self._db.exec(delete(ResetTokenInDB).where(ResetTokenInDB.reset_token_id == reset_token.reset_token_id))
        
        self._db.commit()
        self._db.refresh(student_in_db)
        
        return {"detail": "Password updated successfully"}
    
    
    
    
    # -- CONFIRM PASSWORD RESET -- 
    def confirm_password_reset(self, raw_reset_token: str, new_password: str) -> dict[str, str]:
        
       # validate reset token
       valid_reset_token = AuthService.validate_reset_token(raw_reset_token, self._db)
       
       # reset password
       return self.reset_password(valid_reset_token, new_password)
        
     
 
    
    # -- REVOKE REFRESH TOKEN -- (only when logging out)
    def revoke_refresh_token(self, student_id: uuid.UUID) -> int:
        
        # query to update refresh token "revoked_at" field
        revoke_refresh_token = update(RefreshTokenInDB).where(
            RefreshTokenInDB.student_id == student_id,
            RefreshTokenInDB.revoked_at.is_(None),
            RefreshTokenInDB.expires_at > datetime.now(timezone.utc)
        ).values(revoked_at=datetime.now(timezone.utc))
        
        result = self._db.exec(revoke_refresh_token)
        
        rowcount = result.rowcount
        
        self._db.commit()
        
        if rowcount == 0:
            print(f"No active refresh token for student {student_id}")
        
        
        return rowcount
    
    
    
    
    # -- BLACKLIST ACCESS TOKEN -- (used in logout())
    async def blacklist_access_token(self, access_token: str):
        
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
        ttl = payload["exp"] - datetime.now(timezone.utc).timestamp()
        
        # insert JTI in BLACK LIST REDIS
        await rdb.setex(f"blacklist:{jti}", int(ttl), "1") 
        # 1 indicates that the inserted key exists in the list (1 because it's the smallest value possible, any other would be potentially accepted in the same way)
    
    
    # -- LOGOUT -- 
    async def logout(self, student_id: uuid.UUID, access_token: str):
       
        # REVOKE REFRESH TOKEN
        self.revoke_refresh_token(student_id)
        
        # ACCESS TOKEN IN BLACKLIST REDIS
        self.blacklist_access_token(access_token)
        
       
       
       
    # -- DELETE STUDENT -- (soft delete)
    async def delete_student(self, student: StudentPublic, access_token: str) -> dict[str, str]:
        
        # retrieve student from db
        student_in_db = self.get_student_by_email(student.email)
        # set 'deleted_at' time
        student_in_db.deleted_at = datetime.now(timezone.utc)
        
        self._db.commit()
        
        # logout
        await self.logout(student.student_id, access_token)
        
        return {"detail": "Account deletion requested. Login within 30 days to recover."}
    
   