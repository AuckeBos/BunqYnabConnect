from typing import List

from bunq.sdk.model.core.bunq_model import BunqModel
from bunq.sdk.model.generated.endpoint import MonetaryAccount, Payment
from ynab import Account, Category

from helpers import get_bunq_connector, get_ynab_connector


class YnabAccount:
    account_info: Account
    payments: List[Payment]
    categories: List[Category]
    budget_id: int

    def __init__(self, acc: Account):
        self.account_info = acc

    def set_budget_id(self, id: int):
        self.budget_id = id
        return self


    def load_payments(self) -> "YnabAccount":
        self.payments = get_ynab_connector().get_payments(self.account_info.id)
        return self

    def load_categories(self) -> "YnabAccount":
        self.categories = get_ynab_connector().get_categories(self.account_info.id)
        return self
