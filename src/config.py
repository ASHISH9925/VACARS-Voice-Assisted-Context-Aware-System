import os

SAY_WPM = 130
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
RESEND_MAIL_FROM = os.getenv("RESEND_MAIL_FROM", "Helmet AI <onboarding@resend.dev>")
CAMERA_URL = os.getenv("CAMERA_URL", "http://192.168.0.225")  # esp cam URL
BLUE_LED_PIN = int(os.getenv("BLUE_LED_PIN", "18"))

# Known contacts prompt list (can be overridden via CONTACTS_LIST in .env)
CONTACTS_LIST = os.getenv(
    "CONTACTS_LIST",
    "- Person 1: person1@example.com\n- Person 2: person2@example.com",
)
