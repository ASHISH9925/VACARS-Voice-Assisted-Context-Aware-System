import os
import requests
from typing import List

from langchain_core.tools import tool

from config import RESEND_MAIL_FROM
from utils.logger import get_logger

logger = get_logger(__name__)

RESEND_API_BASE_URL = "https://api.resend.com"
RESEND_API_ENDPOINT = "/emails"


@tool
def send_email(to: List[str], subject: str, body: str) -> str:
    """
    Send an email to a recipient using Resend REST API

    Args:
        to: List of email addresses to send the email to
        subject: The subject of the email
        body: The body of the email, this must be in HTML format be creative and make it interesting
    """
    try:
        api_key = os.environ.get("RESEND_API_KEY")
        if not api_key:
            return "Error: RESEND_API_KEY environment variable not set"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "from": RESEND_MAIL_FROM,
            "to": to,
            "subject": subject,
            "html": body,
        }

        logger.info(f"Sending email with payload: {payload}")

        response = requests.post(
            f"{RESEND_API_BASE_URL}{RESEND_API_ENDPOINT}", headers=headers, json=payload
        )
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Email sent successfully. ID: {response_data.get('id')}")
            return f"Email sent successfully to {to} with subject '{subject}'. Email ID: {response_data.get('id')}"
        else:
            error_message = f"Failed to send email. Status: {response.status_code}, Response: {response.text}"
            logger.error(error_message)
            return error_message

    except requests.exceptions.RequestException as e:
        return f"Network error while sending email to {to}: {str(e)}"
    except Exception as e:
        return f"Failed to send email to {to}: {str(e)}"
