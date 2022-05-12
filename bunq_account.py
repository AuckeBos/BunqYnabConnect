from typing import List

from bunq.sdk.model.core.bunq_model import BunqModel
from bunq.sdk.model.generated.endpoint import MonetaryAccount, Payment




class BunqAccount:
    account_info: BunqModel
    payments: List[Payment]

    def __init__(self, acc: MonetaryAccount):
        """
        Get the BunqModel of a MonetaryAccount, save it in self
        """
        self.account_info = acc.get_referenced_object()

    def load_payments(self) -> "BunqAccount":
        from helpers import get_bunq_connector
        id = self.account_info.id_
        self.payments = get_bunq_connector().get_payments(id)
        return self
