from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from ..models.auth import Token, ResetPasswordRequest
from ..dependencies import get_current_student, get_student_service
from ..services.student import StudentService
from ..models.student import StudentCreate


# definisco router /auth 
router = APIRouter(
    # il prefisso non ha '/' finale perché è incluso nei singoli endpoint
    prefix="/auth",
    tags=["auth"],
   
)

# -- LOGIN studenti -- 
# endoint PUBBLICO
@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.login_for_access_token(form_data)

# -- REGISTRAZIONE studenti -- registrazione + login automatico
# endpoint PUBBLICO
@router.post("/register", response_model=Token)
def register_student(
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.register_and_login(student)


# -- PASSWORD RESET REQUEST --
@router.post("/password/reset-request", response_model=dict[str, str])
def request_password_reset(
    request: ResetPasswordRequest,
    background_tasks: BackgroundTasks,
    student_service: StudentService = Depends(get_student_service)
):
    return student_service.request_password_reset(request.email, background_tasks)
    






# -- PASSWORD RESET --
@router.post("/password/reset")
def reset_password():
    pass