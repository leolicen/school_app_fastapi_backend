from datetime import datetime, timedelta, timezone
import uuid
from sqlalchemy import select
from ..models.auth import AccessTokenData, ResetTokenInDB, RefreshTokenInDB, AccessRefreshToken
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
    def validate_access_token(token: str) -> AccessTokenData:
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
            return AccessTokenData(student_id=student_id)
        
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
        delete_previuos_tokens = delete(ResetTokenInDB).where(ResetTokenInDB.email == normalized_email)
        session.exec(delete_previuos_tokens)
        session.commit()
        
        # creo un nuovo token
        raw_token = secrets.token_urlsafe(32)
        # hasho il token
        token_hash = hash_reset_token(raw_token)
        # creo un nuovo ResetToken con token hashato associato all'email
        reset_token = ResetTokenInDB(
            email=normalized_email,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=15)
        )
        session.add(reset_token)
        session.commit()
        
        return raw_token
    
    
    # -- VALIDATE RESET TOKEN --
    @staticmethod
    def validate_reset_token(raw_reset_token: str, session: Session) -> ResetTokenInDB:
        # hasho il token raw
        reset_token_hash = hash_reset_token(raw_reset_token)
        # definisco query per selezionare reset token valido dal db
        check_token = select(ResetTokenInDB).where(
            ResetTokenInDB.token_hash == reset_token_hash,
            ResetTokenInDB.expires_at > datetime.now(timezone.utc)
        )
        # eseguo la query => token | None
        db_valid_token: ResetTokenInDB | None = session.exec(check_token).first()
        
        if not db_valid_token:
            raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
        return db_valid_token
    
    
    # -- CREATE REFRESH TOKEN --
    @staticmethod 
    def create_refresh_token(student_id: uuid.UUID, session: Session) -> str:
        
        # creo token raw
        raw_refresh_token = str(uuid.uuid4())
        # creo hash token
        hashed_refresh_token = AuthService.get_password_hash(raw_refresh_token)
        # creo istanza token in db
        refresh_token_in_db = RefreshTokenInDB(
            student_id=student_id,
            token_hash=hashed_refresh_token
        )
        
        session.add(refresh_token_in_db)
        session.commit()
        session.refresh(refresh_token_in_db)
        
        return raw_refresh_token
    
    
    # -- VALIDATE REFRESH TOKEN -- restituisco token o None
    @staticmethod
    def validate_refresh_token(refresh_token: str, student_id: uuid.UUID, session: Session) -> RefreshTokenInDB | None:
        print(f"Validating refresh token for student: {student_id}")
        print(f"Raw token: {refresh_token[:20]}")
        # hasho il token raw
        hashed_refresh_token = AuthService.get_password_hash(refresh_token)
        print(f"Hashed token: '{hash_reset_token[:20]}'")
        
        # definisco query db 
        check_token_validity = select(RefreshTokenInDB).where(
            RefreshTokenInDB.student_id == student_id,
            RefreshTokenInDB.token_hash == hashed_refresh_token
        )
        # eseguo query
        valid_token: RefreshTokenInDB | None = session.exec(check_token_validity).first()
        
        # se il token è sbagliato o già scaduto (eliminato dal db): errore
        if not valid_token:
            print(f"Token not found in DB: invalid or expired")
            return None
        # se il token è stato revocato: errore
        if valid_token.revoked_at is not None:
            print(f"Token found, but revoked at {valid_token.revoked_at}")
            return None
        
        # nel caso in cui il token sia scaduto, ma non sia ancora stato ripulito dal db: ERRORE
        if valid_token.expires_at <= datetime.now(timezone.utc):
            print(f"WARNING | Token expired: {valid_token.expires_at} < {datetime.now(timezone.utc)}")
            return None
        
        print("Token is VALID")
        return valid_token
    
    
    # -- REFRESH TOKEN ROTATION --
    @staticmethod
    def rotate_refresh_token(refresh_token: RefreshTokenInDB, session: Session) -> str:
        
        # estraggo id studente
        student_id = refresh_token.student_id
        
        # revoco l'attuale refresh_token
        refresh_token.revoked_at = datetime.now(timezone.utc)
        session.add(refresh_token)
        session.commit()
        
        # creo un nuovo refresh token
        new_refresh_token = AuthService.create_refresh_token(student_id, session) 
        
        return new_refresh_token
    
    
    # -- FUNZIONE ENDPOINT /REFRESH -- 
    @staticmethod
    def refresh_tokens(refresh_token: str, student_id: uuid.UUID, session: Session) -> AccessRefreshToken:
        # valido il refresh token ricevuto
        valid_refresh_token: RefreshTokenInDB | None = AuthService.validate_refresh_token(refresh_token, student_id, session)
        
        if not valid_refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # effettuo rotazione token (revoca vecchio token + creazione nuovo)
        new_refresh_token: str = AuthService.rotate_refresh_token(valid_refresh_token, session)
        
        # creo un nuovo access token
        new_access_token = AuthService.create_access_token(student_id, settings.access_token_expire_minutes)
        
        return AccessRefreshToken(access_token=new_access_token, token_type="bearer", refresh_token=new_refresh_token)
        
        
 
  
    
    
   
  