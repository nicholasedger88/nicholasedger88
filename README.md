# Markets in 90 Seconds

Minimal Flask MVP for a calm market digest list with paid gating via Gumroad import.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` with your email provider and database settings.

## Run

```bash
python app.py
```

Open http://localhost:5000 to see the landing page.

## Send commands

Paid subscribers are emailed via Flask CLI commands:

```bash
flask --app app send-daily
flask --app app send-weekly
```

- `send-daily` sends to paid subscribers who have not received an email today.
- `send-weekly` sends to paid subscribers who have not received an email in the last 6 days.

## Gumroad import

Export buyers from Gumroad as CSV and run:

```bash
python scripts/import_gumroad_csv.py path/to/gumroad.csv
```

The script upserts subscribers, setting status to `paid`.

## Email providers

Set `EMAIL_PROVIDER` to `smtp` or `sendgrid`.

### SMTP (Gmail app password)
```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your@gmail.com
SMTP_PASS=app-password
SMTP_FROM=your@gmail.com
```

### SendGrid
```
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-key
SMTP_FROM=hello@marketsin90seconds.com
```

## Environment variables
- `FLASK_SECRET_KEY`: Flask session key.
- `DATABASE_URL`: SQLAlchemy database URL (default `sqlite:///app.db`).
- `EMAIL_PROVIDER`: `smtp` or `sendgrid`.
- `SMTP_*`: SMTP credentials.
- `SENDGRID_API_KEY`: SendGrid API key.
- `SMTP_FROM`: From address for both providers.
- `BASE_URL`: Public base URL for unsubscribe links.
- `PORT`: Flask port.
