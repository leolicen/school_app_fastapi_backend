import uuid
from fastapi.security import OAuth2PasswordBearer
import jwt
import logging
from typing import Annotated
from fastapi import Depends
from jwt import InvalidTokenError

from app.services.auth import AuthService
from .core.database import SessionDep
from .core.settings import settings
from .services.student import StudentService 
from .models.student import StudentPublic
from .services.course import CourseService
from .services.internship import InternshipService
from .exceptions.exceptions import InactiveStudentError
from .services.auth import AuthService
from .core.redis import RedisDep


logger = logging.getLogger(__name__)

   
# define OAuth2PasswordBearer instance that requests endpoint url that returns the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# -- AUTH SERVICE DEPENDENCY --
def get_auth_service(redis_client: RedisDep):
    return AuthService(redis_client=redis_client)


# -- STUDENT SERVICE DEPENDENCY --
def get_student_service(
    session: SessionDep, 
    auth_service: Annotated[AuthService, Depends(get_auth_service)], # auth service injected as dependency 
    redis_client: RedisDep
    ):
    
    return StudentService(session=session, auth_service=auth_service, redis_client=redis_client) # auth service already available within student service injected in the endpoints


# -- COURSE SERVICE DEPENDENCY --
def get_course_service(session: SessionDep):
    return CourseService(session=session)


# -- INTERNSHIP SERVICE DEPENDENCY --
def get_internship_service(session: SessionDep):
    return InternshipService(session=session)




# -- GET CURRENT STUDENT -- 
# retrieves student from validated token 
# => does not check is_active flag, returns ACTIVE & INACTIVE students
# => e.g. used in /students/me (all students can read their info, but only active ones can modify them)
async def get_current_student(
    token: Annotated[str, Depends(oauth2_scheme)], 
    student_service: Annotated[StudentService, Depends(get_student_service)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
    ) -> StudentPublic:
    
    # validate token and put retrieved id in TokenData
    access_token_data = await auth_service.validate_access_token(token)
    # convert id from string to UUID
    student_id = access_token_data.get_uuid()
    
    # check if there is a student with the extracted id  
    student = student_service.get_student_by_id(id=student_id) #  student = self.get_student_by_id(id=token_data.get_uuid())
    
    if student is None:
        logger.error(f"Valid access token but student {student_id} not found in DB")
        raise InvalidTokenError("Valid token references non-existent user")

    logger.debug(f"Student {student.student_id} authorized")
   
    return student



# -- GET CURRENT ACTIVE USER  -- 
# retrieves student from validated token 
# adds IS_ACTIVE check => returns only ACTIVE students
# dependency for all protected endpoints (only active students can modify data and perform operations within the app)
async def get_current_active_student(current_student: Annotated[StudentPublic, Depends(get_current_student)]) -> StudentPublic:
    
    if not current_student.is_active:
        logger.warning(f"Inactive student access attempt: {current_student.student_id}")
        raise InactiveStudentError()
    
    logger.debug(f"Active student {current_student.student_id} authorized")    
    
    return current_student


# -- GET CURRENT USER ID ONLY -- (with EXPIRED ACCESS TOKEN) --
# used in /auth/refresh to retrieve student id even with an expired access token  
def get_current_student_id_only(token: str = Depends(oauth2_scheme)) -> uuid.UUID:
    
    try:
        
        logger.debug("Extracting student ID for refresh")
        
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm],
            options={ "verify_exp": False}  # does not check token expiration
        )
        
        student_id_str: str = payload.get("sub")
        
        if student_id_str is None:
            logger.warning(f"Missing 'sub' claim")
            raise InvalidTokenError("Missing subject in access token")
        
        logger.debug(f"Student ID extracted. Authorized to refresh token")
        
        return uuid.UUID(student_id_str)
    
    except (jwt.PyJWTError, ValueError):
        logger.warning("Access token decode failed")
        raise InvalidTokenError("Invalid access token for refresh")






