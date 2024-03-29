from datetime import datetime
from typing import Dict

import requests

import ynab
from ynab import Account, Category, TransactionDetail, SubTransaction
from ynab.rest import ApiException

from bunq_ynab_connector._ynab.ynab_account import YnabAccount
from helpers.cache import cache
from helpers.exceptions import YnabAccountNotFoundException
from helpers.helpers import *
from bunq_ynab_connector._ynab.budget import Budget


class Ynab:
    """
    Class responsible for any _ynab connections

    TODO:
        1. Recognise a transfer from 1 account to another, and create it as such
        3. Decide category based on payee name / iban
    """
    client = None

    def __init__(self):
        """
        Create client
        """
        self._monkey_patch_ynab()
        self.client = self._get_client()

    def add_transaction(self, iban: str, payee: str, value: float, memo: str,
                        raw_data: Dict) -> bool:
        """
        Add a transaction. Called by the _bunq connector.
        :param iban: The iban on which the transaction was made. Will be translated to
        account_id. If this translation fails,
        throw exception
        :param payee: Name of the counterparty
        :param value: The value of the transaction, in EUR
        :param memo: Memo of the transaction
        :param raw_data: The raw transaction data, used for category prediction
        :return: success
        """
        account = self.iban_to_account(iban)
        budget_id = account.budget_id
        category = self._decide_category(budget_id, raw_data)
        date = datetime.datetime.now()
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

    def iban_to_account(self, iban: str) -> YnabAccount:
        """
        Convert an iban to an account id, by reading the 'Notes' on every account. The
        account is the one with the notes
        exactly matching the iban
        :param iban:
        :return: The account id
        """
        accounts = self.get_ynab_accounts()
        for account in accounts:
            if account.iban == iban:
                return account
        raise YnabAccountNotFoundException(f"No account found for iban {iban}")

    @cache(ttl=86400)
    def get_budgets(self) -> List[Budget]:
        """
        Get an array of all the budgets
        :return: The budgets
        """
        api = ynab.BudgetsApi(self.client)
        try:
            budgets = api.get_budgets()
            return [Budget(budget_info) for budget_info in budgets.data.budgets]
        except Exception as e:
            print(f"Exception when getting budgets: {e}")
            raise e

    @cache(ttl=86400)
    def get_ynab_accounts(self) -> List[YnabAccount]:
        """
        Get an array of all the accounts. Add property 'budget_id' to each account
        :return:  The accounts
        """
        api = ynab.AccountsApi(self.client)
        accounts = []
        for b in self.get_budgets():
            try:
                for account in api.get_accounts(b.id).data.accounts:
                    accounts.append(YnabAccount(account).set_budget_id(b.id))
            except ApiException as e:
                print(f"Exception when getting accounts: {e}")
                raise e
        return accounts

    # Cache for 24 hours
    @cache(ttl=86400)
    def get_categories(self, budget_id: str) -> []:
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
                    result.append(category)
            return result
        except Exception as e:
            print(f"Exception when getting categories: {e}")

    def get_transactions(self, account: YnabAccount) -> List[TransactionDetail]:
        """
        Get an array of all the transactions of an account
        """
        api = ynab.TransactionsApi(self.client)
        return api.get_transactions_by_account(account.budget_id,
                                               account.id).data.transactions

    def _decide_category(self, budget_id, raw_data: Dict) -> Category:
        """
        Decide the category of a payment:
        - Load the url of the server that should host a model that can predict
        transactions for this budget
        - Post to the server
        - If fail, use backup, else prediction
        - Convert category string to category
        :param budget_id: The id of the budget we are creating a transcation for
        :param raw_data: The raw transaction data
        :return: the category
        """
        # todo: Make sure the classifier can never predict invalid labels
        invalid_categories = ['Split (Multiple Categories)...']
        try:
            url = get_prediction_url(budget_id)
            category_name = requests.post(url, json = raw_data).text
            log(f"Category {category_name} was predicted")
            if category_name in invalid_categories:
                raise Exception(f"Category {category_name} is invalid, falling back to InFlow..")
        except Exception as e:
            log(f"Category could not be predicted: {e}")
            category_name = 'Inflow: Ready to Assign'
        for category in self.get_categories(budget_id):
            if category.name == category_name:
                return category
        raise Exception(f'No category found for budget {budget_id} and category {category_name}')

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

    def _monkey_patch_ynab(self):
        """
        Some ynab classes have bugs. Override the functions with those bugs here,
        to prevent exceptions.

        Some classes have som bugged attributes.
        Their value are sometimes None, while the class doesn't allow it to be none.
        In such cases, an exception would occur if the class is instantiated. To
        prevent this, we override the set() functions of those properties. The new
        function definition simply sets the value, skipping the 'raise exception if
        value is None' part.

        """

        bugged_attributes = ['type', 'transfer_account_id', 'import_id', 'flag_color',
                             'category_id', 'memo', 'payee_id', 'payee_name']

        # Fix TransactionDetail
        for attribute in bugged_attributes:
            def fixed_setter(self, value):
                setattr(self, f'_{attribute}', value)

            setattr(TransactionDetail, attribute, fixed_setter)

        # Fix SubTransaction
        bugged_attributes = ['payee_id', 'transfer_account_id', 'memo']
        for attribute in bugged_attributes:
            def fixed_setter(self, value):
                setattr(self, f'_{attribute}', value)

            setattr(SubTransaction, attribute, fixed_setter)

        # Fix Account
        bugged_attributes = ['type']
        for attribute in bugged_attributes:
            def fixed_setter(self, value):
                setattr(self, f'_{attribute}', value)

            setattr(Account, attribute, fixed_setter)
