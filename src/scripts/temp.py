from mlflow.tracking import MlflowClient

from model_selection.experiments.classifier_selection_experiment import \
    ClassifierSelectionExperiment
from model_selection.model_selector import ModelSelector
from model_selection.model_server import ModelServer

if __name__ == "__main__":
    import _fix_imports
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier

from model_selection.experiments.hyperparameter_tuning_experiment import (
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
    ModelSelector(set).select()




# test()

#
# name = "Classifier for Budget 7f04a6d1-40aa-4fce-a7c5-e213a8ea3c11"
#
# client = MlflowClient()
# test = client.get_latest_versions(name, stages=['None'])[0].version
# client.transition_model_version_stage(
#     name="Classifier for Budget 7f04a6d1-40aa-4fce-a7c5-e213a8ea3c11",
#     # version=3,
#     stage="Production"
# )
# set
# test = ''
ModelServer()