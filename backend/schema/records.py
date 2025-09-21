from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class EventBase(BaseModel):
    event_type: str
    payload: Optional[dict] = None


class EventResponse(EventBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


class RecordBase(BaseModel):
    id: int
    project_name: str
    registry: str
    vintage: int
    quantity: float
    serial_number: str
    created_at: datetime


class RecordCreate(BaseModel):
    project_name: str
    registry: str
    vintage: int
    quantity: float
    serial_number: str


class RecordResponse(RecordBase):
    events: List[EventResponse] = []

    class Config:
        orm_mode = True
