from typing import Annotated, Self
from pydantic import BaseModel, Field, field_validator, model_validator
from ..utils.validators import strong_password_validator, passwords_match_validator



class PasswordMatchModel(BaseModel):
    new_pwd: str
    new_pwd_confirm: str

    # validazione campo new_pwd => regex per controllo sintattico
    @field_validator('new_pwd')
    @classmethod
    def validate_password(cls, v: str) -> str:
        return strong_password_validator(v)
    
    # validazione modello intero => controlla che new_pwd_confirm sia uguale a new_pwd
    @model_validator(mode='after')
    def check_pwd_match(self: Self) -> Self:
        return passwords_match_validator(self)
    
    
    


class ChangePassword(PasswordMatchModel):
    current_password: Annotated[str, Field(max_length=50, min_length=8)]
    
    

