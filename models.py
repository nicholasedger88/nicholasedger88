from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DB_URL = "sqlite:///markets.db"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    plan = Column(String, nullable=False, default="free_weekly")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    unsubscribe_token = Column(String, unique=True, nullable=False)
    watchlist = Column(JSON, default=list)

    send_logs = relationship("SendLog", back_populates="user")


class SendLog(Base):
    __tablename__ = "send_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    period = Column(String, nullable=False)
    status = Column(String, nullable=False)

    user = relationship("User", back_populates="send_logs")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
