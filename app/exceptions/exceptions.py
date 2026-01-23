
# BASE CLASS for all app errors
class AppError(Exception):
    def __init__(self, message: str, code: str):
        self.message = message
        self.code = code
        super().__init__(message) # message passed to the superclass => Python standard for a human-readable traceback | only the message is shown in a standard traceback
    

class InvalidCredentialsError(AppError):
    def __init__(self, message: str = "Incorrect email or password"): # message = only parameter => it can change (incorrect email | incorrect password)
        super().__init__(message, "INVALID CREDENTIALS") # code is not passed manually because it's always the same for both cases
    