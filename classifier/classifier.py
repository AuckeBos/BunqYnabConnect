from typing import List, Tuple

from _bunq.bunq_account import BunqAccount
from helpers.helpers import get_bunq_connector, get_ynab_connector
from _ynab.ynab_account import YnabAccount


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
