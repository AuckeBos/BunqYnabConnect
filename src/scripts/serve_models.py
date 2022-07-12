from model_selection.model_deployer import ModelDeployer

if __name__ == "__main__":
    print('yes')
    import _fix_imports
else:
    print(__name__)
from helpers.helpers import load_datasets
from model_selection.model_selector import ModelSelector

# For each set:
# 1. Serve the currently deployed model
if __name__ == "__main__":
    sets = load_datasets()
    for set in sets:
        classifier_class, hyper_parameters = ModelSelector(set).select()
        ModelDeployer(set).deploy(classifier_class, hyper_parameters)
