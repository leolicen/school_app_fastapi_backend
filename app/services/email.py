import resend
from app.core.settings import settings



class EmailService():
    
        
    @staticmethod
    def send_reset_email(email: str, reset_token: str) -> resend.Emails.SendResponse | None:
        
        # controllo che esista l'api key di resend
        if not settings.resend_api_key:
            print(f"Resend API KEY not found. Unable to send email to {email}.")
            return
            
        # compongo l'url endpoint per reset pwd aggiungendo il ResetToken
        reset_url = f"{settings.pwd_reset_url}?token={reset_token}"
        # definisco i parametri dell'email da inviare
        params: resend.Emails.SendParams = {
            "from": f"Acme <{settings.resend_from}>",
            "to": [f"{email}"],
            "subject": "Reset password",
            "html": f"""<h2>Reset password</h2>
            <p>Clicca <a href="{reset_url}">qui</a> entro 15 minuti.</p>
            """
        }
        
        try:
            reset_email: resend.Emails.SendResponse = resend.Emails.send(params)
            print(f"Reset email sent successfully to {email}")
            return reset_email
        except Exception as e:
            print(f"Failed to send reset email to {email}: {str(e)}")
            return None
    
       
    
