from typing import Tuple

import mlflow
import numpy as np
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, precision_score, f1_score, cohen_kappa_score


class Classifier:
    """
    A classifier trains can train a sklearn classifier and evaluate it
    """

    def train_evaluate(
        self,
        clf,
        data: Tuple[NDArray, NDArray, NDArray, NDArray],
    ):
        """
        Train a classifier, log to mlflow
        """
        clf_class = clf.__class__.__name__
        with mlflow.start_run(nested=True, run_name=clf_class):
            X_train, X_test, y_train, y_test = data
            clf.fit(X_train, y_train)

            y_pred = clf.predict(X_test)
            y_pred = np.array(y_pred, int)
            y = np.array(y_test, int)
            self.evaluate(y, y_pred)
            mlflow.sklearn.log_model(clf, clf_class)

    @classmethod
    def evaluate(
        cls, y: NDArray, y_pred: NDArray, log: bool = True
    ) -> Tuple[float, float, float, float]:
        """
        Evaluate: compute acc, prec, f1, cohens_kappa
        Parameters
        ----------
        log: bool
            If true, log params to mlflow
        """
        accuracy = accuracy_score(y, y_pred)
        precision = precision_score(y, y_pred, average="micro", zero_division=0)
        f1 = f1_score(y, y_pred, average="micro", zero_division=0)
        cohen_kappa = cohen_kappa_score(y, y_pred)
        if log:
            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("f1", f1)
            mlflow.log_metric("cohens_kappa", cohen_kappa)
        return accuracy, precision, f1, cohen_kappa
