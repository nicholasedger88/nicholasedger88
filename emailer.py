import os
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List, Tuple

import requests
from jinja2 import Template

from markets import MarketSnapshot

BASE_DIR = Path(__file__).resolve().parent


def build_email_content(
    markets: List[MarketSnapshot],
    summary: str,
    unsubscribe_url: str,
) -> Tuple[str, str, str]:
    subject = "Markets in 90 Seconds"
    text_lines = [
        "Markets in 90 Seconds",
        summary,
        "",
        "Markets:",
    ]
    for market in markets:
        text_lines.append(
            f"- {market.name}: {market.change_1d:+.2f}% (1D), {market.change_5d:+.2f}% (5D), {market.change_ytd:+.2f}% (YTD)"
        )
    text_lines.append("")
    text_lines.append(f"Unsubscribe: {unsubscribe_url}")
    text_body = "\n".join(text_lines)

    template_path = BASE_DIR / "templates" / "email.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    html_body = template.render(
        summary=summary,
        markets=markets,
        unsubscribe_url=unsubscribe_url,
    )
    return subject, text_body, html_body


def send_email(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    if os.getenv("SENDGRID_API_KEY"):
        _send_via_sendgrid(to_email, subject, text_body, html_body)
        return
    _send_via_smtp(to_email, subject, text_body, html_body)


def _send_via_sendgrid(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "hello@marketsin90seconds.com")
    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body},
            {"type": "text/html", "value": html_body},
        ],
    }
    response = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
    )
    response.raise_for_status()


def _send_via_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    from_email = os.getenv("FROM_EMAIL", smtp_user or "hello@marketsin90seconds.com")

    if not smtp_host:
        raise RuntimeError("SMTP is not configured and SENDGRID_API_KEY is missing.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)
        server.send_message(message)
