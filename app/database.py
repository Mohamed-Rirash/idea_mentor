from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.config import SQLALCHEMY_DATABASE_URL
# from .config import SQLALCHEMY_DATABASE_URL


engine = create_engine(SQLALCHEMY_DATABASE_URL)
                       
SessionLocal = sessionmaker(bind=engine)


Base = declarative_base()