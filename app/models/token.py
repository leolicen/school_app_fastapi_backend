from pydantic import BaseModel
import uuid

# -- modello TOKEN PUBLIC -- quello che viene restituito all'utente
class Token(BaseModel):
    access_token: str
    token_type: str

# -- modello TOKEN DATA -- estratto dal token decodificato, usato in get_student_by_id
class TokenData(BaseModel):
    # l'id utente preso dal token viene restituito come stringa
    user_id: str | None = None
    # definisco metodo che trasforma l'id, se presente, da str a UUID
    def get_uuid(self) -> uuid.UUID | None:
        if self.user_id:
            return uuid.UUID(self.user_id)
        return None