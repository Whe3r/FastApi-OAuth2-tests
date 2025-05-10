from sqlalchemy.orm import sessionmaker

from models import Account
from dataclasses import dataclass
from main import SessionLocal
import logging

session = sessionmaker()
logger = logging.getLogger(__name__)


@dataclass
class FinancialServices:
    id: int
    user_id: int

    def deposit(self, user_id: int, amount: float, sm: sessionmaker) -> float:
        db = sm()
        user_account = db.query(Account).filter(Account.user_id == user_id).first()

        if amount <= 0:
            raise ValueError("Сумма пополнения должна быть положительная")
        if user_account:
            user_account.user_balance += amount
            db.commit()
            db.refresh(user_account)
            return user_account.user_balance
        raise ValueError("Пользователь не найден")

    def withdraw(self, user_id: int, amount: float, sm: sessionmaker) -> float:
        db = sm()
        user_account = db.query(Account).filter(Account.id == user_id).first()
        if user_account.user_balance <= 0 or user_account.user_balance < amount:
            raise ValueError("Сумма которую вы хотите снять превышает ваш баланс")
        if user_account:
            user_account.user_balance -= amount
            db.commit()
            db.refresh(user_account)
            return user_account.user_balance
        raise ValueError("Пользователь не найден")

    def send_to(self, amount: float, user_id: int, send_to_user_id: int, sm: sessionmaker) -> [float]:
        db = sm()
        user_account = db.query(Account).filter(Account.id == user_id).first()
        if not user_account:
            raise ValueError("Отправитель не найден")

        recipient_account = db.query(Account).filter(Account.user_id == send_to_user_id).first()
        if not recipient_account:
            raise ValueError("Получатель не найден")

        if 0 >= amount > user_account.user_balance:
            raise ValueError("Сумма которую вы хотите перевести превышает ваш баланс")

        user_account.user_balance -= amount
        recipient_account.user_balance += amount
        db.commit()
        db.refresh(user_account)
        db.refresh(recipient_account)

        return user_account.user_balance, recipient_account.user_balance

    def show_balance(self, account_id: int) -> float:
        db = SessionLocal()
        user_account = db.query(Account).filter(Account.id == account_id).first()
        if user_account:
            logger.info(f"Ваш баланс {user_account.user_balance}")
            return user_account.user_balance

