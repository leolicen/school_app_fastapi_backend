from datetime import datetime, timedelta, timezone
import uuid
from ..models.auth import TokenData, ResetToken
import jwt
from ..core.settings import settings
from fastapi import HTTPException, status
from pydantic import EmailStr
from ..utils.validators import normalize_email
from sqlmodel import delete, Session
import secrets
from ..services.student import StudentService
from ..utils.hash_reset_token import hash_reset_token



class AuthService():
    

    # metodo di MATCH tra PWD IN CHIARO (input utente) e PWD HASHATA salvata nel DB
    @staticmethod
    def verify_password(plain_password: str | bytes, hashed_password: str | bytes) -> bool:
        return settings.pwd_hash.verify(plain_password, hashed_password)


    # metodo per CREARE HASH di una PWD IN CHIARO
    @staticmethod
    def get_password_hash(password: str | bytes) -> str:
        return settings.pwd_hash.hash(password)

    
    # -- funzione CREAZIONE TOKEN -- crea token con id studente e valore exp
    @staticmethod
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
        
    
    # -- funzione VALIDAZIONE TOKEN -- decodifica del token e restituzione ID UTENTE (TokenData)
    @staticmethod
    def validate_token(token: str) -> TokenData:
        # creo HTTP exception in caso di errore di validazione token
        invalid_token_exception = HTTPException(
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
                raise invalid_token_exception
            
            # restituisco un oggetto TokenData per maggior controllo
            return TokenData(user_id=student_id)
        
        except (jwt.PyJWTError, ValueError):
            raise invalid_token_exception
        
 
        
    @staticmethod
    def create_reset_token(
        email: EmailStr,
        student_service: StudentService,
        session: Session
        ) -> str:
        # controllo internamente che l'email corrisponda a un utente registrato
        student_in_db = student_service.get_student_by_email(email)
        # se non esiste loggo errore internamente e esco 
        if not student_in_db:
            raise ValueError("Email not registered") # solo interno
        
        # se esiste, normalizzo l'email per evitare errori come abc@xyz.COM vs. abc@xyz.com
        normalized_email = normalize_email(email)
        # elimino eventuale reset token già esistente
        delete_previuos_tokens = delete(ResetToken).where(ResetToken.email == normalized_email)
        session.exec(delete_previuos_tokens)
        session.commit()
        
        # creo un nuovo token
        raw_token = secrets.token_urlsafe(32)
        # hasho il token
        token_hash = hash_reset_token(raw_token)
        # creo un nuovo ResetToken con token hashato associato all'email
        reset_token = ResetToken(
            email=normalized_email,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(reset_token)
        session.commit()
        
        return raw_token
    
    
    
 
  
    
    
   
  