from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import resend
from fastapi.openapi.utils import get_openapi

from .core.settings import settings
from .core.rate_limiting import setup_rate_limiter
from .core.logger import setup_logging
from .exceptions.handlers import setup_handlers
from .routers.auth import router as authRouter
from .routers.course import router as courseRouter
from .routers.internship import router as internshipRouter
from .routers.student import router as studentRouter
from .core.database import lifespan


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(title="School API", version="1.0.0", routes=app.routes)
    
    for path in openapi_schema["paths"].values():
        for method in path.values():
            if "parameters" in method:
                method["parameters"] = [p for p in method["parameters"] if p.get("name") not in ["args", "kwargs"]]
    app.openapi_schema = openapi_schema
    return app.openapi_schema





# istanza della classe FastAPI
app = FastAPI(title=settings.app_name, lifespan=lifespan) 

# @app.exception_handler(RequestValidationError)
# async def filter_args_kwargs(request: Request, exc: RequestValidationError):
#     print("Handler triggered")
#     print(f"Total errors: {len(exc.errors())}")
    
#     for i, error in enumerate(exc.errors()):
#         print(f"Error {i}: loc={error['loc']}, msg={error['msg']}")
    
#     filtered = [e for e in exc.errors() if e['loc'][-1] not in ('args', 'kwargs')]
    
#     print(f"Filtered to {len(filtered)} errors")
    
#     if filtered:
#         print("Re-raising filtered errors")
#         raise RequestValidationError(filtered)
    
#     print("✅ IGNORING args/kwargs")
    
#     return JSONResponse({"detail": "Validation passed"}, status_code=200)


app.openapi = custom_openapi


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