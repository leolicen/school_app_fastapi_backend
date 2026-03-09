import logging

import resend

from ..core.settings import settings

logger = logging.getLogger(__name__)



class EmailService():
    
        
    @staticmethod
    def send_reset_email(email: str, reset_token: str) -> resend.Emails.SendResponse | None:
        
        # check whether resend api key exists
        if not settings.resend_api_key:
            logger.warning(f"Resend API KEY not found. Unable to send email to {email}.")
            return
            
        # compose url to app (frontend) reset pwd page & append ResetToken
        reset_url = f"{settings.pwd_reset_url}?token={reset_token}"
        
        # define email parameters 
        params: resend.Emails.SendParams = {
            "from": f"NoReplySchool-app <{settings.resend_from}>",
            "to": [f"{email}"],
            "subject": "Reset password",
            "html": f"""<h2>Reset password</h2>
            <p>Click <a href="{reset_url}">here</a> within 15 minutes to reset your password.</p>
            """
        }
        
        try:
            reset_email: resend.Emails.SendResponse = resend.Emails.send(params)
            logger.info(f"Reset email sent successfully to {email}")
            return reset_email
        
        except resend.ResendException as e:
            logger.warning(f"Resend API failed for {email}: {str(e)}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error sending email to {email}: {str(e)}")
            return None
    
       
    
