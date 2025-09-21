from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from config.db import Base
import uuid


class Record(Base):
    __tablename__ = "records"

    id = Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    registry = Column(String, nullable=False)
    vintage = Column(Integer, nullable=False)
    quantity = Column(Float, nullable=False)
    serial_number=Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="record", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(Integer, ForeignKey("records.id"), nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    record = relationship("Record", back_populates="events")
