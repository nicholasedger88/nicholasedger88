import os
from datetime import datetime
from typing import Iterable

from apscheduler.schedulers.background import BackgroundScheduler

from emailer import build_email_content, send_email
from markets import fetch_market_snapshot, generate_summary
from models import SendLog, SessionLocal, User


def _has_sent_today(user_id: int, period: str) -> bool:
    today = datetime.utcnow().date()
    session = SessionLocal()
    try:
        return (
            session.query(SendLog)
            .filter(
                SendLog.user_id == user_id,
                SendLog.period == period,
                SendLog.sent_at >= datetime.combine(today, datetime.min.time()),
            )
            .count()
            > 0
        )
    finally:
        session.close()


def _send_to_users(users: Iterable[User], period: str) -> None:
    markets = fetch_market_snapshot()
    summary = generate_summary(markets)
    base_url = os.getenv("BASE_URL", "http://localhost:5000/")
    if not base_url.endswith("/"):
        base_url = f"{base_url}/"

    session = SessionLocal()
    try:
        for user in users:
            if _has_sent_today(user.id, period):
                continue
            unsubscribe_url = f"{base_url}unsubscribe/{user.unsubscribe_token}"
            subject, text_body, html_body = build_email_content(
                markets,
                summary,
                unsubscribe_url=unsubscribe_url,
            )
            log = SendLog(user_id=user.id, period=period, status="sent")
            try:
                send_email(user.email, subject, text_body, html_body)
            except Exception:
                log.status = "failed"
            session.add(log)
        session.commit()
    finally:
        session.close()


def send_daily() -> None:
    session = SessionLocal()
    try:
        users = (
            session.query(User)
            .filter(User.plan == "pro_daily", User.is_active.is_(True))
            .all()
        )
    finally:
        session.close()
    _send_to_users(users, "daily")


def send_weekly() -> None:
    session = SessionLocal()
    try:
        users = (
            session.query(User)
            .filter(User.plan == "free_weekly", User.is_active.is_(True))
            .all()
        )
    finally:
        session.close()
    _send_to_users(users, "weekly")


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler(timezone="UTC")
    scheduler.add_job(send_daily, "cron", hour=7, minute=15)
    scheduler.add_job(send_weekly, "cron", day_of_week="sun", hour=8, minute=0)
    scheduler.start()
    return scheduler
