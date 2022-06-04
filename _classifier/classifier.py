from typing import List, Tuple

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from _bunq.bunq_account import BunqAccount
from _classifier.dataset import Dataset
from helpers.helpers import get_bunq_connector, get_ynab_connector
from _ynab.ynab_account import YnabAccount
from sklearn import tree
import pandas as pd


class Classifier:
    """
    A classifier trains one DecisionTreeClassifier for each dataset. There is one
    dataset created for each Ynab budget, as each budget has its own categories

    ATTRIBUTES
    ----------
    datasets: List[Dataset]
        List of datasets, created on init


    RANDOM_STATE: int
        Seed


    TEST_SIZE: float
        Percentage test size
    """

    datasets: List[Dataset]
    RANDOM_STATE = 1337
    TEST_SIZE = 0.1

    def __init__(self):
        self.load_datasets()
        self.build_classifiers()

    def load_datasets(self):
        datasets = []
        budgets = get_ynab_connector().get_budgets()
        for budget in budgets:
            if budget.budget_info.name != "Aucke":
                continue
            datasets.append(Dataset(budget.load_info()))
        self.datasets = datasets

    def build_classifiers(self):
        for dataset in self.datasets:
            X, y = dataset.X, dataset.y
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=self.TEST_SIZE, random_state=self.RANDOM_STATE
            )
            clf = tree.DecisionTreeClassifier()
            clf.fit(X_train, y_train)

            y_pred = clf.predict(X_test)
            acc = accuracy_score(y_test, y_pred)

            predictions = np.array(
                [
                    *dataset.un_transform_set(X_test, y_test),
                    dataset.un_transform_y(y_pred),
                ]
            ).transpose()

            frame = pd.DataFrame(predictions, columns = ['X', 'y', 'y_pred'])

            test = ""
