from typing import List, Tuple

import matplotlib
import mlflow
import numpy as np
from matplotlib import pyplot as plt
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, precision_score, f1_score
from sklearn.model_selection import train_test_split, ShuffleSplit

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
        self._load_datasets()

    def train(self):
        for dataset in self.datasets:
            self._train_one(dataset)

    def _train_one(self, dataset: Dataset):
        mlflow.set_experiment('DecisionTreeClassifier')
        mlflow.sklearn.autolog()
        with mlflow.start_run():
            X, y = dataset.X, dataset.y
            train_idx, test_idx = self._split(X)

            X_train, X_test, y_train, y_test = (
                X.iloc[train_idx],
                X.iloc[test_idx],
                y.iloc[train_idx],
                y.iloc[test_idx],
            )

            clf = tree.DecisionTreeClassifier()
            clf.fit(X_train, y_train)

            y_pred = clf.predict(X_test)
            y_pred = np.array(y_pred, int)
            y = np.array(y_test, int)
            acc, prec, f1 = self._evaluate(y, y_pred)
            mlflow.log_metric('accuracy', acc)
            mlflow.log_metric('precision', prec)
            mlflow.log_metric('f1', f1)
            mlflow.sklearn.log_model(clf, 'DecisionTreeClassifier')

    @classmethod
    def _split(cls, X: pd.DataFrame) -> Tuple[List[int], List[int]]:
        """
        Split a dataset into 1 train,test split, return idx
        """
        splitter = ShuffleSplit(
            n_splits=1, test_size=cls.TEST_SIZE, random_state=cls.RANDOM_STATE
        )
        train_idx, test_idx = next(splitter.split(X))
        return train_idx, test_idx

    def _evaluate(self, y: NDArray, y_pred: NDArray) -> Tuple[float, float, float]:
        """
        Evaluate: compute acc, prec, f1
        """
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average='micro')
        f1 = f1_score(y, y_pred, average='micro')
        return accuracy, precision, f1

    def _load_datasets(self):
        datasets = []
        budgets = get_ynab_connector().get_budgets()
        for budget in budgets:
            if budget.budget_info.name != "Aucke":
                continue
            datasets.append(Dataset(budget.load_info()))
        self.datasets = datasets
