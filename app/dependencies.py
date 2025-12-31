from core.database import SessionDep
from .core.settings import settings
from .services.student import StudentService 
from .models.student import StudentPublic
from typing import Annotated
from fastapi import Depends, HTTPException


# -- STUDENT SERVICE DEPENDENCY --
def get_student_service(session: SessionDep):
    return StudentService(session=session)



 # --  GET CURRENT ACTIVE USER DEPENDENCY -- dipendenza che autentica tramite token l'utente nei singoli endpoint protetti
 # (aggiunge controllo per flag is_active => restituisce lo studente SOLO SE È ATTIVO)
async def get_current_active_student(
    token: Annotated[str, Depends(settings.oauth2_scheme)],
    student_service: StudentService = Depends(get_student_service)
    ) -> StudentPublic:
    current_student = student_service.get_current_student(token)
    if not current_student.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive user"
            )
    return current_student





