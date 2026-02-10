from fastapi import FastAPI
import resend

from .core.settings import settings
from .core.rate_limiting import setup_rate_limiter
from .core.logger import setup_logging
from .exceptions.handlers import setup_handlers
from .routers.auth import router as authRouter
from .routers.course import router as courseRouter
from .routers.internship import router as internshipRouter
from .routers.student import router as studentRouter
from .core.database import lifespan



# istanza della classe FastAPI
app = FastAPI(title=settings.app_name, lifespan=lifespan) #,lifespan=lifespan


# configurazione globale RESEND una volta sola all'avvio dell'app
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
else:
    print("Resend API KEY not found. Reset password service will not work.")
    

# registro un rate limiter a livello di app
setup_rate_limiter(app)

# logger config
setup_logging()

# exception handlers config
setup_handlers(app)

app.include_router(authRouter)
app.include_router(internshipRouter)
app.include_router(courseRouter)
app.include_router(studentRouter)