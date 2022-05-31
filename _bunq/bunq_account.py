from typing import List

from bunq.sdk.model.core.bunq_model import BunqModel
from bunq.sdk.model.generated.endpoint import MonetaryAccount, Payment

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
        self.transactions = get_bunq_connector().get_transactions(self.id)
        return self

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
