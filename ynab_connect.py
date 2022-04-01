from datetime import datetime

import ynab
from ynab import Account, Category
from ynab.rest import ApiException

from cache import cache
from helpers import get_config


class Ynab:
    """
    Class responsible for any Ynab connections

    TODO:
        1. Recognise a transfer from 1 account to another, and create it as such
        2. Monkey path TransactionDetail
        3. Decide category based on payee name / iban
    """
    client = None

    def __init__(self):
        """
        Create client
        """
        self.client = self._get_client()

    def add_transaction(self, iban: str, payee: str, value: float, memo: str) -> bool:
        """
        Add a transaction. Called by the Bunq connector.

        === IMPORTANT ===
        todo: Monkey patch TransactionDetail class
         The class TransactionDetail of the Ynab sk is broken. If an exception occurs,
         manually comment out the two
         lines in __init__ of TransactionDetail where the properties
         transfer_account_id and import_id are set.


        :param iban: The iban on which the transaction was made. Will be translated to
        account_id. If this translation fails,
        throw exception
        :param payee: Name of the counterparty
        :param value: The value of the transaction, in EUR
        :param memo: Memo of the transaction
        :return: success
        """
        account = self._iban_to_account(iban)
        budget_id = account.budget_id
        category = self._decide_category(budget_id, payee)
        date = datetime.now()
        value = int(value * 1000)  # Convert to the right units
        flag_color = 'blue'
        transaction = ynab.SaveTransaction(account_id=account.id,
                                           # transfer_account_id=account.id,
                                           flag_color=flag_color,
                                           date=date,
                                           payee_name=payee,
                                           category_id=category.id,
                                           memo=memo,
                                           amount=value)
        api = ynab.TransactionsApi(self.client)
        response = api.create_transaction(budget_id,
                                          ynab.SaveTransactionWrapper(transaction))
        return True

    def _iban_to_account(self, iban: str) -> Account:
        """
        Convert an iban to an account id, by reading the 'Notes' on every account. The
        account is the one with the notes
        exactly matching the iban
        :param iban:
        :return: The account id
        """
        accounts = self._get_accounts()
        for account in accounts:
            if account.note == iban:
                return account
        raise Exception(f"No account found for iban {iban}")

    def _decide_category(self, budget_id, payee: str) -> Category:
        """
        Decide the category of a payment to a certain payee.
        For now: Always select the 'Inflow' category.
        Todo: decide based on payee name
        :param budget_id: The id of the budget we are creating a transcation for
        :param payee: The payee name
        :return: the category id
        """
        name = 'Inflow: Ready to Assign'
        for category in self._get_categories(budget_id):
            if category.name == name:
                return category
        raise Exception(f'No category found for budget {budget_id} and payee {payee}')

    def _get_client(self):
        """
        Create client, login using token, return client
        :return: client
        """
        token = get_config("ynab_token")
        configuration = ynab.Configuration()
        configuration.api_key['Authorization'] = token
        configuration.api_key_prefix['Authorization'] = 'Bearer'
        client = ynab.ApiClient(configuration)
        return client

    # Cache for 24 hours
    @cache(ttl=86400)
    def _get_categories(self, budget_id: str) -> []:
        """
        Get an array of all the categories of a budget
        :param budget_id: the budget
        :return: The categories
        """
        api = ynab.CategoriesApi(self.client)
        result = []
        try:
            for group in api.get_categories(budget_id).data.category_groups:
                for category in group.categories:
                    print(category.name)
                    result.append(category)
            return result
        except Exception as e:
            print(f"Exception when getting categories: {e}")

    @cache(ttl=86400)
    def _get_budgets(self) -> []:
        """
        Get an array of all the budgets
        :return: The budgets
        """
        api = ynab.BudgetsApi(self.client)
        try:
            budgets = api.get_budgets()
            return budgets.data.budgets
        except Exception as e:
            print(f"Exception when getting budgets: {e}")

    @cache(ttl=86400)
    def _get_accounts(self) -> []:
        """
        Get an array of all the accounts. Add property 'budget_id' to each account
        :return:  The accounts
        """
        api = ynab.AccountsApi(self.client)
        accounts = []
        for b in self._get_budgets():
            try:
                for account in api.get_accounts(b.id).data.accounts:
                    account.budget_id = b.id
                    accounts.append(account)
                accounts.extend(api.get_accounts(b))
            except ApiException as e:
                print(f"Exception when getting accounts: {e}")
        return accounts
