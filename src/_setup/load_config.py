import json
import os

import requests
from bunq import ApiEnvironmentType
from bunq.sdk.context.api_context import ApiContext

CURRENT_DIR = os.path.dirname(__file__)
CONFIG_DIR = f"{CURRENT_DIR}/../../config"
CONFIG_FILE = f"{CONFIG_DIR}/cfg.json"
BUNQ_CONFIG_FILE = f"{CONFIG_DIR}/bunq.cfg"
DOCKERFILE_TEMPLATE = f"{CURRENT_DIR}/../../docker/Dockerfile.template"
DOCKERFILE = f"{CURRENT_DIR}/../../Dockerfile"


def setup():
    if os.path.exists(CONFIG_DIR):
        print("Config folder yet exists. To re-run the setup, delete your config dir")
        exit()
    print(
        "Before continuing, make sure you have \na) your _bunq api key \nb) your _ynab "
        "api token\n"
    )
    input("Press enter to key to continue...")
    _setup_config()
    print(
        "Config dir created. Please copy your private key and chainfile to the "
        "config dir, named privkey.pem and fullchain.pem respectively"
    )
    input("Press enter to key to continue...")
    _setup_bunq()


def _setup_config():
    """
    Retrieve user input for the .cfg file
    """
    print("To enable the bunq webhook, a Flask REST api is hosted.")
    cfg = {
        "host": input("On which host should the server listen? [0.0.0.0]: ")
        or "0.0.0.0",
        "port": input(
            """On which port should the server be reachable? Note that this port should
            be forwarded in your private network. When you start the docker container,
            make sure you map this port to port 9888 on the container. [9888]: "
            """
        )
        or 9888,
        "hostname": input(
            "On which url is the host found (bunq connects to this " "url)?: "
        ),
        "ynab_token": input("What is your YNAB api token?: "),
        "ssl_context": ("/config/fullchain.pem", "/config/privkey.pem"),
        "currency": input("What is your default currency code?: "),
    }
    os.mkdir(CONFIG_DIR)
    # Create empty model port file
    from helpers.helpers import MODEL_PORT_FILE

    with open(MODEL_PORT_FILE, "x") as file:
        json.dump({}, file)
    with open(CONFIG_FILE, "x") as file:
        json.dump(cfg, file)

def _setup_bunq() -> None:
    """
    Ask for _bunq connection token, create cfg file
    """
    env = ApiEnvironmentType.PRODUCTION
    key = input("What is your bunq api key?: ")
    description = "BunqYnabConnect"
    ips = [get_public_ip()]
    try:
        context = ApiContext.create(env, key, description, ips)
        context.save(BUNQ_CONFIG_FILE)
    except Exception as e:
        print(f"Could not create _bunq config: {e}", True)
        exit()


def get_public_ip():
    """
    Get the current public ip address
    """
    return requests.get("http://ipinfo.io/json").json()["ip"]
