from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer

from ..models.student import StudentPublic, StudentUpdate
from ..dependencies import get_current_student, get_current_active_student, get_student_service
from ..services.student import StudentService
from ..models.password import ChangePassword


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# define /auth router
router = APIRouter(
    prefix="/students",
    tags=["students"],
)

# -- GET CURRENT STUDENT -- 
# PROTECTED
# depends from GET_CURRENT_STUDENT => retrieves info of ANY STUDENT (ACTIVE & INACTIVE) => anybody can read their own info
@router.get("/me", response_model=StudentPublic)
def get_current_student(current_student: Annotated[StudentPublic, Depends(get_current_student)]):
    return current_student


# -- UPDATE STUDENT --
# PROTECTED
# depends from GET_CURRENT_ACTIVE_STUDENT => student must be active to modify data
@router.patch("/me", response_model=StudentPublic)
def update_student(
    current_student: Annotated[StudentPublic, Depends(get_current_active_student)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    student_to_update: StudentUpdate
    ):
    return student_service.update_student(current_student.student_id, student_to_update)



# DELETE_STUDENT
# PROTECTED
# depends from GET_CURRENT_STUDENT => ANY STUDENT can delete their account
@router.delete("/me", response_model=dict[str, str])
async def delete_account(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    access_token: Annotated[str, Depends(oauth2_scheme)]
):
    return await student_service.delete_student(current_student, access_token)



# -- CHANGE_PASSWORD -- (within the app => student account)
# PROTECTED
# depends from GET_CURRENT_STUDENT => ANY STUDENT (active & non-) => anybody can read their own info ("/me") and modify password to access the app
@router.post("/change-password", status_code=status.HTTP_200_OK, response_model=dict[str, str])
def change_password(
    current_student: Annotated[StudentPublic, Depends(get_current_student)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    pwd_data: ChangePassword
):
    student_service.change_password(current_student,pwd_data)
    
    return {"detail": "Password updated successfully"}

