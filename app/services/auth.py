from datetime import datetime, timedelta, timezone
import uuid
import jwt
from pwdlib import PasswordHash
from sqlalchemy.exc import SQLAlchemyError
import redis.asyncio as redis
import logging
import secrets
from pydantic import EmailStr
from sqlmodel import delete, Session, select

from ..models.student import StudentInDB
from ..models.auth import AccessTokenData, ResetTokenInDB, RefreshTokenInDB, AccessRefreshToken, RefreshRequest
from ..core.settings import settings
from ..utils.validators import normalize_email
from ..utils.hash_reset_token import hash_reset_token
from ..exceptions.exceptions import InvalidResetTokenError, InvalidRefreshTokenError, DatabaseError


logger = logging.getLogger(__name__)
 # PasswordHash instance with Argon2 as hasher
pwd_hash = PasswordHash.recommended()


class AuthService():
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
    

    # -- VERIFY PASSWORD -- MATCH between PLAIN PWD (user input) and HASHED PWD saved in DB
    @staticmethod
    def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
        
        return pwd_hash.verify(plain_password, hashed_password)



    # -- GET_PASSWORD_HASH -- CREATE HASH of PLAIN PWD --
    @staticmethod
    def get_password_hash(password: str | bytes) -> str:
        
        return pwd_hash.hash(password)


    
    # -- CREATE ACCESS TOKEN -- create token with student id and expiration value
    @staticmethod
    def create_access_token(id: uuid.UUID, expires_delta: timedelta | None = None) -> str:
        
            # calculate expires_delta
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            
           # create id for jti claim (used for redis blacklist) 
            jti = str(uuid.uuid4()) 
            # 'payload' (1/3 JWT elements together with 'header' and 'signature') made of a "sub" claim (subject) with unique id + "exp" claim + "jti" claim
            payload = {
                "sub": str(id),
                "exp": expire,
                "jti": jti # JWT ID
            }
            # secret_key and algorithm taken from settings class that reads .env variables 
            encoded_jwt = jwt.encode(payload, settings.secret_key, settings.algorithm)
            
            logger.debug("Access token created")
            
            return encoded_jwt
        
        
    
    # -- VALIDATE ACCESS TOKEN -- decode access token & return STUDENT ID (TokenData)
    
    async def validate_access_token(self, token: str) -> AccessTokenData:
       
        try:
            logger.debug("Validating access token")
            # decode received token 
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            # extract "jti" claim
            jti = payload.get("jti")
            
            # check whether jti is redis blacklisted 
            if jti and await self.redis.get(f"blacklist:{jti}"):
                logger.warning("Access token revoked. Validation failed")
                raise jwt.InvalidTokenError("Token revoked")
            
            # extract "sub" claim (contains id)
            student_id = payload.get("sub")
            
            if student_id is None:
                logger.warning("Missing 'sub' claim. Invalid access token")
                raise jwt.InvalidTokenError("Missing student ID")
            
            logger.debug("Access token validated")
            # return TokenData object for better control
            return AccessTokenData(student_id=student_id)
    
          
        except jwt.PyJWTError: 
            logger.error("PyJWTError - check settings")
            raise
        
        except ValueError:
            logger.warning("Payload ValueError")
            raise jwt.InvalidTokenError("Invalid payload")
        
        
 
    # -- CREATE RESET TOKEN -- for password reset request
    @staticmethod
    def create_reset_token(
        email: EmailStr,
        session: Session
        ) -> str:
        
        # if exists, normalize it to avoid errors => e.g. abc@xyz.COM vs. abc@xyz.com
        normalized_email = normalize_email(email)
        # check whether email belongs to registered student => student_service.get_student_by_email(email) is not used to avoid circular import errors 
        student_in_db = session.exec(
            select(StudentInDB).where(StudentInDB.email == normalized_email)
        ).first()
        
        # if not, log the error internally and exit
        if not student_in_db:
            logger.warning("Email not found. Cannot create reset token")
            raise ValueError("Email not registered") # only within the app => intercepted by request_password_reset with 'pass' => no info to the client
        
        
        # with block => auto-commit + auto-rollback
        with session.begin(): 
            # delete any other already existing token
            delete_previuos_tokens = delete(ResetTokenInDB).where(ResetTokenInDB.email == normalized_email)
            session.exec(delete_previuos_tokens)
            # create new token
            raw_token = secrets.token_urlsafe(32)
            # hash token
            token_hash = hash_reset_token(raw_token)
            # create new ResetToken with hashed token linked to email
            reset_token = ResetTokenInDB(
                email=normalized_email,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
            )
            session.add(reset_token)
            
        logger.debug(f"Reset token created for email {normalized_email}")
    
        return raw_token
    
       
    
    # -- VALIDATE RESET TOKEN --
    @staticmethod
    def validate_reset_token(raw_reset_token: str, session: Session) -> ResetTokenInDB:
        
        # hash raw token
        reset_token_hash = hash_reset_token(raw_reset_token)
        
        with session.begin():
            # query to select valid reset token  from db
            check_token = select(ResetTokenInDB).where(
                ResetTokenInDB.token_hash == reset_token_hash,
                ResetTokenInDB.expires_at > datetime.now(timezone.utc)
            )
            # execute query => token | None
            db_valid_token: ResetTokenInDB | None = session.exec(check_token).first()
            
            if not db_valid_token:
                logger.warning("Invalid/expired reset token attempt")
                raise InvalidResetTokenError()
        
        return db_valid_token
        
       
    
    # -- CREATE REFRESH TOKEN --
    @staticmethod 
    def create_refresh_token(student_id: uuid.UUID, session: Session) -> str:
        
        # create raw token
        raw_refresh_token = str(uuid.uuid4())
        
        # create token hash 
        hashed_refresh_token = AuthService.get_password_hash(raw_refresh_token)
        
        # crete RefreshTokenInDB
        refresh_token_in_db = RefreshTokenInDB(
            student_id=student_id,
            token_hash=hashed_refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        )
        
        session.add(refresh_token_in_db) # session.commit() will be executed from the function that calls this method (e.g. login_for_access_token())
        
        logger.debug(f"Refresh token created for student {student_id}")
        
        return raw_refresh_token
        
        
    
    
    # -- VALIDATE REFRESH TOKEN -- -> token | None
    @staticmethod
    def validate_refresh_token(refresh_token: str, student_id: uuid.UUID, session: Session) -> RefreshTokenInDB | None:

        try:
            logger.info(f"Validating refresh token for student: {student_id}")

            # fetch all valid (non-revoked, non-expired) tokens for this student
            # Argon2 is salted/non-deterministic: can't hash and compare directly,
            # must retrieve candidates and verify with verify_password()
            check_token_validity = select(RefreshTokenInDB).where(
                RefreshTokenInDB.student_id == student_id,
                RefreshTokenInDB.revoked_at.is_(None),
                RefreshTokenInDB.expires_at > datetime.now(timezone.utc)
            )
            candidates: list[RefreshTokenInDB] = session.exec(check_token_validity).all()

            # find the token whose stored hash matches the raw token
            valid_token: RefreshTokenInDB | None = None
            for candidate in candidates:
                if AuthService.verify_password(refresh_token, candidate.token_hash):
                    valid_token = candidate
                    break

            if not valid_token:
                logger.warning(f"Token not found in DB: invalid/expired")
                return None

            logger.debug(f"Refresh token validated successfully for student {student_id}")

            return valid_token

        except (SQLAlchemyError, ValueError, TypeError) as e:
            logger.error(f"DB/hash error during refresh token validation for student {student_id}: {str(e)}")
            return None
    
    
    
    # -- REFRESH TOKEN ROTATION --
    @staticmethod
    def rotate_refresh_token(refresh_token: RefreshTokenInDB, session: Session) -> str:

        student_id = refresh_token.student_id

        try:
            # revoke current refresh_token
            refresh_token.revoked_at = datetime.now(timezone.utc)
            session.add(refresh_token)

            # create new refresh token (session.add() called inside, no commit)
            new_refresh_token = AuthService.create_refresh_token(student_id, session)

            # commit the already-open transaction (autobegin started by validate_refresh_token's SELECT)
            session.commit()

            logger.debug(f"Refresh token rotated for student {student_id}")

            return new_refresh_token

        except Exception as e:
            session.rollback()
            logger.error(f"Refresh token rotation failed for student {student_id}: {str(e)}")
            raise DatabaseError("Refresh token rotation failed")
    
    
    
    # -- REFRESH TOKENS -- /refresh endpoint function
    @staticmethod
    def refresh_tokens(refresh_token: str, student_id: uuid.UUID, session: Session) -> AccessRefreshToken:
        
        try:
            # validate received refresh token 
            valid_refresh_token: RefreshTokenInDB | None = AuthService.validate_refresh_token(refresh_token, student_id, session)
            
            if not valid_refresh_token:
                logger.warning(f"Invalid refresh token attempt for student {student_id}")
                raise InvalidRefreshTokenError()
            
            # rotate token (revoke old token + create new)
            new_refresh_token: str = AuthService.rotate_refresh_token(valid_refresh_token, session)
            
            # create new access token
            new_access_token = AuthService.create_access_token(
                student_id, 
                timedelta(minutes=settings.access_token_expire_minutes)
            )
            
            logger.info(f"Tokens refreshed successfully for student {student_id}")
            
            return AccessRefreshToken(access_token=new_access_token, token_type="Bearer", refresh_token=new_refresh_token)
        
        except (InvalidRefreshTokenError, DatabaseError):
            raise 
        
        except Exception as e:
            logger.error(f"Tokens refresh failed for student {student_id}: {str(e)}")
            raise DatabaseError("Failed to refresh tokens")
            
        
 
  
    
    
   
  