from typing import List, Tuple

import mlflow
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.metrics import accuracy_score, precision_score, f1_score, cohen_kappa_score
from sklearn.model_selection import ShuffleSplit
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from _classifier.dataset import Dataset


class Classifier:
    """
    A classifier trains can train a calssifier and evaluate it
    """

    def train(
        self,
        clf,
        data: Tuple[NDArray, NDArray, NDArray, NDArray],
    ):
        """
        Train a classifier, log to mlflow
        """
        clf_class = clf.__class__.__name__
        print(f"Training {clf_class}")
        with mlflow.start_run(nested=True, run_name=clf_class):
            X_train, X_test, y_train, y_test = data
            clf.fit(X_train, y_train)

            y_pred = clf.predict(X_test)
            y_pred = np.array(y_pred, int)
            y = np.array(y_test, int)
            acc, prec, f1, cohen_kappa = self._evaluate(y, y_pred)
            mlflow.log_metric("accuracy", acc)
            mlflow.log_metric("precision", prec)
            mlflow.log_metric("f1", f1)
            mlflow.log_metric("cohens_kappa", cohen_kappa)
            mlflow.sklearn.log_model(clf, clf_class)
        print(f"Done training {clf_class}")

    def _evaluate(
        self, y: NDArray, y_pred: NDArray
    ) -> Tuple[float, float, float, float]:
        """
        Evaluate: compute acc, prec, f1
        """
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average="micro", zero_division=0)
        f1 = f1_score(y, y_pred, average="micro", zero_division=0)
        cohen_kappa = cohen_kappa_score(y, y_pred)
        return accuracy, precision, f1, cohen_kappa
