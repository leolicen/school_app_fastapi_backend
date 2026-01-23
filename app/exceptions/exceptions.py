
# BASE CLASS for all app errors
class AppError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message) # message passed to the superclass => Python standard for a human-readable traceback | only the message is shown in a standard traceback
    

class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Incorrect email or password"): # message = only parameter => it can change (incorrect email | incorrect password)
        super().__init__(message, "INVALID CREDENTIALS") # code is not passed manually because it's always the same for both cases
        

class AccountExpiredError(AppError):
    def __init__(self, message: str = "Account retrieval period expired"):
        super().__init__(message, "ACCOUNT_EXPIRED")
        

class DuplicateEmailError(AppError):
    def __init__(self, message: str = "Email already registered"):
        super().__init__(message, "DUPLICATE_EMAIL")
        

class DatabaseError(AppError):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, "DATABASE_ERROR")
        

class StudentNotFoundError(AppError):
    def __init__(self, message: str = "Student not found"):
        super().__init__(message, "STUDENT_NOT_FOUND")