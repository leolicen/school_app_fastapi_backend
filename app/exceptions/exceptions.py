
# BASE CLASS for all app errors
from decimal import Decimal


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
        

class InvalidCurrentPasswordError(AppError):
    def __init__(self, message: str = "Current password is not correct"):
        super().__init__(message, "INVALID_CURRENT_PASSWORD")
        
        
class InvalidResetTokenError(AppError):
    def __init__(self, message: str = "Invalid or expired reset token"):
        super().__init__(message, "INVALID_RESET_TOKEN")
        
        
class InvalidRefreshTokenError(AppError):
    def __init__(self, message: str = "Invalid or expired refresh token"):
        super().__init__(message, "INVALID_REFRESH_TOKEN")
        
        
class MissingRefreshTokenError(AppError):
    def __init__(self, message: str = "Refresh token required"):
        super().__init__(message, "MISSING_REFRESH_TOKEN")
        

class CourseNotFoundError(AppError):
    def __init__(self, message: str = "Course not found"):
        super().__init__(message, "COURSE_NOT_FOUND")
        
class AgreementForbiddenError(AppError):
    def __init__(self, message: str = "Agreement not found or not accessible"):
        super().__init__(message, "AGREEMENT_FORBIDDEN")
        
class AgreementEntryMismatchError(AppError):
    def __init__(self, message: str = "Agreement mismatch"):
        super().__init__(message, "AGREEMENT_MISMATCH")
        
class InternshipCompletedError(AppError):
    def __init__(self, message: str = "Internship completed. Cannot create new entry"):
        super().__init__(message, "INTERNSHIP_COMPLETED")
        
class InternshipHoursExceededError(AppError):
    def __init__(self, requested: Decimal, remaining: Decimal):
        super().__init__(f"Cannot insert {requested} hours. Only {remaining} left", "INTERNSHIP_HOURS_EXCEEDED")
        

class InternshipOverlappingEntryError(AppError):
    def __init__(self, message: str = "Overlapping entry time. Cannot create new entry"):
        super().__init__(message, "INTERNSHIP_OVERLAPPING_ENTRY")
        
class InternshipEntryNotDeletableError(AppError):
    def __init__(self, message: str = "Entry not found or too old to be canceled"):
        super().__init__(message, "INTERNSHIP_ENTRY_NOT_DELETABLE")