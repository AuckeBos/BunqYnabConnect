
if __name__ == "__main__":
    import _fix_imports
from model_selection.model_deployer import ModelDeployer
from helpers.helpers import load_datasets, log
from model_selection.model_selector import ModelSelector

# For each set:
# 1. Select the best model
# 2. Deploy it
if __name__ == "__main__":
    sets = load_datasets()
    log(f"Training {len(sets)} models")
    for set in sets:
        log(f"BUDGET {set.budget.id} ({set.budget.budget_info.name})", False, True)
        classifier_class, hyper_parameters = ModelSelector(set).select()
        ModelDeployer(set).deploy(classifier_class, hyper_parameters)
    log(f"Model training finished")