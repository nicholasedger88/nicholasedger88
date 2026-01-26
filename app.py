import os
import secrets
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request, send_file
import stripe

from emailer import build_email_content, send_email
from markets import fetch_market_snapshot, generate_summary
from models import SendLog, SessionLocal, User, init_db
from scheduler import start_scheduler

BASE_DIR = Path(__file__).resolve().parent

load_dotenv()

app = Flask(__name__)

init_db()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")


@app.get("/")
def landing_page():
    return send_file(BASE_DIR / "index.html")


@app.post("/signup")
def signup():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "Email is required."}), 400

    session = SessionLocal()
    try:
        user = session.query(User).filter_by(email=email).first()
        if not user:
            user = User(
                email=email,
                plan="free_weekly",
                is_active=True,
                unsubscribe_token=secrets.token_urlsafe(16),
            )
            session.add(user)
        else:
            user.is_active = True
        session.commit()
    finally:
        session.close()

    return jsonify({"status": "ok", "plan": "free_weekly"})


@app.post("/create-checkout")
def create_checkout():
    payload = request.get_json(silent=True) or request.form
    email = (payload.get("email") or "").strip().lower()
    price_id = os.getenv("STRIPE_PRICE_ID", "")
    if not stripe.api_key or not price_id:
        return jsonify({"error": "Stripe is not configured."}), 500
    if not email:
        return jsonify({"error": "Email is required."}), 400

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=email,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{request.host_url}success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{request.host_url}",
        metadata={"email": email},
    )
    return jsonify({"checkout_url": session.url})


@app.get("/success")
def success():
    session_id = request.args.get("session_id")
    if not session_id:
        return "Missing session_id", 400

    session = stripe.checkout.Session.retrieve(session_id)
    email = session.customer_details.get("email") if session.customer_details else None
    if not email:
        return "Missing customer email", 400

    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter_by(email=email.lower()).first()
        if not user:
            user = User(
                email=email.lower(),
                plan="pro_daily",
                is_active=True,
                unsubscribe_token=secrets.token_urlsafe(16),
            )
            db_session.add(user)
        else:
            user.plan = "pro_daily"
            user.is_active = True
        db_session.commit()
    finally:
        db_session.close()

    return render_template_string(
        """
        <main style="font-family: system-ui; padding: 3rem;">
          <h1>You're all set.</h1>
          <p>Your subscription is active. You'll receive the next daily issue.</p>
          <a href="/">Return home</a>
        </main>
        """
    )


@app.get("/unsubscribe/<token>")
def unsubscribe(token):
    db_session = SessionLocal()
    try:
        user = db_session.query(User).filter_by(unsubscribe_token=token).first()
        if not user:
            return "Invalid token", 404
        user.is_active = False
        db_session.commit()
    finally:
        db_session.close()
    return "You have been unsubscribed."


@app.get("/admin/stats")
def admin_stats():
    admin_key = os.getenv("ADMIN_KEY", "")
    provided_key = request.headers.get("X-Admin-Key") or request.args.get("key")
    if not admin_key or provided_key != admin_key:
        return "Unauthorized", 401

    today = datetime.utcnow().date()
    db_session = SessionLocal()
    try:
        total_users = db_session.query(User).count()
        sends_today = (
            db_session.query(SendLog)
            .filter(SendLog.sent_at >= datetime.combine(today, datetime.min.time()))
            .count()
        )
        failures = (
            db_session.query(SendLog)
            .filter(SendLog.status == "failed")
            .count()
        )
    finally:
        db_session.close()

    return jsonify(
        {
            "total_users": total_users,
            "sends_today": sends_today,
            "failures": failures,
        }
    )


@app.post("/admin/send-test")
def send_test_email():
    admin_key = os.getenv("ADMIN_KEY", "")
    provided_key = request.headers.get("X-Admin-Key") or request.args.get("key")
    if not admin_key or provided_key != admin_key:
        return "Unauthorized", 401

    payload = request.get_json(silent=True) or request.form
    email = payload.get("email")
    if not email:
        return "Email required", 400

    markets = fetch_market_snapshot()
    summary = generate_summary(markets)
    subject, text_body, html_body = build_email_content(
        markets,
        summary,
        unsubscribe_url=f"{request.host_url}unsubscribe/test",
    )
    send_email(email, subject, text_body, html_body)
    return "Sent"


if __name__ == "__main__":
    if os.getenv("START_SCHEDULER", "true").lower() == "true":
        start_scheduler()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
