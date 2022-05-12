from typing import List, Tuple

from bunq.sdk.model.generated.endpoint import MonetaryAccountBank, Payment
from ynab import Account

from bunq_account import BunqAccount
from bunq_connect import Bunq
from cache import cache
from exceptions import YnabAccountNotFoundException
from helpers import get_bunq_connector, get_ynab_connector
from ynab_account import YnabAccount
from ynab_connect import Ynab


# @cache(60 * 60 * 24)
def get_account_info() -> List[Tuple[BunqAccount, YnabAccount]]:
    """
    Get a list of tuples, each item:
    - A BunqAccount (with payments)
    - A YnabAccount (with payments)
    """
    ynab_accounts = [account.load_categories().load_payments() for account in
                     get_ynab_connector().get_ynab_accounts()]
    bunq_accounts = [account.load_payments() for account in
                     get_bunq_connector().get_ynab_accounts()]
    test = ''


info = get_account_info()
test = ''
