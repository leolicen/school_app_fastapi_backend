from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# carico file .env 
load_dotenv()

# definisco classe Config con nomi proprietà uguali a chiavi del 
# file .env => in automatico pydantic associerà i valori delle chiavi .env
# con quelli della classe Config
# l'ordine di precedenza è: parametri inseriti (qui nessuno), valori
# chiavi .env, valori di default
# qui mix tra campi obbligatori (se assenti da .env danno errore)
# e default
class Config(BaseSettings):
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
    

config = Config()
    