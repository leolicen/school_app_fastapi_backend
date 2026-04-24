import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash
from pydantic import EmailStr
import redis.asyncio as redis
from sqlalchemy import update
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import delete, Session, select

from ..models.student import StudentInDB
from ..models.auth import AccessTokenData, ResetTokenInDB, RefreshTokenInDB, AccessRefreshToken
from ..models.user import UserRole
from ..models.tutor import TutorInDB
from ..core.settings import settings
from ..utils.validators import normalize_email
from ..utils.hash_reset_token import hash_reset_token
from ..exceptions.exceptions import InvalidResetTokenError, InvalidRefreshTokenError, DatabaseError


logger = logging.getLogger(__name__)

# PasswordHash instance with Argon2 as hasher
pwd_hash = PasswordHash.recommended()


class AuthService():

    def __init__(self, redis_client: redis.Redis):
        """Initialize AuthService with a Redis client for access token blacklisting."""
        self.redis = redis_client


    @staticmethod
    def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
        """Match between plain password (user input) and hashed password saved in db."""
        return pwd_hash.verify(plain_password, hashed_password)


    @staticmethod
    def get_password_hash(password: str | bytes) -> str:
        """Create hash of plain password."""
        return pwd_hash.hash(password)


    @staticmethod
    def create_access_token(user_id: uuid.UUID, role: UserRole, expires_delta: timedelta | None = None) -> str:
        """Create access token with user id, role and expiration value."""
        # calculate expiration
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)

        # create id for jti claim (used for redis blacklist)
        jti = str(uuid.uuid4())
        # payload (1/3 JWT elements together with header and signature): "sub" claim (subject) + "role" + "exp" claim + "jti" claim
        payload = {
            "sub": str(user_id),
            "role": role.value,
            "exp": expire,
            "jti": jti  # JWT ID
        }
        # secret_key and algorithm taken from settings class that reads .env variables
        encoded_jwt = jwt.encode(payload, settings.secret_key, settings.algorithm)

        logger.debug("Access token created")

        return encoded_jwt


    async def validate_access_token(self, token: str) -> AccessTokenData:
        """Decode access token and return user id & role as AccessTokenData."""
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
            user_id = payload.get("sub")

            if user_id is None:
                logger.warning("Missing 'sub' claim. Invalid access token")
                raise jwt.InvalidTokenError("Missing user ID")
            
            # extract "role" claim
            role = payload.get("role")
            
            if role is None:
                logger.warning("Missing 'role' claim. Invalid access token")
                raise jwt.InvalidTokenError("Missing role")

            logger.debug("Access token validated")
            # return TokenData object for better control
            return AccessTokenData(user_id=user_id, role=role)

        except jwt.PyJWTError:
            logger.warning("PyJWTError - Access token validation failed")
            raise

        except ValueError:
            logger.warning("Payload ValueError")
            raise jwt.InvalidTokenError("Invalid payload")
    
    
    @staticmethod
    def _resolve_user_role_by_email(email: str, session: Session) -> UserRole:
        """Return UserRole for a given normalized email, or raise ValueError."""
        
        if session.exec(select(StudentInDB).where(StudentInDB.email == email)).first():
            return UserRole.STUDENT
        
        if session.exec(select(TutorInDB).where(TutorInDB.email == email)).first():
            return UserRole.TUTOR
        
        raise ValueError("Email not registered") # intercepted by request_password_reset with 'pass' => no info leaked to client


    @staticmethod
    def create_reset_token(email: EmailStr, session: Session) -> str:
        """Create a one-time reset token linked to the given email."""
        # if exists, normalize it to avoid errors (e.g. abc@xyz.COM vs. abc@xyz.com)
        normalized_email = normalize_email(email)
        
        # retrieve user role from email if user exists
        user_role = AuthService._resolve_user_role_by_email(email=normalized_email, session=session)

        # delete any already existing token
        delete_previous_tokens = delete(ResetTokenInDB).where(ResetTokenInDB.email == normalized_email)
        session.exec(delete_previous_tokens)
        # create new raw token
        raw_token = secrets.token_urlsafe(32)
        # hash token
        token_hash = hash_reset_token(raw_token)
        # create new ResetToken with hashed token linked to email
        reset_token = ResetTokenInDB(
            email=normalized_email,
            role=user_role,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(reset_token)

        logger.debug(f"Reset token created for email {normalized_email}")

        return raw_token


    @staticmethod
    def validate_reset_token(raw_reset_token: str, session: Session) -> ResetTokenInDB:
        """Hash the raw token and look it up in the DB. Raises InvalidResetTokenError if not found or expired."""
        # hash raw token
        reset_token_hash = hash_reset_token(raw_reset_token)

        # query to select valid reset token from db
        check_token = select(ResetTokenInDB).where(
            ResetTokenInDB.token_hash == reset_token_hash,
            ResetTokenInDB.expires_at > datetime.now(timezone.utc)
        )
        # execute query => token | None
        db_valid_token: ResetTokenInDB | None = session.exec(check_token).first()

        if not db_valid_token:
            logger.warning("Invalid/expired reset token attempt")
            raise InvalidResetTokenError()

        return db_valid_token


    @staticmethod
    def create_refresh_token(user_id: uuid.UUID, role: UserRole, session: Session) -> str:
        """Create and persist a new refresh token for the given user. Returns the raw (unhashed) token."""
        # create raw token
        raw_refresh_token = str(uuid.uuid4())

        # create token hash
        hashed_refresh_token = AuthService.get_password_hash(raw_refresh_token)

        # create RefreshTokenInDB
        refresh_token_in_db = RefreshTokenInDB(
            user_id=user_id,
            role=role,
            token_hash=hashed_refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
        )

        session.add(refresh_token_in_db)

        logger.debug(f"Refresh token created for user {user_id}")

        return raw_refresh_token


    @staticmethod
    def validate_refresh_token(refresh_token: str, user_id: uuid.UUID, session: Session) -> RefreshTokenInDB | None:
        """Returns a valid RefreshTokenInDB or None."""
        try:
            logger.info(f"Validating refresh token for user: {user_id}")

            # fetch all valid (non-revoked, non-expired) tokens for this user
            # Argon2 is salted/non-deterministic: can't hash and compare directly,
            # must retrieve candidates and verify with verify_password()
            check_token_validity = select(RefreshTokenInDB).where(
                RefreshTokenInDB.user_id == user_id,
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
                logger.warning("Token not found in DB: invalid/expired")
                return None

            logger.debug(f"Refresh token validated successfully for user {user_id}")

            return valid_token

        except (SQLAlchemyError, ValueError, TypeError) as e:
            logger.error(f"DB/hash error during refresh token validation for user {user_id}: {str(e)}")
            return None


    @staticmethod
    def rotate_refresh_token(refresh_token: RefreshTokenInDB, session: Session) -> str:
        """Revoke the current refresh token and issue a new one. Returns the new raw token."""
        user_id = refresh_token.user_id
        role = refresh_token.role

        try:
            # revoke current refresh token
            refresh_token.revoked_at = datetime.now(timezone.utc)
            session.add(refresh_token)

            # create new refresh token (session.add() called inside, no commit)
            new_refresh_token = AuthService.create_refresh_token(user_id=user_id, role=role, session=session)

            logger.debug(f"Refresh token rotated for user {user_id}")

            return new_refresh_token

        except Exception as e:
            session.rollback()
            logger.error(f"Refresh token rotation failed for user {user_id}: {str(e)}")
            raise DatabaseError("Refresh token rotation failed")


    @staticmethod
    def refresh_tokens(refresh_token: str, user_id: uuid.UUID, session: Session) -> AccessRefreshToken:
        """Validate, rotate and reissue both tokens. Called by the /refresh endpoint."""
        try:
            # validate received refresh token
            valid_refresh_token: RefreshTokenInDB | None = AuthService.validate_refresh_token(refresh_token, user_id, session)

            if not valid_refresh_token:
                logger.warning(f"Invalid refresh token attempt for user {user_id}")
                raise InvalidRefreshTokenError()

            # rotate token (revoke old token + create new)
            new_refresh_token: str = AuthService.rotate_refresh_token(valid_refresh_token, session)

            # create new access token
            new_access_token = AuthService.create_access_token(
                user_id=user_id,
                role=valid_refresh_token.role,
                expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
            )

            logger.info(f"Tokens refreshed successfully for user {user_id}")

            return AccessRefreshToken(access_token=new_access_token, token_type="Bearer", refresh_token=new_refresh_token)

        except (InvalidRefreshTokenError, DatabaseError):
            raise

        except Exception as e:
            logger.error(f"Tokens refresh failed for user {user_id}: {str(e)}")
            raise DatabaseError("Failed to refresh tokens")
        
    
    @staticmethod
    def revoke_refresh_token(user_id: uuid.UUID, session: Session) -> int:
        """Revoke active refresh tokens for this user. Used only during logout."""
        try:
            # query to update refresh token "revoked_at" field
            revoke_refresh_token = update(RefreshTokenInDB).where(
                RefreshTokenInDB.user_id == user_id,
                RefreshTokenInDB.revoked_at.is_(None),
                RefreshTokenInDB.expires_at > datetime.now(timezone.utc)
            ).values(revoked_at=datetime.now(timezone.utc))

            result = session.exec(revoke_refresh_token)

            rowcount = result.rowcount

            if rowcount == 0:
                logger.debug(f"No active refresh token for user {user_id}")
            else:
                logger.info(f"Revoked {rowcount} refresh token(s) for user {user_id}")

            return rowcount

        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Failed to revoke refresh tokens for {user_id}: {str(e)}")
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
