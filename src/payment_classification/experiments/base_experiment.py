import functools
from abc import abstractmethod
from typing import List, Callable, Tuple

import mlflow
import numpy as np
import pandas as pd
from mlflow.entities import Run
from sklearn.model_selection import ShuffleSplit

from payment_classification.dataset import Dataset


class BaseExperiment:
    """
    Base class for experiments

    ATTRIBUTES
    ----------
    run_id: str
        The mlflow run id of the experiment. Set in decorator

    RANDOM_STATE: int
        seed
    TEST_SIZE = 0.1
        Test size (percentage)

    EXPERIMENT_NAME: str
        If set, use it as experiment name. Else use class name

    best_run: run
        The run that showed to contain the best model. Set in select_best_run()
    """

    run_id: str

    RANDOM_STATE = 1337
    TEST_SIZE = 0.1

    EXPERIMENT_NAME: str = None

    best_run: Run

    @staticmethod
    def register_mlflow(func: Callable) -> Callable:
        """
        Decorator function. Sets the current experiment based on the class name.
        Starts a run before running the function, ends it after
        Parameters
        ----------
        func: callable
            The function to run
        """

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):  # type: ignore
            mlflow.set_experiment(self.experiment_name)
            mlflow.sklearn.autolog()
            with mlflow.start_run(run_name="experiment") as run:
                self.run_id = run.info.run_id
                return func(self, *args, **kwargs)

        return wrapper

    @classmethod
    def split_to_idx(cls, X: pd.DataFrame) -> Tuple[List[int], List[int]]:
        """
        Split a dataset into 1 train,test split, return idx
        """
        splitter = ShuffleSplit(
            n_splits=1, test_size=cls.TEST_SIZE, random_state=cls.RANDOM_STATE
        )
        train_idx, test_idx = next(splitter.split(X))
        return train_idx, test_idx

    @classmethod
    def split_to_sets(cls, X: pd.DataFrame, y: pd.DataFrame, as_numpy: bool = True):
        """
        Split a dataset into 1 train,test split, return sets
        @param bool as_numpy: If true, return as np array, else as dataframe
        """
        train_idx, test_idx = cls.split_to_idx(X)
        X_train, X_test, y_train, y_test = (
            X.iloc[train_idx],
            X.iloc[test_idx],
            y.iloc[train_idx],
            y.iloc[test_idx],
        )
        if as_numpy:
            X_train, X_test, y_train, y_test = (
                np.array(X_train),
                np.array(X_test),
                np.array(y_train, int).reshape((len(train_idx),)),
                np.array(y_test, int).reshape((len(test_idx),)),
            )
        return X_train, X_test, y_train, y_test

    @property
    def experiment_name(self) -> str:
        return self.EXPERIMENT_NAME or self.__class__.__name__

    @abstractmethod
    def run(self, dataset: Dataset) -> None:
        """
        Run the experiment on a dataset
        """
        pass

    @abstractmethod
    def select_best_run(self) -> None:
        """
        Of all children runs, select the one with the best performing model
        """
        pass
