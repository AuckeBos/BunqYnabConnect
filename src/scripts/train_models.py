if __name__ == "__main__":
    import _fix_imports
from model_selection.model_deployer import ModelDeployer
from helpers.helpers import load_datasets, log, MLFLOW_INITIALIZATION_FILE, \
    trigger_model_serving_restart
from model_selection.model_selector import ModelSelector
from pathlib import Path

def train_models():
    """
    For each set:
    1. Select the best model
    2. Deploy it
    """

    sets = load_datasets()
    log(f"Training {len(sets)} models")
    for set in sets:
        log(f"BUDGET {set.budget.id} ({set.budget.budget_info.name})", False, True)
        classifier_class, hyper_parameters = ModelSelector(set).select()
        ModelDeployer(set).deploy(classifier_class, hyper_parameters)
    log(f"Model training finished")

    # Touch the init file, notifying serve_models.py that at least one train_models is
    # performed
    Path(MLFLOW_INITIALIZATION_FILE).touch()
    # Trigger a model server restart
    trigger_model_serving_restart()

if __name__ == "__main__":
    train_models()
