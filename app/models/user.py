from enum import Enum

from sqlmodel import SQLModel


class UserRole(str, Enum):
    STUDENT = "student"
    TUTOR = "tutor"
    
class UserPublic(SQLModel):
    """ Model returned by require_role() dependency. """
    role: UserRole
    is_active: bool
