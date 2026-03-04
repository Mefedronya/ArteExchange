from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Account(Base):
    __tablename__ = 'Accounts'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(260), nullable=False)
    first_name = Column(String(80), nullable=False)
    surname = Column(String(80), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    def __repr__(self):
         return f"<Account id={self.id} username='{self.username}'>"