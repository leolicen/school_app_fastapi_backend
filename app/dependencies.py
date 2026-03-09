import logging
import uuid
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt import InvalidTokenError

from .core.database import SessionDep
from .core.redis import RedisDep
from .core.settings import settings
from .exceptions.exceptions import InactiveStudentError
from .models.student import StudentPublic
from .services.auth import AuthService
from .services.course import CourseService
from .services.internship import InternshipService
from .services.student import StudentService


logger = logging.getLogger(__name__)

# define OAuth2PasswordBearer instance that requests the token endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# -- AUTH SERVICE DEPENDENCY --
def get_auth_service(redis_client: RedisDep):
    """Provide an AuthService instance with a Redis client."""
    return AuthService(redis_client=redis_client)


# -- STUDENT SERVICE DEPENDENCY --
def get_student_service(
    session: SessionDep,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    redis_client: RedisDep
):
    """Provide a StudentService instance with DB session, auth service, and Redis client."""
    return StudentService(session=session, auth_service=auth_service, redis_client=redis_client)


# -- COURSE SERVICE DEPENDENCY --
def get_course_service(session: SessionDep):
    """Provide a CourseService instance with a DB session."""
    return CourseService(session=session)


# -- INTERNSHIP SERVICE DEPENDENCY --
def get_internship_service(session: SessionDep):
    """Provide an InternshipService instance with a DB session."""
    return InternshipService(session=session)


# -- GET CURRENT STUDENT --
async def get_current_student(
    token: Annotated[str, Depends(oauth2_scheme)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> StudentPublic:
    """Validate the access token and return the corresponding student (active or inactive).
    
    E.g. used in /students/me (all students can read their info, but only active ones can modify it)
    """
    access_token_data = await auth_service.validate_access_token(token)
    student_id = access_token_data.get_uuid()

    student = student_service.get_student_by_id(id=student_id)

    if student is None:
        logger.error(f"Valid access token but student {student_id} not found in DB")
        raise InvalidTokenError("Valid token references non-existent user")

    logger.debug(f"Student {student.student_id} authorized")

    return student


# -- GET CURRENT ACTIVE STUDENT --
async def get_current_active_student(
    current_student: Annotated[StudentPublic, Depends(get_current_student)]
) -> StudentPublic:
    """Validate that the authenticated student is active.
    
    Dependency for all protected endpoints (only active students can perform operations within the app).
    """
    if not current_student.is_active:
        logger.warning(f"Inactive student access attempt: {current_student.student_id}")
        raise InactiveStudentError()

    logger.debug(f"Active student {current_student.student_id} authorized")

    return current_student


# -- GET CURRENT STUDENT ID ONLY (with EXPIRED ACCESS TOKEN) --
def get_current_student_id_only(
    token: str = Depends(oauth2_scheme)
) -> uuid.UUID:
    """Extract the student UUID from a token without validating expiration.
    
    Used in /auth/refresh to retrieve the student id even with an expired access token.
    """
    try:
        logger.debug("Extracting student ID for refresh")

        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
            options={"verify_exp": False}  # skip expiration check
        )

        student_id_str: str = payload.get("sub")

        if student_id_str is None:
            logger.warning("Missing 'sub' claim")
            raise InvalidTokenError("Missing subject in access token")

        logger.debug("Student ID extracted. Authorized to refresh token")

        return uuid.UUID(student_id_str)

    except (jwt.PyJWTError, ValueError):
        logger.warning("Access token decode failed")
        raise InvalidTokenError("Invalid access token for refresh")
