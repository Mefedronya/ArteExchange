from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQLALCHEMY_DATABASE_URL = (
    "mssql+pyodbc://DESKTOP-P5B9MPU\\SQLEXPRESS/it_planet"
    "driver=ODBC+Driver+17+for+SQL+Server&"
    "trusted_connection=yes"
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=True  
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()