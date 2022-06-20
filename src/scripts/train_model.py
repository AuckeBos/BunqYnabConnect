if __name__ == "__main__":
    import _fix_imports
from helpers.helpers import load_datasets
from payment_classification.model_selector import ModelSelector

if __name__ == "__main__":
    sets = load_datasets()
    set = sets[0]

    ModelSelector(set).select()
