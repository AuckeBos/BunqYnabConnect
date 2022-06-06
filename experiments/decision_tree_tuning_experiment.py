from typing import Tuple

import mlflow
import numpy as np
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.metrics import cohen_kappa_score, make_scorer
from sklearn.model_selection import GridSearchCV
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from _classifier.classifier import Classifier
from _classifier.dataset import Dataset
from experiments.base_experiment import BaseExperiment


class DecisionTreeTuningExperiment(BaseExperiment):
    """
    An experiment run a hyperparameter gridsearch on a DecisionTreeClassifier. This
    classifier seems to perform best, based on the ClassifierSelecitonExperiment

    ATTRIBUTES
    ----------
    PARAMTER_SPACE: Dict
        Hyperparameter map for grid search
    """

    PARAMETER_SPACE = {
        "criterion": ["gini", "entropy", "log_loss"],
        "splitter": ["best", "random"],
        "max_depth": [3, 5, 10, 20, 50, None],
    }

    @BaseExperiment.register_mlflow
    def run(self, dataset: Dataset):
        mlflow.log_text(",".join(dataset.feature_names()), "features.txt")
        X_train, X_test, y_train, y_test = self.split_to_sets(dataset.X, dataset.y)
        score = make_scorer(self.score, greater_is_better=True)
        clf = GridSearchCV(DecisionTreeClassifier(), self.PARAMETER_SPACE, scoring=score)
        clf.fit(X_train, y_train)

        best_clf = clf.best_estimator_
        y_pred = best_clf.predict(X_test)
        score = self.score(y_test, y_pred)
        print(f"Score of best clf: {score}")
        mlflow.log_metric("cohen_kappa", score)

    @classmethod
    def score(cls, y, y_pred):
        return cohen_kappa_score(y, y_pred)
