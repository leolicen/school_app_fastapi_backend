from pydantic import BaseModel, EmailStr
import uuid
from sqlmodel import SQLModel, Relationship, Field
from typing import Annotated, TYPE_CHECKING, Optional
from datetime import datetime
from .password import PasswordMatchModel


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
    reset_token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True) # , 
    email: Annotated[str, Field(max_length=320, index=True)]
    token_hash: Annotated[str, Field(max_length=255, index=True)]
    expires_at: datetime
    
# -- RESET PWD DATA -- dati inviati a endpoint reset-confirm (raw token + new_pwd)
class ResetPwdData(BaseModel):
    raw_reset_token: str
    new_pwd_data: PasswordMatchModel
    
# -- RICHIESTA RESET PWD -- contiene l'email di chi fa richiesta
class ResetPasswordRequest(BaseModel):
    email: EmailStr
    

# refresh_token_expire_days = settings.refresh_token_expire_days
# default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=7)


# -- REFRESH TOKEN -- token per refresh access token
class RefreshTokenInDB(SQLModel, table=True):
    refresh_token_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True) # Annotated[uuid.UUID, Field(default_factory=uuid.uuid4, primary_key=True, sa_column=Column(BINARY(16)))]
    student_id: Annotated[str, Field(foreign_key="studentindb.student_id")] #foreign_key="studentindb.student_id"
    token_hash:  Annotated[str, Field(max_length=255, index=True)]
    created_at: datetime # sa_column=Column(server_default=func.now()
    expires_at: datetime
    revoked_at: Optional[datetime] #default=None, 
    
    student: "StudentInDB" = Relationship(back_populates="refresh_tokens")


    