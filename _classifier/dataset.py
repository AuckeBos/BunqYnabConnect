from datetime import datetime
from typing import List, Tuple

import numpy as np
import pandas as pd
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

    def load_transactions(
        self, accounts: List[Tuple[BunqAccount, YnabAccount]]
    ) -> List[Tuple[Payment, TransactionDetail]]:
        """
        For each account tuple, load and match all transactions. Return the complete list
        """
        transactions = []
        for b_account, y_account in accounts:
            transactions.extend(
                self.load_transactions_for_account(b_account, y_account)
            )
        return transactions

    def load_transactions_for_account(
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
        self.build_frame(transactions)
        # todo: frame to x and y, drop others
        X = self.build_X(transactions[:, 0])
        y = self.build_y(transactions[:, 1])
        return X, y

    def build_frame(self, transactions: NDArray[Tuple[Payment, TransactionDetail]]):
        # wip
        data = np.array(
            [
                [
                    bunq_t.description,
                    bunq_t.amount.value,
                    bunq_t.datetime.hour,
                    bunq_t.datetime.minute,
                    bunq_t.datetime.weekday(),
                    ynab_t.category_name,
                ]
                for bunq_t, ynab_t in transactions
            ]
        )
        descriptions = data[:, 0]
        categories = data[:, 5]

        description_encoder = CountVectorizer(lowercase=False)
        bag_of_words = np.array(
            description_encoder.fit_transform(descriptions).toarray()
        )
        self.description_encoder = description_encoder

        category_encoder = LabelEncoder()
        category_ints = category_encoder.fit_transform(categories)
        self.category_encoder = category_encoder

        # todo: add category ints
        all_data = np.concatenate((data, bag_of_words), axis=1)


        # todo: to pandas frame with col names
        # Merge both, drop 'description'
        features = pd.concat(
            [
                frame,
                pd.DataFrame(bow.toarray(), columns=encoder.get_feature_names()),
            ],
            axis=1,
        )

        labels = [t.category_name for t in transactions[:, 1]]

        # To frame
        frame = pd.DataFrame(features)

        # To frame
        frame = pd.DataFrame([])
        # Create bag of words of the descriptions
        encoder = CountVectorizer(lowercase=False)
        bow = encoder.fit_transform(frame["description"])
        self.X_encoder = encoder
        # Merge both, drop 'description'
        features = pd.concat(
            [
                frame,
                pd.DataFrame(bow.toarray(), columns=encoder.get_feature_names()),
            ],
            axis=1,
        )

        return None

    def build_X(self, transactions: List[Payment]) -> NDArray:
        """
        Build X
        """

        # Load all featuers
        features = [
            {
                "description": t.description,
                "amount": t.amount.value,
                "hour": t.datetime.hour,
                "minute": t.datetime.minute,
                "dayofweek": t.datetime.weekday(),
            }
            for t in transactions
        ]
        # To frame
        frame = pd.DataFrame(features)
        # Create bag of words of the descriptions
        encoder = CountVectorizer(lowercase=False)
        bow = encoder.fit_transform(frame["description"])
        self.X_encoder = encoder
        # Merge both, drop 'description'
        features = pd.concat(
            [
                frame,
                pd.DataFrame(bow.toarray(), columns=encoder.get_feature_names()),
            ],
            axis=1,
        )

        return None

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

    def un_transform_set(self, X: NDArray, y: NDArray) -> Tuple[NDArray, NDArray]:
        return self.un_transform_X(X), self.un_transform_y(y)

    def un_transform_X(self, X: NDArray) -> NDArray:
        return np.array([" ".join(x) for x in self.X_encoder.inverse_transform(X)])

    def un_transform_y(self, y: NDArray) -> NDArray:
        return self.y_encoder.inverse_transform(y)
