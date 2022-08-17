from typing import Any, Dict, Tuple

from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from helpers.helpers import log
from model_selection.dataset import Dataset
from model_selection.experiments.classifier_selection_experiment import (
    ClassifierSelectionExperiment,
)
from model_selection.experiments.hyperparameter_tuning_experiment import (
    HyperparameterTuningExperiment,
)


class ModelSelector:
    """
    Class the is able to select and train the best model for a specific budget.
    To select a model, perform the following steps:
    - Run a ClassifierSelectionExperiment, to find the classifier that seems to work
    best for the budget
    - For that classifier, run a HyperparameterTuningExperiment, to find the best set
    of hyperparameters for that classifier for that budget
    - Train the selected classifier with the selected hyperparameters on the full
    dataset, save the trained model. This model is ready to be served for
    classification purposes
    """

    dataset: Dataset

    HYPERPARAMETER_SPACES = {
        KNeighborsClassifier().__class__.__name__: {
            "n_neighbors": [3, 5, 10, 25],
            "algorithm": ["auto", "ball_tree", "kd_tree", "brute"],
        },
        SVC().__class__.__name__: {
            "C": [0.5, 1, 2],
            "kernel": ["linear", "poly", "rbf", "sigmoid"],
            "gamma": ["scale", "auto", 3],
            "shrinking": [True, False],
        },
        # DecisionTreeClassifier().__class__.__name__: {
        #     "criterion": ["gini", "entropy", "log_loss"],
        #     "splitter": ["best", "random"],
        #     "max_depth": [3, 5, 10, 20, 50, None],
        # },
        DecisionTreeClassifier().__class__.__name__: {
            "max_depth": [
                3,
                5,
            ],
        },
        RandomForestClassifier().__class__.__name__: {
            "n_estimators": [100, 1000, 2500],
            "criterion": ["gini", "entropy", "log_loss"],
            "max_depth": [5, 10, 20, 50, 250, None],
        },
        MLPClassifier().__class__.__name__: {
            "max_iter": [1000],
            "activation": ["tanh", "relu"],
            "solver": ["lbfgs", "sgd"],
            "alpha": [0.01, 0.1, 1],
            "learning_rate": ["contant", "adaptive"],
            "learning_rate_init": [0.01, 0.001, 0.0001],
        },
        AdaBoostClassifier().__class__.__name__: {"n_estimators": [25, 50, 100, 250]},
        GaussianNB().__class__.__name__: {},
    }

    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    def select(self) -> Tuple[str, Dict[str, Any]]:
        """
        Select the best model:
        - Select the best classifier
        - Select the best parameters for it
        Return classifier class and hyper parameter set
        """
        log(f"Selecting the best classifier")
        cls_name = self._select_best_classifier_class()
        log(f"The best classifier is {cls_name}")
        parameters = self._select_best_parameters(cls_name)
        log(f"The best parameters are {parameters}")

        return cls_name, parameters

    def _select_best_classifier_class(self) -> str:
        """
        Select the best estimator class, by running the ClassifierSelectionExperiment
        Returns
        -------
        The class name
        """
        experiment = ClassifierSelectionExperiment()
        experiment.run(self.dataset)

        cls = experiment.best_run.data.tags["estimator_class"]
        cls_name = cls.split(".")[-1]
        return cls_name

    def _select_best_parameters(self, cls_name: str) -> dict:
        """
        Select the best set of hyperparameters for the classifier for the budget
        """
        hyper_space = self.HYPERPARAMETER_SPACES[cls_name]

        experiment = HyperparameterTuningExperiment(eval(cls_name)(), hyper_space)
        experiment.run(self.dataset)
        params = experiment.grid_search.best_params_
        return params