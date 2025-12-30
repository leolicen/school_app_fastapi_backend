from core.database import SessionDep
from services.auth import AuthService
from typing import Annotated
from fastapi import Depends

# -- AUTH SERVICE DEPENDENCY --

def get_auth_service(session: SessionDep) -> AuthService:
    return AuthService(session=session)

