from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Feedback(Base):
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(String(50), nullable=True)
    analysis_type = Column(String(30), nullable=False)
    rating = Column(Integer, default=0)
    helpful = Column(String(10), nullable=True)
    comment = Column(Text, nullable=True)
    prompt_snapshot = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UsageCredit(Base):
    __tablename__ = "usage_credits"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    balance_tokens = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    total_words_analyzed = Column(Integer, default=0)
    plan_type = Column(String(20), default="free")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class UsageLog(Base):
    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(String(50), nullable=True)
    analysis_type = Column(String(30), nullable=False)
    words_processed = Column(Integer, default=0)
    tokens_charged = Column(Integer, default=0)
    cost_cents = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_code = Column(String(20), unique=True, index=True, nullable=False)
    status = Column(String(20), default="pending")
    referrer_bonus = Column(Integer, default=0)
    referred_bonus = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SharedAnalysis(Base):
    __tablename__ = "shared_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    share_token = Column(String(32), unique=True, index=True, nullable=False)
    title = Column(String(200), default="")
    subject = Column(String(100), default="")
    course = Column(String(100), default="")
    data_json = Column(Text, nullable=False)
    views = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    badge = Column(String(50), nullable=False)
    earned_at = Column(DateTime(timezone=True), server_default=func.now())
