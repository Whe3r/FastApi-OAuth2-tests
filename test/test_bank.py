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

        bank = FinancialServices(1, 1)
        result = MagicMock()
        db = MagicMock()
        fl = MagicMock()
        sm = MagicMock(return_value=db)
        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.return_value = account

        res = bank.deposit(1, 20000, sm)
        self.assertEqual(res, 21000)

        with self.assertRaises(ValueError):
            bank.deposit(1, -2, sm)

        fl.first.return_value = None
        with self.assertRaises(ValueError):
            bank.deposit(10, 2000, sm)

    def test_withdraw(self):
        account = Account()
        account.id = 1
        account.user_id = 1
        account.user_balance = 10000

        bank = FinancialServices(1, 1)
        result = MagicMock()
        db = MagicMock()
        fl = MagicMock()
        sm = MagicMock(return_value=db)
        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.return_value = account

        res = bank.withdraw(1, 2000, sm)
        self.assertEqual(res, 8000)

        with self.assertRaises(ValueError):
            bank.withdraw(1, 20000, sm)

        with self.assertRaises(ValueError):
            bank.withdraw(1, -2000, sm)

        fl.first.return_value = None
        with self.assertRaises(ValueError):
            bank.withdraw(10, 2000, sm)


   #@pytest.mark.parametrize()
    def test_send_to(self):
        account1 = Account()
        account1.id = 1
        account1.user_id = 10
        account1.user_balance = 3000
        account2 = Account()
        account2.id = 2
        account2.user_id = 2
        account2.user_balance = 5000
        bank = FinancialServices(1, 1)

        db = MagicMock()
        sm = MagicMock(return_value=db)
        fl = MagicMock()
        result = MagicMock()

        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.side_effect = [account1, account2]

        actual = bank.send_to(1000, 1, 2, sm)
        self.assertEqual(2000, actual[0])
        self.assertEqual(6000, actual[1])

        fl.first.side_effect = [None, account2]
        with self.assertRaises(ValueError):
            bank.send_to(1000, 1, 2, sm)

        fl.first.side_effect = [account1, None]
        with self.assertRaises(ValueError):
            bank.send_to(1000, 1, 2, sm)

        fl.first.side_effect = [account1, account2]
        with self.assertRaises(ValueError):
            bank.send_to(20000, 1, 2, sm)

        fl.first.side_effect = [account1, account2]
        with self.assertRaises(ValueError):
            bank.send_to(-2000, 1, 2, sm)

    def test_show_balance(self):
        account = Account()
        account.id = 1
        account.user_id = 1
        account.user_balance = 1000

        bank = FinancialServices(1, 1)
        result = MagicMock()
        db = MagicMock()
        fl = MagicMock()
        sm = MagicMock(return_value=db)
        db.query.return_value = result
        result.filter.return_value = fl
        fl.first.return_value = account

        res = bank.show_balance(1, sm)
        self.assertEqual(res, 1000)

        fl.first.return_value = None
        with self.assertRaises(ValueError):
            bank.show_balance(10, sm)


if __name__ == '__main__':
    unittest.main()
