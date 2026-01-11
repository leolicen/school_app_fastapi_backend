from pydantic import BaseModel, Field, EmailStr
import uuid
from sqlalchemy import BINARY, Column, func
from sqlmodel import SQLModel, Relationship
from typing import Annotated, TYPE_CHECKING
from datetime import datetime, timezone, timedelta
from .password import PasswordMatchModel
from ..core.settings import settings

if TYPE_CHECKING:
    from .student import StudentInDB

# -- ACCESS (& REFRESH) TOKEN PUBLIC -- quello che viene restituito all'utente
class AccessRefreshToken(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str 

# -- TOKEN DATA -- estratto dal token decodificato, usato in get_student_by_id
class AccessTokenData(BaseModel):
    # l'id studente preso dal token viene restituito come stringa
    student_id: str | None = None
    # definisco metodo che trasforma l'id, se presente, da str a UUID
    def get_uuid(self) -> uuid.UUID | None:
        if self.student_id:
            return uuid.UUID(self.student_id)
        return None

# -- RESET TOKEN -- tabella che salva i token temporanei per il reset password (associa email e reset token)
class ResetTokenInDB(SQLModel, table=True):
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
    



# -- REFRESH TOKEN -- token per refresh access token
class RefreshTokenInDB(SQLModel, table=True):
    refresh_token_id: Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    student_id: Annotated[uuid.UUID, Field(foreign_key="studentindb.student_id")]
    token_hash: str
    created_at: Annotated[datetime, Field(sa_column=Column(server_default=func.now(), nullable=False))]
    expires_at: Annotated[datetime, Field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days))]
    revoked_at: Annotated[datetime | None, Field(default=None, sa_column=Column(nullable=True))]
    
    student: StudentInDB = Relationship(back_populates="refresh_tokens")


    