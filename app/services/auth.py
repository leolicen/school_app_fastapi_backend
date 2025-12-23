from pwdlib import PasswordHash
from pydantic import EmailStr
from sqlmodel import Session, select
from ..models.student import Student

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


    # -- metodo GET USER -- verifica l'esistenza di un utente con quella email
    def get_student_in_db(self, email: EmailStr) -> Student | None:
        return self._db.exec(
            select(Student).where(Student.email == email)
        ).first()
        # first() restituisce già None se non trova nulla
       
        
    # -- funzione AUTENTICAZIONE UTENTE --
    def authenticate_student(self, email: EmailStr, password: str) -> Student | False:
        student = self.get_student_in_db(email)
        if not student:
            return False 
        if not self.verify_password(password, student.hashed_password):
            return False
        return student
            