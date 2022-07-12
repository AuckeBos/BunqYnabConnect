import functools
from abc import abstractmethod
from typing import List, Callable, Tuple

import mlflow
import numpy as np
import pandas as pd
from bunq.sdk.model.generated.endpoint import Payment
from mlflow.entities import Run
from numpy.typing import NDArray
from sklearn.model_selection import ShuffleSplit

from model_selection.dataset import Dataset


class BaseExperiment:
    """
    Base class for experiments

    ATTRIBUTES
    ----------
    run_id: str
        The mlflow run id of the experiment. Set in decorator

    EXPERIMENT_NAME: str
        If set, use it as experiment name. Else use class name

    best_run: run
        The run that showed to contain the best model. Set in select_best_run()
    """

    run_id: str



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
        Of all children runs, select the one with the best performing model. Set on
        self.best_run
        """
        pass
