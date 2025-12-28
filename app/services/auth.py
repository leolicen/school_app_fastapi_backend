from datetime import datetime, timedelta, timezone
from typing import Annotated
from pwdlib import PasswordHash
from pydantic import EmailStr
from sqlmodel import Session, select
from ..models.student import Student
import uuid
from ..models.token import TokenData, Token
import jwt
from ..core.settings import settings
from fastapi import Depends, HTTPException
from jwt.exceptions import InvalidTokenError

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
    def get_student_by_email(self, email: EmailStr) -> Student | None:
        return self._db.exec(
            select(Student).where(Student.email == email)
        ).first()
        # first() restituisce già None se non trova nulla
        
    # -- metodo GET STUDENT BY ID -- verifica l'esistenza di un utente tramite id
    def get_student_by_id(self, id: uuid.UUID) -> Student | None:
        return self._db.exec(
            select(Student).where(Student.student_id == id)
        ).first()
       
       
    # -- funzione AUTENTICAZIONE UTENTE -- in fase di LOGIN
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
    
    
    # -- funzione GET CURRENT USER -- recupera lo studente a partire dal token => dipendenza iniettata in ogni endpoint
    #async def get_current_user(self, token: Annotated[str, Depends()]):