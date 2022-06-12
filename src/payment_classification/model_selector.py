from bunq_ynab_connector._ynab.budget import Budget


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
    budget: Budget
    def __init__(self, budget: Budget):
        self.budget = budget




