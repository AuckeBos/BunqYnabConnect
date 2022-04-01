import datetime
import json
import os

from setup import CONFIG_DIR, CONFIG_FILE

LOGFILE = 'log.log'


def log(msg, error=False):
    """
    Helper function to log any data to stdout
    """
    typestring = "E" if error else "I"
    print(
        f'[{typestring}] [{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] - '
        f'{msg}'
    )


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
