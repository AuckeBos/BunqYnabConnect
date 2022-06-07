from typing import Dict

import mlflow
from sklearn.base import BaseEstimator
from sklearn.metrics import make_scorer
from sklearn.model_selection import GridSearchCV

from payment_classification.classifier import Classifier
from payment_classification.dataset import Dataset
from payment_classification.experiments.base_experiment import BaseExperiment


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
    space: Dict

    def __init__(self, clf: BaseEstimator, space: Dict):
        self.clf = clf
        self.space = space
        self.EXPERIMENT_NAME = f"Tuning{clf.__class__.__name__}Experiment"

    @BaseExperiment.register_mlflow
    def run(self, dataset: Dataset):
        mlflow.log_text(",".join(dataset.feature_names()), "features.txt")
        X_train, X_test, y_train, y_test = self.split_to_sets(dataset.X, dataset.y)
        score = make_scorer(self.score, greater_is_better=True)
        clf = GridSearchCV(self.clf, self.space, scoring=score)
        clf.fit(X_train, y_train)

        best_clf = clf.best_estimator_
        y_pred = best_clf.predict(X_test)
        score = self.score(y_test, y_pred)
        print(f"Score of best clf: {score}")
        mlflow.log_metric("cohen_kappa", score)

    @classmethod
    def score(cls, y, y_pred):
        return Classifier.evaluate(y, y_pred)[-1]
