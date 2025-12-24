from pydantic import BaseModel
import uuid

# -- modello TOKEN PUBLIC -- quello che viene restituito all'utente
class Token(BaseModel):
    access_token: str
    token_type: str

# -- modello TOKEN DATA -- estratto dal token decodificato, usato in get_student_by_id
class TokenData(BaseModel):
    user_id: uuid.UUID | None = None