from sqlmodel import Session
from .auth import AuthService
from ..models.student import StudentCreate, StudentPublic, Student
from fastapi import HTTPException


class StudentService():
    def __init__(self, session: Session, auth_service: AuthService):
        self._db = session
        self._auth_service = auth_service
        
    # -- funzione REGISTRAZIONE STUDENTE -- crea un nuovo studente
    def register_student(self, student: StudentCreate) -> StudentPublic:
        try:
            # controllo che non esista già un account con l'email fornita
            if self._auth_service.get_student_by_email(student.email):
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            
            # se non esiste già un account, procedo a hashare la password fornita 
            hashed_password = self._auth_service.get_password_hash(student.password)
            
            # creo un nuovo studente di tipo Student(modello DB)
            # con model_dump creo un dizionario con i campi della variabile student: StudentCreate
            # '**' snocciola le chiavi del dizionario in singole proprietà
            # 'exclude' permette di escludere dal dizionario il campo "password" che contiene la password in chiaro (sostituita poi da quella hashata)
            new_student = Student(
                **student.model_dump(exclude={"password"}),
                hashed_password=hashed_password
            )
            # aggiungo il nuovo studente al DB
            self._db.add(new_student)
            self._db.commit()
            self._db.refresh(new_student)
            
            # converto lo studente di tipo Student (modello DB) in StudentPublic (modello response utente senza hashed_password)
            return StudentPublic.model_validate(new_student)
            
            
        except HTTPException:
            raise
        except Exception:
            self._db.rollback()
            raise HTTPException(
                status_code=500,
                detail="Internal Server Error"
            )