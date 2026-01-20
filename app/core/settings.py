from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # -- Database --
    # l'ordine di precedenza è: parametri inseriti (qui nessuno), valori
    # chiavi .env, valori di default
    # qui mix tra campi obbligatori (se assenti da .env danno errore)
    # e default
    app_name: str = "School App FastAPI Server"
    db_user: str
    db_password:str 
    db_name: str 
    db_host: str = "localhost"
    db_port: int = 3306 
    
    # definisco un getter, un metodo che si comporta come una semplice
    # proprietà, che mi restituisce l'url db 
    @property
    def db_url(self):
        # compongo l'URL che punta al DB su XAMPP 
        # charset=utf8mb4 => unicode completo
        # pool_timeout=30 => attesa max per connessione libera (30s)
        return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4&pool_timeout=30"
    
    # -- JWT --
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    
    redis_url: str = "redis://localhost:6379/0"
    
    # -- REFRESH TOKEN
    refresh_token_expire_days: int = 7
    
    # istanza di PasswordHash con Argon2 come hasher
    pwd_hash = PasswordHash.recommended()
    # definisco istanza di OAuth2PasswordBearer che richiede l'url dell'endpoint che restituisce il token
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
    
    resend_api_key: str
    resend_from: str
    pwd_reset_url: str # indirizzo pagina app Flutter per reset password (da implementare con go router)
    
    
    # classe annidata che dice a Pydantic come comportarsi (senza Pydantic leggerebbe solo variabili d'ambiente di sistema)
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )
    

settings = Settings()