from datetime import datetime
from typing import List

from bunq.sdk.model.core.bunq_model import BunqModel
from bunq.sdk.model.generated.endpoint import MonetaryAccount, Payment
from dateutil import parser
from helpers.helpers import get_bunq_connector


class BunqAccount:
    account_info: BunqModel
    transactions: List[Payment]

    def __init__(self, acc: MonetaryAccount):
        """
        Get the BunqModel of a MonetaryAccount, save it in self
        """
        self.account_info = acc.get_referenced_object()

    def load_transactions(self) -> "BunqAccount":
        transactions = get_bunq_connector().get_transactions(self.id)
        transactions = map(self.update_transaction, transactions)
        # sort by date asc
        self.transactions = sorted(transactions, key=lambda t: t.date)
        return self

    @staticmethod
    def update_transaction(t: Payment):
        """
        Update a bunq transaction: add date
        """
        t.date = parser.parse(t.created).date()
        return t

    @property
    def id(self):
        return self.account_info.id_

    @property
    def iban(self) -> str:
        """
        The iban is set as an alias
        """
        for alias in self.account_info.alias:
            if alias.type_ == 'IBAN':
                return alias.value
        raise ValueError(f"Cannot find iban of bunq model")
