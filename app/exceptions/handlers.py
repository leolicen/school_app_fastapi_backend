from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .exceptions import AppError
import logging

logger = logging.getLogger(__name__)

# default handler for all app errors
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    
    logger.error(f"{exc.code} - {exc.message} at {request.url}", exc_info=True) # exc_info=True shows complete traceback
    
    status_code = {
        "INVALID_CREDENTIALS": 401,
        "NOT_FOUND": 404
    }.get(exc.code, 400) # gets status_code["exc.code"] value, if key exists, otherwise default 400 
    
    return JSONResponse(
        status_code=status_code,
        content= {
            "error": {"code": exc.code, "message": exc.message}
            }
    )
    
    
    



# -- SETUP HANDLERS --
def setup_handlers(app: FastAPI):
    app.add_exception_handler(AppError, app_error_handler)