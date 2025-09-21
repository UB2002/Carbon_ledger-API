from config.db import get_db
from sqlalchemy.orm import Session
from models.table import Record, Event
from schema.records import RecordCreate, RecordBase, RecordResponse, EventResponse
from datetime import datetime
from fastapi import Depends, APIRouter, HTTPException

router = APIRouter()


@router.post("/", response_model=RecordResponse)
def create_record(record: RecordCreate, db: Session = Depends(get_db)):
    db_record = Record(
        project_name=record.project_name,
        registry=record.registry,
        vintage=record.vintage,
        quantity=record.quantity,
        serial_number=record.serial_number,
    )
    # The 'created_at' is handled by the model's default

    # Add creation event through the relationship
    db_record.events.append(Event(event_type="created", payload=record.dict()))

    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@router.get("/", response_model=list[RecordBase])
def get_records(db: Session = Depends(get_db)):
    records = db.query(Record).all()
    return records


@router.get("/{record_id}", response_model=RecordResponse)
def get_record_by_id(record_id: str, db: Session = Depends(get_db)):
    record = db.query(Record).filter(Record.id == record_id).first()
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@router.post("/{record_id}/retire", response_model=EventResponse)
def retire_record(record_id: str, db: Session = Depends(get_db)):
    # It's good practice to lock the record to prevent race conditions.
    record = db.query(Record).filter(Record.id == record_id).with_for_update().first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    # Check for existing "retired" event on the record's events list
    if any(e.event_type == "retired" for e in record.events):
        raise HTTPException(status_code=400, detail="Record already retired")

    event = Event(
        event_type="retired",
        payload={},
    )
    # Appending to the relationship will automatically set record_id
    record.events.append(event)
    db.commit()
    db.refresh(event)
    return event
