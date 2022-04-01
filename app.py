import json

from flask import Flask, request

from bunq_connect import Bunq
from helpers import get_config
from ynab_connect import Ynab

app = Flask(__name__)


@app.route("/receive-transaction", methods=['GET', 'POST'])
def receive_transaction():
    """
    Receive a transaction. Must be added as callback for any transaction of type
    MUTATION by Bunq
    """
    transaction = json.loads(request.data.decode())
    bunq = Bunq()
    bunq.add_transaction(transaction)
    return "OK", 200


if __name__ == '__main__':
    """
    Run the flask app indefinitely
    """
    cfg = get_config()

    app.run(host=cfg["host"], port=cfg["port"], ssl_context=tuple(cfg["ssl_context"]), )
