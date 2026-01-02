import uuid
from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlmodel import Session, select
from app.core import settings
from ..models.student import StudentCreate, StudentPublic, StudentInDB, StudentUpdate
from .auth import AuthService
from ..models.token import Token



class StudentService():
    def __init__(self, session: Session): 
        self._db = session
        # creo HTTP exception in caso di errore di validazione token
        self.invalid_token_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        
    
    # --  GET STUDENT BY EMAIL -- 
    # verifica l'esistenza di un utente tramite email
    # restituisce Student (tabella) perché authenticate_student() ha bisogno di accedere al campo hashed_password
    def get_student_by_email(self, email: EmailStr) -> StudentInDB | None:
        return self._db.exec(
            select(StudentInDB).where(StudentInDB.email == email)
        ).first()
        # first() restituisce già None se non trova nulla
        
    # --  GET STUDENT BY ID -- 
    # verifica l'esistenza di un utente tramite id
    # restituisce StudentPublic perché in get_current_student, dove è usata, non serve e non è sicuro accedere a hashed_password
    # probabilmente si potrebbe sostituire con _db.get(Student, id) perché id è chiave primaria di Student
    def get_student_by_id(self, id: uuid.UUID) -> StudentPublic | None:
        student = self._db.exec(
            select(StudentInDB).where(StudentInDB.student_id == id)
        ).first()
        
        return StudentPublic.model_validate(student)
        
        
    # --  AUTENTICAZIONE STUDENTE -- 
    # in fase di LOGIN
    # restituisce StudentInDB (tabella) perché dentro la funzione serve accedere a hashed_password e in login, dove verrà chiamata, verrà restituito solo il Token
    def authenticate_student(self, email: EmailStr, password: str) -> StudentInDB | False:
        student = self.get_student_by_email(email)
        if not student:
            return False 
        if not AuthService.verify_password(password, student.hashed_password):
            return False
        return student
    
      
    # --  LOGIN -- 
    # login valido per studenti ATTIVI E INATTIVI (accesso alla app), i singoli endpoint controlleranno invece che sia anche attivo
    def login_for_access_token(self, form_data: OAuth2PasswordRequestForm) -> Token:
        # autentico lo studente tramite email e password
        student = self.authenticate_student(form_data.username, form_data.password)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # se è presente uno studente con quelle credenziali, creo un token con il suo id
        access_token = AuthService.create_access_token(student.student_id, settings.access_token_expire_minutes)
        
        return Token(access_token=access_token, token_type="bearer")
    
    
    
    
     # -- REGISTRAZIONE STUDENTE -- 
     # crea un nuovo studente
    def register_student(self, student: StudentCreate) -> StudentPublic:
        try:
            # controllo che non esista già un account con l'email fornita
            if self.get_student_by_email(student.email):
                raise HTTPException(
                    status_code=400,
                    detail="Email already registered"
                )
            
            # se non esiste già un account, procedo a hashare la password fornita 
            hashed_password = AuthService.get_password_hash(student.password)
            
            # creo un nuovo studente di tipo Student(modello DB)
            # con model_dump creo un dizionario con i campi della variabile student: StudentCreate
            # '**' snocciola le chiavi del dizionario in singole proprietà
            # 'exclude' permette di escludere dal dizionario il campo "password" che contiene la password in chiaro (sostituita poi da quella hashata)
            new_student = StudentInDB(
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
            
              
    # -- REGISTRAZIONE & LOGIN --
    def register_and_login(self, student: StudentCreate) -> Token:
        # creo un nuovo studente
        new_student = self.register_student(student)
        # creo istanza OAuth2PasswordRequestForm 
        form_data = OAuth2PasswordRequestForm(
            # email nuovo studente
            username=new_student.email,
            # password in chiaro prima dell'hashing
            password=student.password
        )
        # restituisco token per accesso
        return self.login_for_access_token(form_data)
    
    
    # -- AGGIORNA STUDENTE --
    def update_student(self, current_student_id: uuid.UUID, student_to_update: StudentUpdate) -> StudentPublic:
        # estraggo lo studente da aggiornare dal db
        student_in_db = self._db.get(StudentInDB, current_student_id)
        if not student_in_db:
            raise HTTPException(status_code=404, detail="Student not found")
        # dumpo le info aggiornate
        updated_info = student_to_update.model_dump(exclude_unset=True)
        # aggiorno lo studente in db con le info aggiornate
        student_in_db.sqlmodel_update(updated_info)
        self._db.add(student_in_db)
        self._db.commit()
        self._db.refresh(student_in_db)
        
        return StudentPublic.model_validate(student_in_db)