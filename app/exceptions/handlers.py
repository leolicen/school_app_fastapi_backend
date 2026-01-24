from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import jwt
from .exceptions import AppError, InvalidCredentialsError, AccountExpiredError, DuplicateEmailError, DatabaseError, StudentNotFoundError, InvalidCurrentPasswordError, InvalidResetTokenError, InvalidRefreshTokenError, MissingRefreshTokenError, CourseNotFoundError
import logging
from jwt import InvalidTokenError

logger = logging.getLogger(__name__)

# -- APP ERROR -- default handler for all app errors
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    
    logger.error(f"{exc.code} - {exc.message} at {request.url}", exc_info=True) # exc_info=True shows complete traceback
    
    status_code = {
        "INVALID_CREDENTIALS": 401,
        "INVALID_ACCESS_TOKEN": 401,
        "INVALID_REFRESH_TOKEN": 401,
        "MISSING_REFRESH_TOKEN": 401,
        "INVALID_CURRENT_PASSWORD": 403,
        "INVALID_RESET_TOKEN": 403,
        "STUDENT_NOT_FOUND": 404,
        "COURSE_NOT_FOUND": 404,
        "DUPLICATE_EMAIL": 409,
        "ACCOUNT_EXPIRED": 410,
        "INTERNAL_ERROR": 500,
        "DATABASE_ERROR": 503
    }.get(exc.code, 400) # gets status_code["exc.code"] value, if key exists, otherwise default 400 
    
    return JSONResponse(
        status_code=status_code,
        content= {
            "error": {"code": exc.code, "message": exc.message}
            }
    )
    
# -- INVALID CREDENTIALS --
def invalid_credentials_handler(request: Request, exc: InvalidCredentialsError) -> JSONResponse:
    
    logger.warning(f"Invalid login at {request.url}")
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"error": {"code": exc.code, "message": exc.message}},
        headers={"WWW-Authenticate": "Bearer"} # tells the client to authenticate via bearer token
    )
    


# -- PyJWTError -- base class =>  catches everything (false signature, wrong secret key, wrong algorithm) => server error
def pyjwt_error_handler(request: Request, exc: jwt.PyJWTError) -> JSONResponse:
    
    logger.critical(f"PyJWTError at {request.url}: {exc}")
    
    return JSONResponse(
        status_code=500, 
        content={"error": {"code": "INTERNAL_ERROR"}}
        )

    
# -- INVALID ACCESS TOKEN -- PyJWTError subclass  => catches invalid tokens only (false signature, decode fail, exp) => client error
def invalid_access_token_handler(request: Request, exc: InvalidTokenError) -> JSONResponse:
    
    logger.warning(f"JWT InvalidTokenError at {request.url}: {exc}")
    
    return JSONResponse(
        status_code=401,
        content={"error": {"code": "INVALID_ACCESS_TOKEN", "message": "Invalid access token"}},
        headers={"WWW-Authenticate": "Bearer"}
    )



# -- ACCOUNT EXPIRED --
def account_expired_handler(request: Request, exc: AccountExpiredError) -> JSONResponse:
    
    logger.warning(f"Account retrieval period expired at {request.url} - {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_410_GONE, # target resource permanently deleted,
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    

# -- DUPLICATE EMAIL --
def duplicate_email_handler(request: Request, exc: DuplicateEmailError) -> JSONResponse:
    
    logger.warning(f"Duplicate email at {request.url} - {exc.message}")
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    

# -- DATABASE ERROR --
def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    
    logger.warning(f"Database error at {request.url}: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    

# -- STUDENT NOT FOUND --
def student_not_found_handler(request: Request, exc: StudentNotFoundError) -> JSONResponse:
    
    logger.warning(f"Student not found at {request.url}: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, 
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    

# -- INVALID CURRENT PASSWORD --
def invalid_current_password_handler(request: Request, exc: InvalidCurrentPasswordError) -> JSONResponse:
    
    logger.warning(f"Current password is not correct at {request.url}: {exc.message}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN, 
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    

# -- INVALID RESET TOKEN --
def invalid_reset_token_handler(request: Request, exc: InvalidResetTokenError) -> JSONResponse:
    
    logger.warning(f"Invalid/expired reset token at {request.url}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, 
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    
    
# -- INVALID REFRESH TOKEN --
def invalid_refresh_token_handler(request: Request, exc: InvalidRefreshTokenError) -> JSONResponse:
    
    logger.warning(f"Invalid/expired refresh token at {request.url}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    
    
# -- MISSING REFRESH TOKEN --
def missing_refresh_token_handler(request: Request, exc: MissingRefreshTokenError) -> JSONResponse:
    
    logger.warning(f"Missing refresh token at {request.url}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        content={{"code": exc.code, "message": exc.message}}
    )
    

def course_not_found_handler(request: Request, exc: CourseNotFoundError) -> JSONResponse:
    
    logger.warning(f"Course not found at {request.url}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, 
        content={"error": {"code": exc.code, "message": exc.message}}
    )
    



# -- SETUP HANDLERS --
def setup_handlers(app: FastAPI):
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(jwt.PyJWTError, pyjwt_error_handler)
    app.add_exception_handler(InvalidTokenError, invalid_access_token_handler)
    app.add_exception_handler(AccountExpiredError, account_expired_handler)
    app.add_exception_handler(DuplicateEmailError, duplicate_email_handler)
    app.add_exception_handler(DatabaseError, database_error_handler)
    app.add_exception_handler(StudentNotFoundError, student_not_found_handler)
    app.add_exception_handler(InvalidCurrentPasswordError, invalid_current_password_handler)
    app.add_exception_handler(InvalidResetTokenError, invalid_reset_token_handler)
    app.add_exception_handler(InvalidRefreshTokenError, invalid_refresh_token_handler)
    app.add_exception_handler(MissingRefreshTokenError, missing_refresh_token_handler)
    app.add_exception_handler(CourseNotFoundError, course_not_found_handler)