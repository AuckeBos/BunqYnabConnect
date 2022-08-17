from typing import Any, List

from bunq_ynab_connector._ynab.ynab_account import YnabAccount
from helpers.helpers import get_ynab_connector


class Budget:
    budget_info: Any
    id: int
    accounts: List[YnabAccount]
    categories: List[str]

    def __init__(self, budget_info: Any):
        self.budget_info = budget_info

    @property
    def id(self):
        return self.budget_info.id

    def _load_accounts(self):
        self.accounts = []
        for account in get_ynab_connector().get_ynab_accounts():
            if account.budget_id == self.id:
                self.accounts.append(account)

    def _load_categories(self):
        self.categories = get_ynab_connector().get_categories(self.id)

    def load_info(self):
        self._load_accounts()
        self._load_categories()
        return self
