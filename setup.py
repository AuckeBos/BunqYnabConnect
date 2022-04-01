import json
import os

import requests
from bunq import ApiEnvironmentType
from bunq.sdk.context.api_context import ApiContext

CONFIG_DIR = './config'
CONFIG_FILE = f"{CONFIG_DIR}/cfg.json"
BUNQ_CONFIG_FILE = f"{CONFIG_DIR}/bunq.cfg"


def setup():
    if os.path.exists(CONFIG_DIR):
        print("Config folder yet exists. To re-run the setup, delete your config dir")
        exit()
    print("Running one-time setup")
    print("Before continuing, make sure you have \na) your Bunq api key \nb) your Ynab "
          "api token\nc) The paths of the private key and chainfile of your ssl key")
    input("Press enter to key to continue...")
    _setup_config()
    _setup_bunq()


def _setup_config():
    """
    Retrieve user input for the .cfg file
    """
    print("To enable the Bunq webhook, a Flask REST api is hosted.")
    cfg = {
        "host": input("On which host should the server listen? [0.0.0.0]: ") or
                "0.0.0.0",
        "port": input(
            "On which port should the server listen? Note that this port should "
            "be forwarded in your private network. [9888]: ") or 9888,
        "hostname": input("On which url is the host found (Bunq connects to this "
                          "url)?: "),
        "ynab_token": input("What is your YNAB api token?: "),
        "ssl_context": (
            input("Where is your chain file (.pem) file located?: "),
            input("Where is your privatekey (.pem) file located?: "),
        ),
        "currency": input("What is your default currency code?: ")
    }
    os.mkdir(CONFIG_DIR)
    os.mkdir('./cache')
    with open(CONFIG_FILE, "x") as file:
        json.dump(cfg, file)


def _setup_bunq() -> None:
    """
    Ask for bunq connection token, create cfg file
    """
    env = ApiEnvironmentType.PRODUCTION
    key = input("What is your Bunq api key?: ")
    description = 'BunqYnabConnect'
    ips = [get_public_ip()]
    try:
        context = ApiContext.create(env, key, description, ips)
        context.save(BUNQ_CONFIG_FILE)
    except Exception as e:
        print(f"Could not create Bunq config: {e}", True)
        exit()


def get_public_ip():
    """
    Get the current public ip address
    """
    return requests.get('http://ipinfo.io/json').json()['ip']


if __name__ == '__main__':
    setup()
