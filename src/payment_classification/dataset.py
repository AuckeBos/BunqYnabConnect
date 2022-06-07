from typing import List, Tuple

import numpy as np
import pandas as pd
from bunq.sdk.model.generated.endpoint import Payment
from numpy.typing import NDArray
from ynab import TransactionDetail

from bunq_ynab_connector._bunq.bunq_account import BunqAccount
from bunq_ynab_connector._ynab.budget import Budget
from bunq_ynab_connector._ynab.ynab_account import YnabAccount
from helpers.cache import cache
from helpers.helpers import get_bunq_connector
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


class Dataset:
    """
    ATTRIBUTES
    ----------
    budget: Budget
        The budget to which this dataset belongs. We create one dataset (and thus one
        classifier) for each budget, as each budget has its own categories

    frame: pd.DataFrame
        All data that is used, as frame

    category_encoder: LabelEncoder
        The encoder that encodes ynab-transaction categories into integers (the labels)
    y: pd.DataFrame
        Labels of the dataset: categories as integers

    description_encoder: CountVectorizer
        The encoder that encodes bunq-transaction 'Descriptions' into vectors, using BOW
    X: pd.DataFrame
        Items to classify. BOW representation of descriptions of bunq transactions



    """

    budget: Budget

    frame: pd.DataFrame

    category_encoder: LabelEncoder
    y: pd.DataFrame

    description_encoder: CountVectorizer
    X: pd.DataFrame

    def __init__(self, budget):
        """
        Save the budget as property, and load X, y
        """
        self.budget = budget
        self.X, self.y, self.frame = self._load()

    def _load(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        accounts = self._load_accounts()
        transactions = self._load_transactions(accounts)
        return self._load_dataset(transactions)

    def feature_names(self) -> List[str]:
        return [f"description ({self.description_encoder.__class__.__name__})"] + [
            f for f in self.X.columns.tolist() if "word_" not in f
        ]

    def un_transform_set(
        self, X: pd.DataFrame, y: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        return self.un_transform_X(X), self.un_transform_y(y)

    def un_transform_X(self, X: pd.DataFrame) -> pd.DataFrame:
        return np.array(
            [" ".join(x) for x in self.description_encoder.inverse_transform(X)]
        )

    def un_transform_y(self, y: NDArray) -> NDArray:
        return self.category_encoder.inverse_transform(y)

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
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Build y as the categories of YnabTransactions (as int)
        Build X as the descriptions of BunqTransactions (as BOW)
        """
        transactions = np.array(transactions)
        frame = self._build_frame(transactions)
        X = frame.copy().drop(columns=["description", "category_name", "category"])
        # X = frame.copy().drop(columns=["description", "category_name"])
        y = frame.copy()[["category"]]
        return X, y, frame

    def _build_frame(
        self, transactions: NDArray[Tuple[Payment, TransactionDetail]]
    ) -> pd.DataFrame:
        # Load all data
        data = np.array(
            [
                [
                    bunq_t.description,
                    float(bunq_t.amount.value),
                    int(bunq_t.datetime.hour),
                    int(bunq_t.datetime.minute),
                    int(bunq_t.datetime.weekday()),
                    ynab_t.category_name,
                ]
                for bunq_t, ynab_t in transactions
            ],
            dtype="object",
        )
        # Convert descriptions into bag of words
        descriptions = data[:, 0]
        description_encoder = TfidfVectorizer(lowercase=False)
        bag_of_words = np.array(
            description_encoder.fit_transform(descriptions).toarray()
        )
        self.description_encoder = description_encoder

        # Convert categories into ints
        categories = data[:, 5]
        category_encoder = LabelEncoder()
        category_ints = category_encoder.fit_transform(categories)
        category_ints = np.reshape(category_ints, (category_ints.shape[0], 1))
        self.category_encoder = category_encoder
        # Merge into one array, and convert to frame
        data = np.concatenate((data, category_ints, bag_of_words), axis=1)
        return pd.DataFrame(
            data,
            columns=[
                "description",
                "amount",
                "hour",
                "minute",
                "weekday",
                "category_name",
                "category",
                *[f"word_{w}" for w in description_encoder.get_feature_names()],
            ],
        )

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
