"""
Reporter module
- Handles email and Slack notifications
"""
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path
from typing import List
import requests
import datetime as dt


class Reporter:
    def __init__(self, smtp_server: str, smtp_port: int,
                 smtp_user: str, smtp_password: str,
                 mail_to: List[str], slack_webhook: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.mail_to = mail_to
        self.slack_webhook = slack_webhook

    def send_email(self, html_path: Path, env: str, title: str):
        """Send HTML report via email"""
        if not (self.smtp_user and self.smtp_password):
            print("⚠️ SMTP credentials missing – skipping e-mail")
            return

        msg = EmailMessage()
        msg["Subject"] = f"{title} – {env} – {dt.date.today()}"
        msg["From"] = self.smtp_user
        msg["To"] = self.mail_to
        msg.add_alternative(html_path.read_text(), subtype="html")

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context) as smtp:
            smtp.login(self.smtp_user, self.smtp_password)
            smtp.send_message(msg)

    def send_slack(self, text: str, env: str):
        """Send plaintext report to Slack"""
        # if not self.slack_webhook:
        #     print("⚠️ Slack webhook missing – skipping Slack notification")
        #     return

        # Format for Slack (code block)
        slack_text = f"```\n{text}\n```"



        payload = {
            "text": f"Test Report for {env.upper()} environment",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": slack_text
                    }
                }
            ]
        }

        try:
            response = requests.post(self.slack_webhook, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"⚠️ Slack notification failed: {e}")
            raise