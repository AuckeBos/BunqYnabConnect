from typing import List

from bunq.sdk.model.generated.endpoint import Payment
from ynab import Account, Category

from helpers.helpers import get_ynab_connector


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
