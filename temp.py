from _classifier.classifier import Classifier
from experiments.classifier_selection_experiment import ClassifierSelectionExperiment
from experiments.decision_tree_tuning_experiment import DecisionTreeTuningExperiment
from helpers.helpers import load_datasets

sets = load_datasets()
set = sets[0]
experiment = DecisionTreeTuningExperiment()
experiment.run(set)