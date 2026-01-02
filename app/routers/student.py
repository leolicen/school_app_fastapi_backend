from fastapi import APIRouter, Depends
from ..models.student import StudentPublic, StudentUpdate
from typing import Annotated
from ..dependencies import get_current_student, get_current_active_student, get_student_service
from ..services.student import StudentService

# definisco router /auth 
router = APIRouter(
    # il prefisso non ha '/' finale perché è incluso nei singoli endpoint
    prefix="/students",
    tags=["students"],
)

# -- GET CURRENT STUDENT -- 
# endpoint PROTETTO
# dipende da GET_CURRENT_STUDENT => recupera info di QUALSIASI STUDENTE (ATTIVO e INATTIVO) => tutti possono leggere le proprie info
@router.get("/me", response_model=StudentPublic)
def get_current_student(current_student: Annotated[StudentPublic, Depends(get_current_student)]):
    return current_student


# -- UPDATE STUDENT --
# endpoint PROTETTO
# dipende da GET_CURRENT_ACTIVE_STUDENT => si deve essere studenti attivi per modificare i dati
@router.patch("/me", response_model=StudentPublic)
def update_student(
    current_student: Annotated[StudentPublic, Depends(get_current_active_student)],
    student_service: Annotated[StudentService, Depends(get_student_service)],
    student_to_update: StudentUpdate
    ):
    return student_service.update_student(current_student.student_id, student_to_update)


# DELETE_STUDENT

# CHANGE_PASSWORD