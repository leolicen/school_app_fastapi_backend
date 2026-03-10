from typing import Self

from sqlmodel import Field
from pydantic import BaseModel, EmailStr, field_validator, model_validator

from ..utils.validators import strong_password_validator, passwords_match_validator


class PasswordMatchModel(BaseModel):
    new_pwd: str
    new_pwd_confirm: str

    # field new_pwd vslidation => regex for syntax control 
    @field_validator('new_pwd')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return strong_password_validator(v)

    # whole model validation => checks if new_pwd_confirm is equal to new_pwd
    @model_validator(mode='after')
    def check_pwd_match(self: Self) -> Self:
        return passwords_match_validator(self)


# endpoint /students/change-password
class ChangePassword(PasswordMatchModel):
    current_password: str = Field(max_length=50, min_length=8)


# email of user requesting pwd reset, used in auth/password/reset-request
class ResetPasswordRequest(BaseModel):
    email: EmailStr


# raw token + new_pwd, used in auth/password/reset-confirm
class ResetPwdData(BaseModel):
    raw_reset_token: str
    new_pwd_data: PasswordMatchModel
