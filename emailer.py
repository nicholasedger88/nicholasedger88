import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

import requests
from jinja2 import Template

from digest import Digest

BASE_DIR = Path(__file__).resolve().parent


def send_digest_email(subscriber, digest: Digest) -> None:
    provider = os.getenv("EMAIL_PROVIDER", "smtp").lower()
    html_body = _render_html(digest, subscriber)
    text_body = _render_text(digest, subscriber)
    if provider == "sendgrid":
        _send_via_sendgrid(subscriber.email, digest.subject, text_body, html_body)
    else:
        _send_via_smtp(subscriber.email, digest.subject, text_body, html_body)


def _render_html(digest: Digest, subscriber) -> str:
    template_path = BASE_DIR / "templates" / "email_digest.html"
    template = Template(template_path.read_text(encoding="utf-8"))
    return template.render(
        summary=digest.summary,
        tiles=digest.tiles,
        unsubscribe_url=_unsubscribe_url(subscriber),
    )


def _render_text(digest: Digest, subscriber) -> str:
    lines = [digest.subject, digest.summary, "", "Markets:"]
    for tile in digest.tiles:
        lines.append(
            f"- {tile.name}: {tile.change_1d} (1D), {tile.change_5d} (5D), {tile.change_ytd} (YTD)"
        )
    lines.append("")
    lines.append(f"Unsubscribe: {_unsubscribe_url(subscriber)}")
    return "\n".join(lines)


def _unsubscribe_url(subscriber) -> str:
    base_url = os.getenv("BASE_URL", "http://localhost:5000/")
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"
    return f"{base_url}u/{subscriber.unsubscribe_token}"


def _send_via_sendgrid(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SMTP_FROM", "hello@marketsin90seconds.com")
    if not api_key:
        raise RuntimeError("SENDGRID_API_KEY is required for sendgrid provider.")

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
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
        timeout=10,
    )
    response.raise_for_status()


def _send_via_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASS")
    from_email = os.getenv("SMTP_FROM", user or "hello@marketsin90seconds.com")

    if not host:
        raise RuntimeError("SMTP_HOST is required for smtp provider.")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = from_email
    message["To"] = to_email
    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    with smtplib.SMTP(host, port) as server:
        server.starttls()
        if user and password:
            server.login(user, password)
        server.send_message(message)
