import logging
import uuid
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ..core.database import SessionDep
from ..models.auth import AccessRefreshToken
from ..models.password import ResetPasswordRequest, ResetPwdData
from ..dependencies import get_student_service, get_auth_service, get_current_user_id_only, get_user_service, get_tutor_service
from ..services.student import StudentService
from ..services.user import UserService
from ..services.tutor import TutorService
from ..models.student import StudentCreate
from ..models.tutor import TutorCreate
from ..core.rate_limiting import limiter
from ..services.auth import AuthService
from ..models.auth import RefreshRequest
from ..exceptions.exceptions import MissingRefreshTokenError


logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# define /auth router
router = APIRouter(
    # prefix does not contain final '/' because it is included in the endpoints
    prefix="/auth",
    tags=["auth"],
)


# public
@router.post("/login", response_model=AccessRefreshToken)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: UserService = Depends(get_user_service)
):
    return user_service.login_for_access_token(form_data)


# public (register + automatic login)
@router.post("/student/register", response_model=AccessRefreshToken)
@limiter.limit("5/hour")
def register_student(
    request: Request,
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.register_and_login(student)


# public (register + automatic login)
@router.post("/tutor/register", response_model=AccessRefreshToken)
@limiter.limit("5/hour")
def register_tutor(
    request: Request,
    tutor: TutorCreate,
    tutor_service: TutorService = Depends(get_tutor_service)
):
    return tutor_service.register_and_login(tutor)


# public
@router.post("/password/reset-request", response_model=dict[str, str])
@limiter.limit("5/15minute")
def request_password_reset(
    request: Request,
    reset_request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    user_service: UserService = Depends(get_user_service)
):
    return user_service.request_password_reset(reset_request.email, background_tasks)


# protected only with reset token
# receives raw token & new_pwd from reset password form
@router.post("/password/reset-confirm", response_model=dict[str, str])
@limiter.limit("5/15minute")
def reset_password(
    request: Request,
    reset_pwd_data: ResetPwdData,  # single body param with token & new_pwd
    user_service: UserService = Depends(get_user_service)
):
    return user_service.confirm_password_reset(reset_pwd_data.raw_reset_token, reset_pwd_data.new_pwd_data.new_pwd_confirm)


# protected (but no token expiry validation)
@router.post("/refresh", response_model=AccessRefreshToken)
@limiter.limit("5/minute")
def refresh_tokens(
    request: Request,
    refresh_request: RefreshRequest,
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id_only)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    session: SessionDep  # session: Annotated[Session, Depends(SessionDep)] => created args & kwargs issue
):
    if not refresh_request:
        logger.warning("Refresh token missing")
        raise MissingRefreshTokenError()

    return auth_service.refresh_tokens(refresh_request.refresh_token, user_id, session)


# protected 
@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id_only)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    access_token: Annotated[str, Depends(oauth2_scheme)]
):
    await user_service.logout(user_id, access_token)
    return {"detail": "User successfully logged out"}
