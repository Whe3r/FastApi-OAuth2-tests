import unittest
from unittest.mock import Mock, MagicMock

from unittest.mock import MagicMock

from bank import FinancialServices

from models import Account
from bank import FinancialServices


class MyTestCase(unittest.TestCase):
    def test_deposit(self):
        account = Account()
        account.id = 1
        account.user_id = 1
        account.user_balance = 1000
        result = MagicMock()
        db = MagicMock()
        fl = MagicMock()

        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.return_value = account
        bank = FinancialServices(db)

        res = bank.deposit(1, 20000)
        self.assertEqual(res, 21000)

        with self.assertRaises(ValueError):
            bank.deposit(1, -2)

        fl.first.return_value = None
        with self.assertRaises(ValueError):
            bank.deposit(10, 2000)

    def test_withdraw(self):
        account = Account()
        account.id = 1
        account.user_id = 1
        account.user_balance = 10000
        db = MagicMock()
        fl = MagicMock()
        result = MagicMock()

        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.return_value = account
        bank = FinancialServices(db)

        res = bank.withdraw(1, 2000)
        self.assertEqual(res, 8000)

        with self.assertRaises(ValueError):
            bank.withdraw(1, 20000)

        with self.assertRaises(ValueError):
            bank.withdraw(1, -2000)

        fl.first.return_value = None
        with self.assertRaises(ValueError):
            bank.withdraw(10, 2000)

    # @pytest.mark.parametrize()
    def test_send_to(self):
        account1 = Account()
        account1.id = 1
        account1.user_id = 10
        account1.user_balance = 3000
        account2 = Account()
        account2.id = 2
        account2.user_id = 2
        account2.user_balance = 5000
        db = MagicMock()
        fl = MagicMock()
        result = MagicMock()

        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.side_effect = [account1, account2]
        bank = FinancialServices(db)

        actual = bank.send_to(1000, 1, 2)
        self.assertEqual(2000, actual[0])
        self.assertEqual(6000, actual[1])

        fl.first.side_effect = [None, account2]
        with self.assertRaises(ValueError):
            bank.send_to(1000, 1, 2)

        fl.first.side_effect = [account1, None]
        with self.assertRaises(ValueError):
            bank.send_to(1000, 1, 2)

        fl.first.side_effect = [account1, account2]
        with self.assertRaises(ValueError):
            bank.send_to(20000, 1, 2)

        fl.first.side_effect = [account1, account2]
        with self.assertRaises(ValueError):
            bank.send_to(-2000, 1, 2)

    def test_show_balance(self):
        account = Account()
        account.id = 1
        account.user_id = 1
        account.user_balance = 1000
        result = MagicMock()
        db = MagicMock()
        fl = MagicMock()

        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.return_value = account
        bank = FinancialServices(db)

        res = bank.show_balance(1)
        self.assertEqual(res, 1000)

        fl.first.return_value = None
        with self.assertRaises(ValueError):
            bank.show_balance(10)


if __name__ == '__main__':
    unittest.main()
