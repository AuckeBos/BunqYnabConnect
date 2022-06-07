import json
import threading

from flask import Flask, request

from helpers.helpers import get_bunq_connector
from helpers.helpers import get_config

app = Flask(__name__)


@app.route("/receive-transaction", methods=['GET', 'POST'])
def receive_transaction():
    """
    Receive a transaction. Must be added as callback for any transaction of type
    MUTATION by _bunq

    # A:
    Run in thread, such that we return 200 immediately. Otherwise return takes to
    long, hence _bunq doesnt receive it, hence it will re-run the callback 5 times,
    resulting in multiple _ynab transactions
    """
    transaction = json.loads(request.data.decode())
    threading.Thread(target=process_transaction, args=(transaction,)).start()
    return "OK", 200


def process_transaction(transaction):
    """
    Process a transaction, by claled add_transaction on _bunq
    """
    get_bunq_connector().add_transaction(transaction)


if __name__ == '__main__':
    """
    Run the flask app indefinitely
    """
    cfg = get_config()

    app.run(host=cfg["host"], port=cfg["port"], ssl_context=tuple(cfg["ssl_context"]), )
