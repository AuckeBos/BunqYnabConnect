import datetime
import json
import os
import pickle
from functools import wraps
from time import sleep
from typing import List, Any

from mlflow import log_artifact

from _setup.load_config import CONFIG_DIR, CONFIG_FILE


LOGFILE = "../log.log"
_bunq_connector = None
_ynab_connector = None


def log(msg, error=False, with_divider = False):
    """
    Helper function to log any data to stdout
    Parameters
    ----------
    msg: str
        The msg to log
    error: bool = False
        Prefix with 'E' if True, else 'I'
    with_divider: bool = False
        If true, surround with dividers
    """
    typestring = "E" if error else "I"
    txt = (
        f'[{typestring}] [{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] - '
        f"{msg}\n"
    )
    if with_divider:
        divider = f"{'=' * len(txt)}\n"
        txt = f"{divider}{txt}{divider}"
    with open(LOGFILE, "a") as f:
        f.write(txt)

def setup_needed() -> bool:
    """
    Check whether the setup has been ran. If not, return True
    """
    return not os.path.exists(CONFIG_DIR)


def get_config(key=None):
    """
    Load config json file. If key is provided, return only that value. Otherwise the
    complete dict
    """
    if setup_needed():
        print("Please run the setup script: python setup.py")
        exit()

    with open(CONFIG_FILE) as file:
        cfg = json.load(file)
        if key is not None:
            return cfg[key]
        return cfg


def get_bunq_connector():
    """
    Get the BunqConnector as singleton
    """
    from bunq_ynab_connector._bunq.bunq import Bunq

    global _bunq_connector
    if _bunq_connector is None:
        _bunq_connector = Bunq()
    return _bunq_connector


def get_ynab_connector():
    """
    Get the YNABConnector as singleton
    """
    from bunq_ynab_connector._ynab.ynab import Ynab

    global _ynab_connector
    if _ynab_connector is None:
        _ynab_connector = Ynab()
    return _ynab_connector


def load_datasets() -> List:
    from model_selection.dataset import Dataset

    """
    Load all datasets, one for each budget
    """
    log("Loading datasets")
    datasets = []
    budgets = get_ynab_connector().get_budgets()
    for budget in budgets:
        # Remove below on production
        # if budget.budget_info.name != "Maaike":
        #     continue
        dataset = Dataset(budget.load_info())
        if not dataset.is_valid:
            log(f"Skipping invalid dataset {dataset.budget.id}")
        else:
            datasets.append(dataset)
            log(f"Dataset loaded for budget {budget.id}")
    log("Finished loading datasets")
    return datasets


def retry(max_attempts: int, message: str = None):
    """
    Retry decorator. If an exception occurs, retry. For at most max_attemts times
    :param max_attempts: The max nr of attempts
    :param message The error message to log
    args
    """

    message = message or ""
    message += f" - Call failed {max_attempts} times"

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            count = 0
            exception = None
            # Try until max attempts
            while count < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    count += 1
                    if count >= max_attempts:
                        exception = e
                        break
                    log(f"Call failed, retrying... - {e}")
                    sleep(5)
            log(f"{message} - {exception}", True)

        return wrapper

    return decorator


def object_to_mlflow(obj: Any, name: str) -> None:
    """
    Save an object to an artifact by:
    - Saving the object to a temp pickle file
    - Saving the temp pickle file as artifact in the current mlfow run
    Parameters
    ----------
    obj: Any
        The dict to save
    name: str
        The artefact name
    """
    with open("../helpers/artifact.pickle", "wb+") as handle:
        pickle.dump(obj, handle, protocol=pickle.HIGHEST_PROTOCOL)
    log_artifact("../helpers/artifact.pickle", name)


def get_mlflow_model_name(dataset) -> str:
    """
    Get the name under which to deploy the model for this dataset
    """
    return f"Classifier for Budget {dataset.budget.id}"
