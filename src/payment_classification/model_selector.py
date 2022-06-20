import os

import mlflow.sklearn
import numpy as np
from sklearn.base import BaseEstimator
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
import pickle
from bunq_ynab_connector._ynab.budget import Budget
from helpers.helpers import log, build_pipeline
from payment_classification.classifier import Classifier
from payment_classification.dataset import Dataset
from payment_classification.experiments.classifier_selection_experiment import (
    ClassifierSelectionExperiment,
)
from payment_classification.experiments.hyperparameter_tuning_experiment import (
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

    def select(self):
        """
        Select the best model:
        - Select the best classifier
        - Select the best parameters for it
        - Train it on the full set
        - Save to filesystem

        Todo: also need transformers to transform x and y on predict
        """
        budget_id = self.dataset.budget.id
        log(f"Selecting the best model for budget {budget_id}")
        cls_name = self._select_best_classifier_class()
        log(f"The best classifier is {cls_name}")
        parameters = self._select_best_parameters(cls_name)
        log(f"The best parameters are {parameters}")
        classifier = self._fully_train_best_classifier(cls_name, parameters)
        dir = f"{budget_id}"
        # os.makedirs(dir)
        path = f"model"
        mlflow.sklearn.log_model(
            classifier,
            artifact_path=path,
            registered_model_name=f"Classifier for Budget {budget_id}",
        )

        # with open(path, "wb+") as f:
        #     pickle.dump(classifier, f)
        log(f"Classifier saved in {path}")

    def _select_best_classifier_class(self) -> str:
        """
        Select the best estimator class, by running the ClassifierSelectionExperiment
        Returns
        -------
        The class name
        """
        experiment = ClassifierSelectionExperiment()
        experiment.run(self.dataset)

        cls = experiment.best_run.data.tags["_estimator_class"]
        return cls

    def _select_best_parameters(self, cls_name: str) -> dict:
        """
        Select the best set of hyperparameters for the classifier for the budget
        """
        hyper_space = self.HYPERPARAMETER_SPACES[cls_name]

        experiment = HyperparameterTuningExperiment(eval(cls_name)(), hyper_space)
        experiment.run(self.dataset)
        params = experiment.grid_search.best_params_
        return params

    def _fully_train_best_classifier(
        self, cls_name: str, hyperparameters: dict
    ) -> BaseEstimator:
        """
        After the best classifier and its best params have been selected, create a new
        instance of the classifier with the best params, train it on the full dataset,
        return the trained classifier
        """
        classifier = eval(cls_name)(**hyperparameters)
        pipeline = build_pipeline(classifier)

        X = np.array(self.dataset.X)
        y = np.array(self.dataset.y, int)

        pipeline.fit(X, y)
        return pipeline
