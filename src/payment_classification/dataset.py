from typing import List, Tuple

import numpy as np
import pandas as pd
from bunq.sdk.model.generated.endpoint import Payment
from numpy.typing import NDArray
from sklearn.preprocessing import LabelEncoder
from ynab import TransactionDetail

from bunq_ynab_connector._bunq.bunq_account import BunqAccount
from bunq_ynab_connector._ynab.budget import Budget
from bunq_ynab_connector._ynab.ynab_account import YnabAccount
from helpers.cache import cache
from helpers.helpers import get_bunq_connector


class Dataset:
    """
    ATTRIBUTES
    ----------
    budget: Budget
        The budget to which this dataset belongs. We create one dataset (and thus one
        classifier) for each budget, as each budget has its own categories

    category_encoder: LabelEncoder
        The encoder that encodes ynab-transaction categories into integers (the labels)
    y: NDArray
        Labels of the dataset: categories as integers

    X: NDArray[Payment]
        Items to classify. Will be transformed into a frame using the FeatureExtractor
    """

    budget: Budget

    category_encoder: LabelEncoder
    y: NDArray

    X: NDArray[Payment]

    def __init__(self, budget):
        """
        Save the budget as property, and load X, y
        """
        self.budget = budget
        self.X, self.y = self._load()

    def _load(self) -> Tuple[NDArray[Payment], NDArray]:
        """
        Load the dataset.

        - First load all Ynab accounts in the budget, match them with Bunq accounts,
            and keep only the matched tuples.
        - For each tuple, load and match all transactions. Keep a list of all matched
            transactions
        - Each match is a bunq-ynab transaction combination. Build y by StringEncoding
            the 'category' of the ynab transaction.
        """
        accounts = self._load_accounts()
        transactions = self._load_transactions(accounts)
        return self._load_dataset(transactions)

    # a day
    @cache(60 * 60 * 24)
    def _load_accounts(self) -> List[Tuple[BunqAccount, YnabAccount]]:
        """
        Load Bunq-Ynab account tuples, by matching YnabAccount descriptions with
        BunqAccount ibans
        """
        result = []
        ynab_accounts = self.budget.accounts
        bunq_accounts = get_bunq_connector().get_bunq_accounts()
        for y_account in ynab_accounts:
            iban = y_account.iban
            for b_account in bunq_accounts:
                if b_account.iban == iban:
                    y_account.load_transactions()
                    b_account.load_transactions()
                    result.append((b_account, y_account))
                    break
        return result

    def _load_transactions(
        self, accounts: List[Tuple[BunqAccount, YnabAccount]]
    ) -> List[Tuple[Payment, TransactionDetail]]:
        """
        For each account tuple, load and match all transactions. Return the complete list
        """
        transactions = []
        for b_account, y_account in accounts:
            transactions.extend(
                self._load_transactions_for_account(b_account, y_account)
            )
        return transactions

    def _load_transactions_for_account(
        self, b_account: BunqAccount, y_account: YnabAccount
    ) -> List[Tuple[Payment, TransactionDetail]]:
        """
        Load all transactions for both accounts. Match them on date and amount. Return
        list of matched tuples
        """
        b_transactions = b_account.transactions
        y_transactions = y_account.transactions
        matched_transactions = []
        for y_transaction in y_transactions:
            if self._is_invalid_ynab_transaction(y_transaction):
                continue
            for b_transaction in b_transactions:
                if self._transactions_match(y_transaction, b_transaction):
                    b_transactions.remove(b_transaction)
                    matched_transactions.append((b_transaction, y_transaction))
                    break
        return matched_transactions

    def _load_dataset(
        self, transactions: List[Tuple[Payment, TransactionDetail]]
    ) -> Tuple[NDArray[Payment], NDArray]:
        """
        Build y as the categories of YnabTransactions (as int)
        Build X as simply the list of Transactions. The feature extraction is done
        through the FeatureExtractor
        """
        transactions = np.array(transactions)

        categories = [t.category_name for t in transactions[:, 1]]
        category_encoder = LabelEncoder()
        y = category_encoder.fit_transform(categories)
        self.category_encoder = category_encoder
        X = transactions[:, 0]
        return X, y

    @classmethod
    def _is_invalid_ynab_transaction(cls, transaction: TransactionDetail) -> bool:
        """
        A ynab transaction is invalid if its amount is < 0.05, as this is very likely
        to be a test transaction
        """
        return abs(transaction.amount / 1000) <= 0.05

    @classmethod
    def _transactions_match(cls, y: TransactionDetail, b: Payment) -> bool:
        """
        Match transactions on date and amount. Note that this might result in wrongly
        matched items, but we don't mind this for now
        """
        return y.date == b.date and round(y.amount / 1000, 2) == float(b.amount.value)
