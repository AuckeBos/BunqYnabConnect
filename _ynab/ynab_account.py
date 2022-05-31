from typing import List

from ynab import Account, Category, TransactionDetail

from helpers.helpers import get_ynab_connector


class YnabAccount:
    account_info: Account
    transactions: List[TransactionDetail]
    categories: List[Category]
    budget_id: int

    def __init__(self, acc: Account):
        self.account_info = acc

    def set_budget_id(self, id: int):
        self.budget_id = id
        return self

    def load_transactions(self) -> "YnabAccount":
        self.transactions = get_ynab_connector().get_transactions(self)
        return self

    @property
    def iban(self) -> str:
        """
        A _ynab account normally doesn't have an Iban. This project works based on the
        assumption that the user saves the Iban of the _bunq account that is linked to
        the _ynab account, in its notes
        """
        return self.account_info.note

    @property
    def id(self) -> str:
        return self.account_info.id
