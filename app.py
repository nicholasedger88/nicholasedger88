import os
import secrets
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, url_for
from sqlalchemy import or_

from digest import build_digest
from emailer import send_digest_email
from models import SendLog, SessionLocal, Subscriber, init_db

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", secrets.token_urlsafe(16))

    init_db()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/signup")
    def signup():
        email = request.form.get("email", "").strip().lower()
        if not email:
            return render_template("index.html", error="Please enter a valid email."), 400

        session = SessionLocal()
        try:
            subscriber = session.query(Subscriber).filter_by(email=email).first()
            if not subscriber:
                subscriber = Subscriber(
                    email=email,
                    status="waitlist",
                    unsubscribe_token=secrets.token_urlsafe(16),
                    is_active=True,
                )
                session.add(subscriber)
            else:
                subscriber.is_active = True
            session.commit()
        finally:
            session.close()

        return redirect(url_for("index", success="1"))

    @app.get("/u/<token>")
    def unsubscribe(token: str):
        session = SessionLocal()
        try:
            subscriber = session.query(Subscriber).filter_by(unsubscribe_token=token).first()
            if not subscriber:
                return render_template("unsubscribed.html", invalid=True), 404
            subscriber.status = "waitlist"
            subscriber.is_active = False
            session.commit()
        finally:
            session.close()
        return render_template("unsubscribed.html")

    @app.cli.command("send-daily")
    def send_daily():
        start_of_today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        session = SessionLocal()
        try:
            subscribers = (
                session.query(Subscriber)
                .filter(
                    Subscriber.status == "paid",
                    Subscriber.is_active.is_(True),
                    or_(Subscriber.last_sent_at.is_(None), Subscriber.last_sent_at < start_of_today),
                )
                .all()
            )
        finally:
            session.close()
        _send_digest_to_subscribers(subscribers, "daily")

    @app.cli.command("send-weekly")
    def send_weekly():
        threshold = datetime.utcnow() - timedelta(days=6)
        session = SessionLocal()
        try:
            subscribers = (
                session.query(Subscriber)
                .filter(
                    Subscriber.status == "paid",
                    Subscriber.is_active.is_(True),
                    or_(Subscriber.last_sent_at.is_(None), Subscriber.last_sent_at < threshold),
                )
                .all()
            )
        finally:
            session.close()
        _send_digest_to_subscribers(subscribers, "weekly")

    return app


def _send_digest_to_subscribers(subscribers, period: str) -> None:
    digest = build_digest()
    session = SessionLocal()
    try:
        for subscriber in subscribers:
            log = SendLog(subscriber_id=subscriber.id, period=period, status="ok")
            try:
                send_digest_email(
                    subscriber,
                    digest,
                )
                subscriber.last_sent_at = datetime.utcnow()
            except Exception as exc:
                log.status = "fail"
                log.error_message = str(exc)
            session.add(log)
            session.add(subscriber)
        session.commit()
    finally:
        session.close()


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
