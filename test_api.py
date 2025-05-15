import os

from fastapi.testclient import TestClient

from bank import FinancialServices
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, User
import jwt

from models import Base, User, Account


from main import hash_password
import pytest

SQLALCHEMY_DATABASE_URL = "sqlite:///D:\\database.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(autouse=True)
def run_before_and_after_tests(tmpdir):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


def test_register_user():
    response = client.post("/register", json={
        "username": "user2",
        "email": "user2@mail.com",
        "password": "user"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "user2"
    assert "id" in data
    assert isinstance(data["password"], str)


def test_login_user():
    db = TestSessionLocal()
    hashed_password = hash_password('aaw213')
    new_user = User(username='user', email='test12@mail.ru', password=hashed_password)
    db.add(new_user)
    db.commit()
    response = client.post("/authorization", data={"username": "user", "password": "aaw213"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_fail_login():
    response = client.post("/authorization",
                           data={"username": "fakeuser", "password": "fakepassword"})
    assert response.status_code == 401


def test_deposit():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "fs_id": 3,
        "amount": 1000
    }
    response = client.post("/deposit", headers=headers, params=params)


    assert response.status_code == 200


