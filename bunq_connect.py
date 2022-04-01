import json
import os.path
import warnings

from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.http.api_client import ApiClient

from helpers import log, get_config
from setup import BUNQ_CONFIG_FILE
from ynab_connect import Ynab

warnings.filterwarnings('ignore')


class Bunq:
    """
    Class responsible for any Bunq connection functionality
    """

    ynab: Ynab

    def __init__(self):
        """
        Create Ynab connector, load self
        """
        self.ynab = Ynab()
        self._load()
        self._check_callback()

    def add_transaction(self, transaction: dict):
        """
        Add a transaction to Ynab. Should be called by Flask, whenever Bunq calls
        webhook.
        """
        try:
            log(f"Adding transaction {transaction}")
            data = transaction['NotificationUrl']['object']['Payment']
            amount = float(data['amount']['value'])
            currency = data['amount']['currency']
            memo = ''
            if currency != get_config("currency"):
                memo = f'Note: currency is {currency}'
            iban = data['alias']['iban']
            payee = data['counterparty_alias']['display_name']
            self.ynab.add_transaction(iban, payee, amount, memo)
            log("Transaction added!")
        except Exception as e:
            log(f"Transaction not added: {e}", True)

    def _load(self):
        """
        Initialize context, ran on init
        """
        context = ApiContext.restore(BUNQ_CONFIG_FILE)
        context.ensure_session_active()
        context.save(BUNQ_CONFIG_FILE)
        BunqContext.load_api_context(context)

    def _get_callbacks(self) -> []:
        """
        Get all existing callbacks.
        Since sdk chokes on the Callback model, use raw api client
        :return: Callbacks as list, each callback has only category and
        notification_target
        """
        user_id = BunqContext.user_context().user_id
        url = f"/user/{user_id}/notification-filter-url"
        response = ApiClient(BunqContext.api_context()).get(url, {}, {})
        filters = json.loads(response.body_bytes.decode())["Response"]
        return [
            {
                "category": f["NotificationFilterUrl"]["category"],
                "notification_target": f["NotificationFilterUrl"]["notification_target"],
            } for f in filters
        ]

    def _put_callbacks(self, callbacks) -> bool:
        """
        Save list of callbacks. Override all callbacks with provided lists.
        Since sdk chokes on the Callback model, use raw api client
        :param callbacks: List of dicts, one dict per callback
        :return: bool success
        """
        user_id = BunqContext.user_context().user_id
        url = f"/user/{user_id}/notification-filter-url"

        data = {"notification_filters": callbacks}

        response = ApiClient(BunqContext.api_context()).post(url,
                                                             json.dumps(data).encode(),
                                                             {})
        log("Callback added successfully!")
        return True

    def _callback_exists(self, url, category) -> bool:
        """
        Check if a callback exists for a specific url
        :return: bool
        """
        callbacks = self._get_callbacks()
        for callback in callbacks:
            if callback["notification_target"].endswith(url) and \
                    callback["category"] == category:
                return True
        return False

    def _check_callback(self) -> None:
        """
        Check if the needed callback exists, else create it
        """
        cfg = get_config()
        url = f'https://{cfg["hostname"]}:{cfg["port"]}/receive-transaction'
        category = 'MUTATION'
        if self._callback_exists(url, category):
            return
        log("Adding callback once...")
        callbacks = self._get_callbacks()
        callbacks.append({
            "category": category,
            "notification_target": url
        })
        self._put_callbacks(callbacks)
