from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

from bunq_ynab_connector._ynab.budget import Budget
from payment_classification.dataset import Dataset
from payment_classification.experiments.classifier_selection_experiment import (
    ClassifierSelectionExperiment,
)
from payment_classification.experiments.hyperparameter_tuning_experiment import (
    HyperparameterTuningExperiment,
)


class GaussianNB__class__:
    pass


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

    # Todo: add
    HYPERPARAMETER_SPACES = {
        KNeighborsClassifier.__class__.__name__: {},
        SVC.__class__.__name__: {},
        DecisionTreeClassifier.__class__.__name__: {},
        RandomForestClassifier.__class__.__name__: {},
        MLPClassifier.__class__.__name__: {},
        AdaBoostClassifier.__class__.__name__: {},
        GaussianNB__class__.__name__: {},
    }

    def __init__(self, dataset: Dataset):
        self.dataset = dataset

    def select(self):
        # wip
        experiment = ClassifierSelectionExperiment()
        experiment.run(self.dataset)
        classifier_class = experiment.best_run.data.tags["estimator_class"]
        classifier_class_name = classifier_class.split(".")[-1]
        hyper_space = self.HYPERPARAMETER_SPACES[classifier_class_name]

        experiment = HyperparameterTuningExperiment(
            eval(classifier_class)(), hyper_space
        )


        # Todo: Create map of classifier to hyperparam map. Select item run
        #  experiment, set resultint data
