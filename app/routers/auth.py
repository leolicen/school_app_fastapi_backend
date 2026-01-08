from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from ..models.auth import AccessRefreshToken, ResetPasswordRequest, ResetPwdData
from ..dependencies import get_student_service
from ..services.student import StudentService
from ..models.student import StudentCreate
from ..core.rate_limiting import limiter


# definisco router /auth 
router = APIRouter(
    # il prefisso non ha '/' finale perché è incluso nei singoli endpoint
    prefix="/auth",
    tags=["auth"],
   
)

# -- LOGIN -- 
# endoint NON PROTETTO
@router.post("/login", response_model=AccessRefreshToken)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.login_for_access_token(form_data)


# -- REGISTRAZIONE -- (registrazione + login automatico)
# endpoint NON PROTETTO
@router.post("/register", response_model=AccessRefreshToken)
@limiter.limit("5/hour")
def register_student(
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.register_and_login(student)


# -- PASSWORD RESET REQUEST --
# endpoint NON PROTETTO
@router.post("/password/reset-request", response_model=dict[str, str])
@limiter.limit("5/15minute")
def request_password_reset(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.request_password_reset(request.email, background_tasks)
    


# -- PASSWORD RESET --
# endpoint NON PROTETTO
# riceve raw token e new_pwd dal form di reset password
@router.post("/password/reset-confirm", response_model=dict[str, str])
@limiter.limit("5/15minute")
def reset_password(
    reset_pwd_data: ResetPwdData, # unico body param che ingloba token e new_pwd
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.confirm_password_reset(reset_pwd_data.raw_reset_token, reset_pwd_data.new_pwd_data.new_pwd_confirm)