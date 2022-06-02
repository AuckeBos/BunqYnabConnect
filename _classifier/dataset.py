from datetime import datetime
from typing import List, Tuple

import numpy as np
from bunq.sdk.model.generated.endpoint import Payment
from numpy.typing import NDArray
from ynab import TransactionDetail

from _bunq.bunq_account import BunqAccount
from _ynab.budget import Budget
from _ynab.ynab_account import YnabAccount
from helpers.cache import cache
from helpers.helpers import get_bunq_connector
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import CountVectorizer


class Dataset:
    """
    ATTRIBUTES
    ----------
    budget: Budget
        The budget to which this dataset belongs. We create one dataset (and thus one
        classifier) for each budget, as each budget has its own categories

    y_encoder: LabelEncoder
        The encoder that encodes ynab-transaction categories into integers (the labels)
    y: NDArray[int]
        Labels of the dataset: categories as integers

    X_encoder: CountVectorizer
        The encoder that encodes bunq-transaction 'Descriptions' into vectors, using BOW
    X: NDArray
        Items to classify. BOW representation of descriptions of bunq transactions



    """
    budget: Budget

    y_encoder: LabelEncoder
    y: NDArray[int]

    X_encoder: CountVectorizer
    X: NDArray

    def __init__(self, budget):
        """
        Save the budget as property, and load X, y
        """
        self.budget = budget
        self.X, self.y = self.load()

    def load(self):
        """
        Load the dataset.

        - First load all Ynab accounts in the budget, match them with Bunq accounts,
            and keep only the matched tuples.
        - For each tuple, load and match all transactions. Keep a list of all matched
            transactions
        - Each match is a bunq-ynab transaction combination. Build y by StringEncoding
            the 'category' of the ynab transaction. Build X by the BOW representation of
            the 'description' of the bunq transaction
        """
        accounts = self.load_accounts()
        transactions = self.load_transactions(accounts)
        X, y = self.load_dataset(transactions)
        return X, y

    # a day
    @cache(60 * 60 * 24)
    def load_accounts(self) -> List[Tuple[BunqAccount, YnabAccount]]:
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

    def load_transactions(self, accounts: List[Tuple[BunqAccount, YnabAccount]]) -> \
            List[Tuple[Payment, TransactionDetail]]:
        """
        For each account tuple, load and match all transactions. Return the complete list
        """
        transactions = []
        for b_account, y_account in accounts:
            transactions.extend(self.load_transactions_for_account(b_account, y_account))
        return transactions

    def load_transactions_for_account(self, b_account: BunqAccount,
                                      y_account: YnabAccount) -> \
            List[Tuple[Payment, TransactionDetail]]:
        """
        Load all transactions for both accounts. Match them on date and amount. Return
        list of matched tuples
        """
        b_transactions = b_account.transactions
        y_transactions = y_account.transactions
        matched_transactions = []
        for y_transaction in y_transactions:
            if self.is_invalid_ynab_transaction(y_transaction):
                continue
            for b_transaction in b_transactions:
                if self.transactions_match(y_transaction, b_transaction):
                    b_transactions.remove(b_transaction)
                    matched_transactions.append((b_transaction, y_transaction))
                    break
        return matched_transactions

    def load_dataset(self, transactions: List[Tuple[Payment, TransactionDetail]]):
        """
        Build y as the categories of YnabTransactions (as int)
        Build X as the descriptions of BunqTransactions (as BOW)
        """
        transactions = np.array(transactions)
        X = self.build_X(transactions[:, 0])
        y = self.build_y(transactions[:, 1])
        return X, y

    def build_X(self, transactions: List[Payment]) -> NDArray:
        """
        Build X, by BOWing all descriptions
        """
        descriptions = [t.description for t in transactions]
        encoder = CountVectorizer()
        encoder.fit(descriptions)
        X = encoder.transform(descriptions)
        self.X_encoder = encoder
        return X

    def build_y(self, transactions: List[TransactionDetail]) -> NDArray[int]:
        """
        Build y, by transforming category strings to ints
        """
        categories = [t.category_name for t in transactions]
        encoder = LabelEncoder()
        encoder.fit(categories)
        y = encoder.transform(categories)
        self.y_encoder = encoder
        return y

    @classmethod
    def is_invalid_ynab_transaction(cls, transaction: TransactionDetail) -> bool:
        """
        A ynab transaction is invalid if its amount is < 0.05, as this is very likely
        to be a test transaction
        """
        return abs(transaction.amount / 1000) <= 0.05

    @classmethod
    def transactions_match(cls, y: TransactionDetail, b: Payment) -> bool:
        """
        Match transactions on date and amount. Note that this might result in wrongly
        matched items, but we don't mind this for now
        """
        return y.date == b.date and round(y.amount / 1000, 2) == float(b.amount.value)
