from sqlalchemy.orm import session
from app.database import SessionLocal
from typing import Annotated
from fastapi import Depends
from typing import Annotated


#  db_dependency

def get_db():
    db = SessionLocal()  #
    try:
        yield db
    finally:
        db.close() 


db_dependency = Annotated[session, Depends(get_db) ]





