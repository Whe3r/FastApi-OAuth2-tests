
from sqlalchemy import Column, Integer, String, ForeignKey, Float
from pydantic import BaseModel
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    password = Column(String)
    account = relationship("Account", back_populates="user")


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user_balance = Column(Float)
    user = relationship("User", back_populates="account")


class UserAuth(BaseModel):
    username: str
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class AccountModel(BaseModel):
    id: int
    user_id: int
    user_balance: float
