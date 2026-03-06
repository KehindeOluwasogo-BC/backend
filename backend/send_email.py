import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
load_dotenv()


api_key = os.getenv("SENDGRID_API_KEY")
from_email = os.getenv("FROM_EMAIL")
to_email = os.getenv("TO_EMAIL")

message = Mail(
    from_email=from_email,
    to_emails=to_email,
    subject="Reset your password",
    html_content="<p>This is another test email.</p>",
)

try:
    sg = SendGridAPIClient(api_key)
    response = sg.send(message)
    print(f"Sent. Status: {response.status_code}")
except Exception as exc:
    print(f"Send failed: {exc}")