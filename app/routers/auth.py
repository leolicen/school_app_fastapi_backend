from fastapi import APIRouter, Depends
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
from ..models.token import Token
from ..dependencies import get_auth_service
from ..services.auth import AuthService
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
    auth_service: AuthService = Depends(get_auth_service)
    ):
    return auth_service.login_for_access_token(form_data)

# -- endpoint REGISTRAZIONE studenti --
@router.post("/register", response_model=Token)
def register_student(
    student: StudentCreate,
    auth_service: AuthService = Depends(get_auth_service)
    ):
    return auth_service.register_and_login(student)


