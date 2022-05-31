from _bunq.bunq_account import BunqAccount
from _ynab.budget import Budget
from _ynab.ynab_account import YnabAccount
from helpers.helpers import get_bunq_connector


class Dataset:
    budget: Budget

    def __init__(self, budget):
        self.budget = budget
        self.load()

    def load(self):
        accounts = self.load_accounts()
        for y_account, b_account in accounts:
            self.load_transactions(y_account, b_account)

    def load_accounts(self):
        result = []
        ynab_accounts = self.budget.accounts
        bunq_accounts = get_bunq_connector().get_bunq_accounts()
        for y_account in ynab_accounts:
            iban = y_account.iban
            for b_account in bunq_accounts:
                if b_account.iban == iban:
                    y_account.load_transactions()
                    b_account.load_transactions()
                    result.append((y_account, b_account))
                    break
        return result

    def load_transactions(self, y_account: YnabAccount,  b_account: BunqAccount):
        for y_transaction in y_account.transactions:
            for b_transaction in b_account.transactions:
                test = ''
