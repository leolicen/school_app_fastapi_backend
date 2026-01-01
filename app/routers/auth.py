from fastapi import APIRouter, Depends
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from ..models.token import Token
from ..dependencies import get_student_service
from ..services.student import StudentService
from ..models.student import StudentCreate


# definisco router /auth PUBBLICO
router = APIRouter(
    # il prefisso non ha '/' finale perché è incluso nei singoli endpoint
    prefix="/auth",
    tags=["auth"],
   
)

# -- endpoint LOGIN studenti -- 
@router.post("/login", response_model=Token)
def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.login_for_access_token(form_data)

# -- endpoint REGISTRAZIONE studenti -- registrazione + login automatico
@router.post("/register", response_model=Token)
def register_student(
    student: StudentCreate,
    student_service: StudentService = Depends(get_student_service)
    ):
    return student_service.register_and_login(student)


