from sqlmodel import Session
from .auth import AuthService
from ..models.student import StudentCreate, StudentPublic, Student
from fastapi import HTTPException


class StudentService():
    def __init__(self, session: Session): #auth_service: AuthService
        self._db = session
        # self._auth_service = auth_service
        
    