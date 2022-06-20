from typing import Tuple, List

import mlflow
import numpy as np
from bunq.sdk.model.generated.endpoint import Payment
from numpy.typing import NDArray
from sklearn.metrics import accuracy_score, precision_score, f1_score, cohen_kappa_score
from sklearn.model_selection import ShuffleSplit
from sklearn.pipeline import Pipeline

from helpers.helpers import object_to_mlflow, build_pipeline
from payment_classification.dataset import Dataset
from payment_classification.feature_extractor import FeatureExtractor


class Classifier:
    """
    A classifier trains can train a sklearn classifier and evaluate it
    ATTRIBUTES
    ----------
    RANDOM_STATE: int
        seed
    TEST_SIZE = 0.1
        Test size (percentage)
    """

    RANDOM_STATE = 1337
    TEST_SIZE = 0.1

    def train_evaluate(
        self,
        clf,
        dataset: Dataset,
    ):
        """
        Train a classifier, log to mlflow
        """
        clf_class = clf.__class__.__name__

        with mlflow.start_run(nested=True, run_name=clf_class):
            mlflow.set_tag("_estimator_class", clf_class)
            object_to_mlflow(dataset.category_encoder, "LabelTransformer")
            X_train, X_test, y_train, y_test = self.split_to_sets(dataset)
            pipeline = build_pipeline(clf)
            pipeline.fit(X_train, y_train)
            mlflow.log_text(
                ",".join(pipeline["feature_extractor"].feature_names()), "features.txt"
            )
            y_pred = pipeline.predict(X_test)
            y_pred = np.array(y_pred, int)

            self.evaluate(y_test, y_pred)
            mlflow.sklearn.log_model(pipeline, clf_class)

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

    @classmethod
    def split_to_idx(cls, X: NDArray[Payment]) -> Tuple[List[int], List[int]]:
        """
        Split a dataset into 1 train,test split, return idx
        """
        splitter = ShuffleSplit(
            n_splits=1, test_size=cls.TEST_SIZE, random_state=cls.RANDOM_STATE
        )
        train_idx, test_idx = next(splitter.split(X))
        return train_idx, test_idx

    @classmethod
    def split_to_sets(
        cls, dataset: Dataset
    ) -> Tuple[NDArray[Payment], NDArray[Payment], NDArray, NDArray]:
        """
        Split a dataset into 1 train,test split, return sets
        """
        X, y = dataset.X, dataset.y
        train_idx, test_idx = cls.split_to_idx(X)
        X_train, X_test, y_train, y_test = (
            X[train_idx],
            X[test_idx],
            y[train_idx],
            y[test_idx],
        )
        return X_train, X_test, y_train, y_test
