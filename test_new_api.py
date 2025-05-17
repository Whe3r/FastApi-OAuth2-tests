import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import main

from main import app, get_current_user, SessionLocal, get_db
from models import User, Account

client = TestClient(app)


class MockSession:
    def query(self, model):
        mock_query = MagicMock()

        if model == User:
            mock_user = MagicMock(spec=User)
            mock_user.id = 1
            mock_user.username = "user"
            mock_user.email = "user@example.com"
            mock_user.password = "test"
            mock_query.filter.return_value.first.return_value = mock_user

        elif model == Account:
            mock_account = MagicMock(spec=Account)
            mock_account.user_balance = 1000
            mock_account.user_id = 1
            mock_query.filter.return_value.first.return_value = mock_account

        else:
            mock_query.filter.return_value.first.return_value = None

        return mock_query

    def commit(self):
        pass

    def refresh(self, odj):
        pass

    def close(self):
        pass


def mock_session_local():
    return MockSession()


async def mock_get_current_user():
    class UserMock:
        id = 1
        username = "user"

    return UserMock()


app.dependency_overrides[get_current_user] = mock_get_current_user
app.dependency_overrides[SessionLocal] = mock_session_local
app.dependency_overrides[get_db] = mock_session_local

main.SessionLocal = mock_session_local


def test_deposit():
    headers = {"Authorization": "Bearer token"}
    response = client.post("/deposit", headers=headers, params={"fs_id": 3, "amount": 500})

    assert response.status_code == 200
    data = response.json()
    assert "user_balance" in data
    assert data["user_balance"] == 1500


def test_withdraw():
    headers = {"Authorization": "Bearer token"}
    response = client.post("/withdraw", headers=headers, params={"fs_id": 3, "amount": 500})
    assert response.status_code == 200
    data = response.json()
    assert "user_balance" in data
    assert data["user_balance"] == 500


def test_send():
    headers = {"Authorization": "Bearer token"}
    params = {"fs_id": 3, "amount": 500, "recipient_id": 2}
    response = client.post("/send", headers=headers, params=params)
    assert response.status_code == 200
    data = response.json()
    assert "sender_balance" in data
    assert "recipient_balance" in data
    assert data["sender_balance"] == 500
    assert data["recipient_balance"] == 1500


def test_show_balance():
    headers = {"Authorization": "Bearer token"}
    response = client.get("/show-balance", headers=headers, params={"fs_id": 3})
    assert response.status_code == 200
    data = response.json()
    assert "user_balance" in data
    assert data["user_balance"] == 1000
