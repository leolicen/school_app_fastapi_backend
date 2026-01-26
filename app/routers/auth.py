import uuid
from fastapi import APIRouter, Cookie, Depends, BackgroundTasks, status
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from app.core import settings
from ..models.auth import AccessRefreshToken, ResetPasswordRequest, ResetPwdData
from ..dependencies import get_student_service, get_current_student_id_only
from ..services.student import StudentService
from ..models.student import StudentCreate
from ..core.rate_limiting import limiter
from core.database import SessionDep
from ..services.auth import AuthService
import logging
from ..exceptions.exceptions import MissingRefreshTokenError


logger = logging.getLogger(__name__)



# define /auth router
router = APIRouter(
    # prefix does not contain final '/'  because it is included in the endpoints
    prefix="/auth",
    tags=["auth"],
   
)

# -- LOGIN -- 
# PUBLIC
@router.post("/login", response_model=AccessRefreshToken)
@limiter.limit("10/minute")
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.login_for_access_token(form_data)



# -- REGISTER STUDENT -- (register + automatic login)
# PUBLIC
@router.post("/register", response_model=AccessRefreshToken)
@limiter.limit("5/hour")
def register_student(
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.register_and_login(student)


# -- REQUEST PASSWORD RESET --
# PUBLIC
@router.post("/password/reset-request", response_model=dict[str, str])
@limiter.limit("5/15minute")
def request_password_reset(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.request_password_reset(request.email, background_tasks)
    


# -- RESET PASSWORD --
# PROTECTED (?)
# receives raw token & new_pwd from reset password form
@router.post("/password/reset-confirm", response_model=dict[str, str])
@limiter.limit("5/15minute")
def reset_password(
    reset_pwd_data: ResetPwdData, # single body param with token & new_pwd
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.confirm_password_reset(reset_pwd_data.raw_reset_token, reset_pwd_data.new_pwd_data.new_pwd_confirm)



# -- REFRESH TOKENS --
# PROTECTED (?)
@router.post("/refresh", response_model=AccessRefreshToken)
@limiter.limit("5/minute")
def refresh_tokens(
    student_id: Annotated[uuid.UUID, Depends(get_current_student_id_only)],
    session: Annotated[Session, Depends(SessionDep)],
    refresh_token: Annotated[str | None, Cookie()] = None # Cookie is a HTTP header
):
    
    if not refresh_token:
        logger.warning("Refresh token missing")
        raise MissingRefreshTokenError()
        
    return AuthService.refresh_tokens(refresh_token, student_id, session)


# -- LOGOUT --
# PROTECTED (?)
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    student_id: Annotated[uuid.UUID, Depends(get_current_student_id_only)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    access_token: Annotated[str, Depends(settings.oauth2_scheme)]
):
    await student_service.logout(student_id, access_token)