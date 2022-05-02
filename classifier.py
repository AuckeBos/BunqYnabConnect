from typing import List, Tuple

from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, Payment
from ynab import Account

from bunq_connect import Bunq
from exceptions import YnabAccountNotFoundException
from ynab_connect import Ynab

bunq_connector = Bunq()
ynab_connector = Ynab()

def get_account_info() -> List[Tuple[MonetaryAccountBank, Account, List[Payment]]]:
    """
    Get a list, one item for each ynab account:
    - Bunq account
    - Ynab account
    - List of bunq payments
    """
    result = []
    bunq_data = bunq_connector.get_payments()
    for (bunq_account, payments) in bunq_data:
        iban = bunq_connector.iban_of_bunqmodel(bunq_account)
        try:
            ynab_account = ynab_connector.iban_to_account(iban)
            result.append((bunq_account, ynab_account, payments))
        except YnabAccountNotFoundException:
            continue
    return result


get_account_info()
