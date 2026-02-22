import uuid
import logging
from fastapi import APIRouter, Depends, BackgroundTasks, Request, status
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from ..core.database import SessionDep
from ..models.auth import AccessRefreshToken
from ..models.password import ResetPasswordRequest, ResetPwdData
from ..dependencies import get_student_service, get_auth_service, get_current_student_id_only
from ..services.student import StudentService
from ..models.student import StudentCreate
from ..core.rate_limiting import limiter
from ..services.auth import AuthService
from ..models.auth import RefreshRequest

from ..exceptions.exceptions import MissingRefreshTokenError


logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")



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
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.login_for_access_token(form_data)



# -- REGISTER STUDENT -- (register + automatic login)
# PUBLIC
@router.post("/register", response_model=AccessRefreshToken)
@limiter.limit("5/hour")
def register_student(
    request: Request,
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.register_and_login(student)



# -- REQUEST PASSWORD RESET --
# PUBLIC
@router.post("/password/reset-request", response_model=dict[str, str])
@limiter.limit("5/15minute")
def request_password_reset(
    request: Request,
    reset_request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.request_password_reset(reset_request.email, background_tasks)
    


# -- RESET PASSWORD --
# PROTECTED (?)
# receives raw token & new_pwd from reset password form
@router.post("/password/reset-confirm", response_model=dict[str, str])
@limiter.limit("5/15minute")
def reset_password(
    request: Request,
    reset_pwd_data: ResetPwdData, # single body param with token & new_pwd
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.confirm_password_reset(reset_pwd_data.raw_reset_token, reset_pwd_data.new_pwd_data.new_pwd_confirm)



# @limiter.limit("5/minute")
# -- REFRESH TOKENS --
# PROTECTED (?)
@router.post("/refresh", response_model=AccessRefreshToken)
def refresh_tokens(
    refresh_request: RefreshRequest,
    student_id: Annotated[uuid.UUID, Depends(get_current_student_id_only)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session: SessionDep # session: Annotated[Session, Depends(SessionDep)] => created args & kwargs issue 
):
    
    if not refresh_request:
        logger.warning("Refresh token missing")
        raise MissingRefreshTokenError()
        
    return auth_service.refresh_tokens(refresh_request.refresh_token, student_id, session)


# -- LOGOUT --
# PROTECTED (?)
@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    student_id: Annotated[uuid.UUID, Depends(get_current_student_id_only)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    access_token: Annotated[str, Depends(oauth2_scheme)]
):
    await student_service.logout(student_id, access_token)