from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    
    # -- DATABASE --
    # l'ordine di precedenza è: 1) inserted params (none here) 2) .env keys values 3) default values 
    # here mix between mandatory fields (if absent from .env, error) and default fields
  
    app_name: str = "School App FastAPI Server"
    db_user: str
    db_password:str 
    db_name: str 
    db_host: str = "localhost"
    db_port: int = 3306 
    
    # define getter, a method that acts like a property and returns db url
    @property
    def db_url(self):
        # compose URL that directs to DB 
        # charset=utf8mb4 => complete unicode 
        # pool_timeout=30 => max wait for free connection (30s)
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4&pool_timeout=30"
    
    # -- JWT --
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    
    redis_url: str = "redis://localhost:6379/0"
    
    # -- REFRESH TOKEN
    refresh_token_expire_days: int = 7
    
    # PasswordHash instance with Argon2 as hasher
    pwd_hash = PasswordHash.recommended()
    # define OAuth2PasswordBearer instance that requests endpoint url that returns the token
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
    
    resend_api_key: str
    resend_from: str
    pwd_reset_url: str # flutter app url to reset password (to implement with go router)
    
    
    # nested class that tells Pydantic how to behave (without Pydantic it would only read system env variables)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    

settings = Settings()