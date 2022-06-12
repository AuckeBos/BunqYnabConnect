from payment_classification.experiments.classifier_selection_experiment import \
    ClassifierSelectionExperiment

if __name__ == "__main__":
    import _fix_imports
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from payment_classification.experiments.hyperparameter_tuning_experiment import (
    HyperparameterTuningExperiment,
)
from helpers.helpers import load_datasets

sets = load_datasets()
set = sets[0]


def tune_tree():
    space = {
        "criterion": ["gini", "entropy", "log_loss"],
        "splitter": ["best", "random"],
        "max_depth": [3, 5, 10, 20, 50, None],
    }
    clf = DecisionTreeClassifier()
    HyperparameterTuningExperiment(clf, space).run(set)


def tune_forest():
    space = {
        "n_estimators": [100, 1000, 2500],
        "criterion": ["gini", "entropy", "log_loss"],
        "max_depth": [5, 10, 20, 50, 250, None],
    }
    clf = RandomForestClassifier(n_jobs=-1)
    HyperparameterTuningExperiment(clf, space).run(set)

def test():
    ClassifierSelectionExperiment().run(set)


test()
