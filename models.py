import os
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False, default="waitlist")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_sent_at = Column(DateTime, nullable=True)
    unsubscribe_token = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    send_logs = relationship("SendLog", back_populates="subscriber")


class SendLog(Base):
    __tablename__ = "send_logs"

    id = Column(Integer, primary_key=True)
    subscriber_id = Column(Integer, ForeignKey("subscribers.id"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)
    period = Column(String, nullable=False)
    status = Column(String, nullable=False)
    error_message = Column(String, nullable=True)

    subscriber = relationship("Subscriber", back_populates="send_logs")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
