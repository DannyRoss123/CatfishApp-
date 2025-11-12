from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, Boolean, Text, Float

from .database import Base


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    data = Column(LargeBinary, nullable=False)
    profile_url = Column(String)
    notes = Column(Text)
    profile_bio = Column(Text)
    conversation_text = Column(Text)
    phash = Column(String)
    sha256 = Column(String)
    risk_score = Column(Integer, default=0)
    confidence = Column(Float, default=0.0)
    signals = Column(Text)  # JSON string
    advice = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
