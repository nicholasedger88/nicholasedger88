# Markets in 90 Seconds

Minimal Flask app for a calm, daily or weekly markets summary email.

## Features
- Static landing page served from `index.html`.
- Email subscriptions with free weekly and paid daily plans.
- SQLite + SQLAlchemy models for users and send logs.
- Market data from Yahoo Finance (indices, FX, rates) and CoinGecko (gold via PAXG proxy).
- Stripe Checkout for subscriptions.
- SendGrid delivery with SMTP fallback.
- APScheduler background jobs for daily and weekly sends.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with your keys.
Set `BASE_URL` to the public origin for unsubscribe links.

## Run the app

```bash
python app.py
```

## Stripe setup
- Create a product + recurring price in Stripe.
- Set `STRIPE_SECRET_KEY` and `STRIPE_PRICE_ID`.
- The app creates a Checkout Session at `/create-checkout` and upgrades users after `/success`.

## SendGrid or SMTP
- If `SENDGRID_API_KEY` is set, SendGrid is used.
- Otherwise the app falls back to SMTP using `SMTP_HOST`, `SMTP_USER`, and `SMTP_PASSWORD`.

## Scheduler
- Daily: 07:15 UTC (pro_daily users)
- Weekly: Sunday 08:00 UTC (free_weekly users)

Disable the scheduler by setting `START_SCHEDULER=false`.

## Admin
`/admin/stats` is protected by `ADMIN_KEY` via header `X-Admin-Key` or query param `?key=`.

Example:

```bash
curl -H "X-Admin-Key: $ADMIN_KEY" http://localhost:5000/admin/stats
```
