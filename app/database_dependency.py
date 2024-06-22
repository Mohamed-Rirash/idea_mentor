from sqlalchemy.orm import Session  # Import Session class
from app.database import SessionLocal
from fastapi import Depends
from typing import Annotated

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 

db_dependency = Annotated[Session, Depends(get_db)]  # Use Session class here
