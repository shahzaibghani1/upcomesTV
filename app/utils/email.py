import smtplib
from email.mime.text import MIMEText
from email_validator import validate_email, EmailNotValidError
from typing import Dict, Union

# A placeholder function to simulate a third-party email validation API.
async def verify_email_existence(email: str) -> Dict[str, Union[str,bool]]:
    """
    Simulates a call to a third-party email verification service.
    
    In a real application, you would replace this with an actual API call
    to a service like Hunter.io, ZeroBounce, or Mailtrap.
    
    This function performs a basic check and simulates the result.
    """
    try:
        # Pydantic's EmailStr already does this, but this is a more robust check
        # using a dedicated library. It checks for DNS, MX records, etc.
        # check_deliverability=True performs a check to see if the domain is valid.
        valid = validate_email(email, check_deliverability=True)
        # NOTE: This does NOT guarantee the email is a real, legitimate account.
        # It just means the domain exists and can receive emails.
        # A service like ZeroBounce would do an SMTP check to confirm a mailbox.
        return {"is_valid": True, "details": "Email format and domain valid."}
    except EmailNotValidError as e:
        return {"is_valid": False, "details": str(e)}

# The original email sending function remains, but is now more specific in its purpose.
def send_email(to_email: str, subject: str, body: str):
    from_email = "upcomestv25@gmail.com"  # your actual Gmail
    from_password = "fvvs jlfs otsg prml"  # your Gmail password or app password
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
    server.login(from_email, from_password)
    server.sendmail(from_email, [to_email], msg.as_string())
    server.quit()