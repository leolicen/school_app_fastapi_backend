from pydantic import BaseModel, Field, EmailStr
import uuid
from sqlalchemy import BINARY, Column
from sqlmodel import SQLModel
from typing import Annotated
from datetime import datetime
from .password import PasswordMatchModel

# -- TOKEN PUBLIC -- quello che viene restituito all'utente
class Token(BaseModel):
    access_token: str
    token_type: str

# -- TOKEN DATA -- estratto dal token decodificato, usato in get_student_by_id
class TokenData(BaseModel):
    # l'id utente preso dal token viene restituito come stringa
    user_id: str | None = None
    # definisco metodo che trasforma l'id, se presente, da str a UUID
    def get_uuid(self) -> uuid.UUID | None:
        if self.user_id:
            return uuid.UUID(self.user_id)
        return None

# -- RESET TOKEN -- tabella che salva i token temporanei per il reset password (associa email e reset token)
class ResetToken(SQLModel, table=True):
    reset_token_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    email: EmailStr
    token_hash: str
    expires_at: datetime
    
# -- RESET PWD DATA -- dati inviati a endpoint reset-confirm (raw token + new_pwd)
class ResetPwdData(BaseModel):
    raw_reset_token: str
    new_pwd_data: PasswordMatchModel
    
# -- RICHIESTA RESET PWD -- contiene l'email di chi fa richiesta
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    