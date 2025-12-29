from datetime import datetime, timedelta, timezone
from typing import Annotated
from pwdlib import PasswordHash
from pydantic import EmailStr
from sqlmodel import Session, select
from ..models.student import Student, StudentPublic
import uuid
from ..models.token import TokenData, Token
import jwt
from ..core.settings import settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

class AuthService():
    def __init__(self, session: Session):
        self._db = session
        # istanza di PasswordHash con Argon2 come hasher
        self._pwd_hash = PasswordHash.recommended()
       
    

    # metodo di MATCH tra PWD IN CHIARO (input utente) e PWD HASHATA salvata nel DB
    def verify_password(self, plain_password: str | bytes, hashed_password: str | bytes) -> bool:
        return self._pwd_hash.verify(plain_password, hashed_password)

    # metodo per CREARE HASH di una PWD IN CHIARO
    def get_password_hash(self, password: str | bytes) -> str:
        return self.pwd_hash.hash(password)


    # -- metodo GET STUDENT BY EMAIL -- verifica l'esistenza di un utente tramite email
    # restituisce Student (tabella) perché authenticate_student ha bisogno di accedere al campo hashed_password
    def get_student_by_email(self, email: EmailStr) -> Student | None:
        return self._db.exec(
            select(Student).where(Student.email == email)
        ).first()
        # first() restituisce già None se non trova nulla
        
    # -- metodo GET STUDENT BY ID -- verifica l'esistenza di un utente tramite id
    # restituisce StudentPublic perché in get_current_student, dove è usata, non serve e non è sicuro accedere a hashed_password
    def get_student_by_id(self, id: uuid.UUID) -> StudentPublic | None:
        return self._db.exec(
            select(Student).where(Student.student_id == id)
        ).first()
       
       
    # -- funzione AUTENTICAZIONE STUDENTE -- in fase di LOGIN
    # restituisce Student (tabella) perché dentro la funzione serve accedere a hashed_password e in login, dove verrà chiamata, verrà restituito solo il Token
    def authenticate_student(self, email: EmailStr, password: str) -> Student | False:
        student = self.get_student_by_email(email)
        if not student:
            return False 
        if not self.verify_password(password, student.hashed_password):
            return False
        return student
    
    # -- funzione CREAZIONE TOKEN -- crea token con id studente e valore exp
    def create_access_token(id: uuid.UUID, expires_delta: timedelta | None = None) -> str:
            # calcolo expires_delta
            if expires_delta:
                expire = datetime.now(timezone.utc) + expires_delta
            else:
                expire = datetime.now(timezone.utc) + timedelta(minutes=15)
            # payload (1/3 elementi del JWT con header e signature) formato da claim "sub" (subject) con valore id univoco + claim "exp"
            payload = {
                "sub": str(id),
                "exp": expire
            }
            # secret_key e algorithm presi da classe settings che legge variabili d'ambiente da .env
            encoded_jwt = jwt.encode(payload, settings.secret_key, settings.algorithm)
            
            return encoded_jwt
    
    
    # -- funzione GET CURRENT STUDENT -- recupera lo studente a partire dal token => dipendenza iniettata in ogni endpoint
    # si usa ASYNC perché lo richiede la dependency injection
    async def get_current_student(self, token: Annotated[str, Depends(oauth2_scheme)]) -> StudentPublic:
        # creo HTTP exception in caso di errore di validazione token
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )
        try:
            # decodifico il token ricevuto
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            # estraggo il claim "sub" (contenente l'id)
            student_id = payload.get("sub")
            if student_id is None:
                raise credentials_exception
            # creo un oggetto TokenData per maggior controllo
            token_data = TokenData(user_id=student_id)
        except (jwt.PyJWTError, ValueError):
            raise credentials_exception
        # controllo che ci sia uno studente con l'id estratto
        student = self.get_student_by_id(id=token_data.user_id)
        if student is None:
            raise credentials_exception
        # se sì, lo restituisco
        return student
    
    # -- funzione GET CURRENT ACTIVE USER -- aggiunge controllo per flag is_active => restituisce lo studente SOLO SE È ATTIVO
    async def get_current_active_student(current_student: Annotated[StudentPublic, Depends(get_current_student)]) -> StudentPublic:
        if not current_student.is_active:
            raise HTTPException(
                status_code=400,
                detail="Inactive user"
            )
        return current_student
    
    
    # -- funzione LOGIN -- login valido per studenti ATTIVI E INATTIVI (accesso alla app), i singoli endpoint controlleranno invece che sia anche attivo
    def login_for_access_token(self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
        # autentico lo studente tramite email e password
        student = self.authenticate_student(form_data.username, form_data.password)
        if not student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        # se è presente uno studente con quelle credenziali, creo un token con il suo id
        access_token = self.create_access_token(student.student_id, settings.access_token_expire_minutes)
        
        return Token(access_token=access_token, token_type="bearer")
            