from typing import Dict

import mlflow
from sklearn.base import BaseEstimator
from sklearn.metrics import make_scorer
from sklearn.model_selection import GridSearchCV

from model_selection.classifier import Classifier
from model_selection.dataset import Dataset
from model_selection.experiments.base_experiment import BaseExperiment


class HyperparameterTuningExperiment(BaseExperiment):
    """
    An experiment to run hyperparam opt on a sklearn classifier

    ATTRIBUTES
    ----------
    clf: BaseEstimator
        The classifier to optimize
    space: Dict
        The parameter space to run a gridsearch over
    """

    clf: BaseEstimator
    grid_search: GridSearchCV
    space: Dict

    def __init__(self, clf: BaseEstimator, space: Dict):
        self.clf = clf
        self.space = space
        self.EXPERIMENT_NAME = f"Tuning{clf.__class__.__name__}Experiment"

    @BaseExperiment.register_mlflow
    def run(self, dataset: Dataset):
        mlflow.set_tag("budget", dataset.budget.id)
        score = make_scorer(self.score, greater_is_better=True)
        grid_search = GridSearchCV(self.clf, self.space, scoring=score)

        X_train, X_test, y_train, y_test = Classifier.split_to_sets(dataset)

        grid_search.fit(X_train, y_train)
        best_clf = grid_search.best_estimator_
        y_pred = best_clf.predict(X_test)
        score = self.score(y_test, y_pred)
        print(f"Score of best clf: {score}")
        mlflow.log_metric("cohens_kappa", score)
        self.select_best_run()
        self.grid_search = grid_search

    @classmethod
    def score(cls, y, y_pred):
        return Classifier.evaluate(y, y_pred)[-1]

    def select_best_run(self) -> None:
        self.best_run = mlflow.get_run(self.run_id)
