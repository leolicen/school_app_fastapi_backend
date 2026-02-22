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




# FastAPI class instance
app = FastAPI(title=settings.app_name, lifespan=lifespan) 




# RESEND one-time global configuration at app launch
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
else:
    print("Resend API KEY not found. Reset password service will not work.")
    

# app-level rate limiter registration
setup_rate_limiter(app)

# logger config
setup_logging()

# exception handlers config
setup_handlers(app)

# add routers to app
app.include_router(authRouter)
app.include_router(internshipRouter)
app.include_router(courseRouter)
app.include_router(studentRouter)