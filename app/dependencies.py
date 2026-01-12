import uuid
from app.services.auth import AuthService
from core.database import SessionDep
from .core.settings import settings
from .services.student import StudentService 
from .models.student import StudentPublic
from typing import Annotated
from fastapi import Depends, HTTPException, status
import jwt
from .services.course import CourseService



# -- STUDENT SERVICE DEPENDENCY --
def get_student_service(session: SessionDep):
    return StudentService(session=session)


# -- COURSE SERVICE DEPENDENCY --
def get_course_service(session: SessionDep):
    return CourseService(session=session)




# -- GET CURRENT STUDENT -- 
# recupera lo studente a partire da token validato
# => prescinde da is_active, restituiti studenti ATTIVI e INATTIVI
# => usata in /students/me (tutti gli studenti possono leggere le proprie info, ma solo quelli attivi le modificano)
async def get_current_student(
    token: Annotated[str, Depends(settings.oauth2_scheme)], 
    student_service: StudentService = Depends(get_student_service)
    ) -> StudentPublic:
    # valido il token e ricevo l'id estratto in TokenData
    access_token_data = await AuthService.validate_access_token(token)
    # converto l'id (che è una stringa) in UUID
    student_id = access_token_data.get_uuid()
    # ulteriore controllo (già presente in validate_access_token) per sicurezza
    if student_id is None:
        raise student_service.invalid_token_exception
    # controllo che ci sia uno studente con l'id estratto passando l'id convertito a UUID
    student = student_service.get_student_by_id(id=student_id) #  student = self.get_student_by_id(id=token_data.get_uuid())
    if student is None:
        raise student_service.invalid_token_exception
    # se sì, lo restituisco
    return student



# -- GET CURRENT ACTIVE USER  -- 
# recupera lo studente a partire dal token validato 
# aggiunge controllo per flag IS_ACTIVE => restituisce lo studente SOLO SE È ATTIVO
# dipendenza di tutti gli endpoint protetti (solo chi è attivo può modificare e compiere azioni nell'app)
async def get_current_active_student(current_student: Annotated[StudentPublic, Depends(get_current_student)]) -> StudentPublic:
    if not current_student.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user"
            )
    return current_student


# -- GET CURRENT USER ID with EXPIRED ACCESS TOKEN --
# usata in /auth/refresh per recuperare l'id studente anche se l'access token è scaduto 
def get_current_student_id_only(token: str = Depends(settings.oauth2_scheme)) -> uuid.UUID:
   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token, 
            settings.secret_key, 
            algorithms=[settings.algorithm],
            options={ "verify_exp": False}  # non controlla la scadenza del token
        )
        student_id_str: str = payload.get("sub")
        
        if student_id_str is None:
            raise credentials_exception
        
        return uuid.UUID(student_id_str)
    
    except:
        raise credentials_exception






