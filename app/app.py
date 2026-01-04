from fastapi import FastAPI
import resend
from .core.settings import settings



# istanza della classe FastAPI
app = FastAPI(title="ITS App API") #,lifespan=lifespan

# configurazione globale RESEND una volta sola all'avvio dell'app
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
else:
    print("Resend API KEY not found. Reset password service will not work.")
