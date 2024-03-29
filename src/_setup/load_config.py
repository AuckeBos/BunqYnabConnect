import json
import os

import requests
from bunq import ApiEnvironmentType
from bunq.sdk.context.api_context import ApiContext

CURRENT_DIR = os.path.dirname(__file__)
CONFIG_DIR = f"{CURRENT_DIR}/../../config"
CONFIG_FILE = f"{CONFIG_DIR}/cfg.json"
BUNQ_CONFIG_FILE = f"{CONFIG_DIR}/bunq.cfg"
DOCKERFILE_TEMPLATE = f"{CURRENT_DIR}/../../docker/docker-compose.template"
DOCKERFILE = f"{CURRENT_DIR}/../../docker-compose.yml"


def setup():
    """
    Run the one-time setup. Must be run on the host, and it:
    - Asks for user input, is saved in cfg.json. Contains data like host and port
    - Creates the docker-compose.yml, based on the port
    - Creates a bunq cfg file
    """
    if os.path.exists(CONFIG_DIR):
        print("Config folder yet exists. To re-run the setup, delete your config dir")
        exit()
    print(
        "Before continuing, make sure you have \na) your _bunq api key \nb) your _ynab "
        "api token\n"
    )
    input("Press enter to key to continue...")
    _setup_config()
    print("""Config dir created. Please make sure to create symlinks 
    config/privkey.pem  and config/fullchain.pem to the locations of those files. And 
    make sure the certificates are updated automatically, for example using certbot.
    """
    )
    _setup_docker()
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
            be forwarded in your private network. The docker image will expose port 
            9888, docker-compose maps it to the port you define here. [9888]: "
            """
        )
        or 9888,
        "hostname": input(
            "On which url (without port, without https://) is the host found (bunq "
            "connects to this url)?: "
        ),
        "ynab_token": input("What is your YNAB api token?: "),
        "ssl_context": ("/config/fullchain.pem", "/config/privkey.pem"),
        "currency": input("What is your default currency code? [EUR]: ") or "EUR",
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


def _setup_docker():
    """
    Create the docker-compose file, based on the docker-compose template
    The actual file has the <PORT> variable replace by the user input, such that the
    dockerfile will expose the port
    """
    from helpers.helpers import get_config
    port = get_config("port")
    with open(DOCKERFILE_TEMPLATE, "r") as f:
        template = f.read()
    updated_content = template.replace("<PORT>", str(port))
    with open(DOCKERFILE, 'w+') as f:
        f.write(updated_content)
    print("Dockerfile created")


def get_public_ip():
    """
    Get the current public ip address
    """
    return requests.get("http://ipinfo.io/json").json()["ip"]
