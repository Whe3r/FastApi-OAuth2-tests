from datetime import datetime, timezone, timedelta

import jwt
from fastapi.testclient import TestClient

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Account

import pytest
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.test")

from main import app, get_db
from main import hash_password

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set for testing")

engine = create_engine(DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(autoflush=False, autocommit=False, bind=engine)


def get_test_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = get_test_db

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
    password_plain = 'aaw213'
    hashed_password = hash_password(password_plain)
    db = TestSessionLocal()
    new_user = User(username='user', email='test12@mail.ru', password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    response = client.post("/authorization", data={"username": "user", "password": password_plain})
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
    db.refresh(new_user)
    account = Account(user_id=new_user.id, user_balance=0)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 1000
    }
    response = client.post("/deposit", headers=headers, params=params)
    data = response.json()
    assert response.status_code == 200
    assert "user_balance" in data
    assert data["user_balance"] == 1000


def test_withdraw():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    account = Account(user_id=new_user.id, user_balance=10000)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 5000
    }
    response = client.post("/withdraw", headers=headers, params=params)
    data = response.json()
    assert response.status_code == 200
    assert "user_balance" in data
    assert data["user_balance"] == 5000


def test_send():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    new_user2 = User(username="testuser2", email="test2@mexample.com", password=hashed_password)
    db.add(new_user)
    db.add(new_user2)
    db.commit()
    account = Account(user_id=new_user.id, user_balance=10000)
    account2 = Account(user_id=2, user_balance=10000)
    db.add(account)
    db.add(account2)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 5000,
        "recipient_id": 2
    }
    response = client.post("/send", headers=headers, params=params)
    data = response.json()
    assert response.status_code == 200
    assert "sender_balance" in data
    assert "recipient_balance" in data
    assert data["sender_balance"] == 5000
    assert data["recipient_balance"] == 15000


def test_show_balance():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    account = Account(user_id=new_user.id, user_balance=5000)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = client.get("/show-balance", headers=headers)
    data = response.json()
    assert response.status_code == 200
    assert "user_balance" in data
    assert data["user_balance"] == 5000


def test_deposit_negative_amount():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    account = Account(user_id=new_user.id, user_balance=0)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": -1000
    }
    response = client.post("/deposit", headers=headers, params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "Сумма пополнения должна быть положительная"


def test_deposit_user_not_found():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 1000
    }
    response = client.post("/deposit", headers=headers, params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "Пользователь не найден"


def test_withdraw_amount_negative():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    account = Account(user_id=new_user.id, user_balance=10000)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": -5000
    }
    response = client.post("/withdraw", headers=headers, params=params)

    assert response.status_code == 400


def test_withdraw_exceeding_balance():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser2", email="test2@example.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    account = Account(user_id=new_user.id, user_balance=1000)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser2", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "amount": 5000
    }

    response = client.post("/withdraw", headers=headers, params=params)

    assert response.status_code == 400
    assert response.json()["detail"] == "Сумма которую вы хотите снять превышает ваш баланс"


def test_withdraw_user_not_found():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 5000
    }
    response = client.post("/withdraw", headers=headers, params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "Пользователь не найден"


def test_send_sender_not_found():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    new_user2 = User(username="testuser2", email="test2@mexample.com", password=hashed_password)
    db.add(new_user)
    db.add(new_user2)
    db.commit()
    account2 = Account(user_id=2, user_balance=10000)
    db.add(account2)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 5000,
        "recipient_id": 2
    }
    response = client.post("/send", headers=headers, params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "Отправитель не найден"


def test_send_recipient_not_found():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    new_user2 = User(username="testuser2", email="test2@mexample.com", password=hashed_password)
    db.add(new_user)
    db.add(new_user2)
    db.commit()
    account = Account(user_id=new_user.id, user_balance=10000)
    db.add(account)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 5000,
        "recipient_id": 2
    }
    response = client.post("/send", headers=headers, params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "Получатель не найден"


def test_send_amount_negative():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    new_user2 = User(username="testuser2", email="test2@mexample.com", password=hashed_password)
    db.add(new_user)
    db.add(new_user2)
    db.commit()
    account = Account(user_id=new_user.id, user_balance=10000)
    account2 = Account(user_id=2, user_balance=10000)
    db.add(account)
    db.add(account2)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": -5000,
        "recipient_id": 2
    }
    response = client.post("/send", headers=headers, params=params)
    assert response.status_code == 400


def test_send_exceeding_balance():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    new_user2 = User(username="testuser2", email="test2@mexample.com", password=hashed_password)
    db.add(new_user)
    db.add(new_user2)
    db.commit()
    account = Account(user_id=new_user.id, user_balance=1000)
    account2 = Account(user_id=2, user_balance=10000)
    db.add(account)
    db.add(account2)
    db.commit()
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    params = {
        "amount": 5000,
        "recipient_id": 2
    }
    response = client.post("/send", headers=headers, params=params)
    assert response.status_code == 400
    assert response.json()["detail"] == "Сумма которую вы хотите перевести превышает ваш баланс"


def test_show_balance_user_not_found():
    db = TestSessionLocal()
    hashed_password = hash_password("test")
    new_user = User(username="testuser", email="test@mexample.com", password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    login_response = client.post("/authorization", data={"username": "testuser", "password": "test"})
    assert login_response.status_code == 200
    token = login_response.json().get("access_token")
    assert token is not None

    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = client.get("/show-balance", headers=headers)
    assert response.status_code == 400
    assert response.json()["detail"] == "Пользователь не найден"
