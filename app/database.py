from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# from .config import SQLALCHEMY_DATABASE_URL

SQLALCHEMY_DATABASE_URL = "postgresql://mohamed:mohamedj1@localhost/ideamentor"


engine = create_engine(SQLALCHEMY_DATABASE_URL)
                       
SessionLocal = sessionmaker(bind=engine)


Base = declarative_base()