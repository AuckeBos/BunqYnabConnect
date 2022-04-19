import json
import os.path
import warnings
from typing import List, Tuple

from bunq import Pagination
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.http.api_client import ApiClient
from bunq.sdk.model.core.bunq_model import BunqModel
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.endpoint import Payment, MonetaryAccount

from cache import cache
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

    @classmethod
    def iban_of_bunqmodel(cls, model: BunqModel) -> str:
        """
        Get the iban of a bunqmodel
        Todo: Create custom BunqModel class, add this method dto is
        """
        for alias in model.alias:
            if alias.type_ == 'IBAN':
                return alias.value
        raise ValueError(f"Cannot find iban of bunq model {model}")

    def get_accounts(self) -> List[BunqModel]:
        """
        Get a list of all bunq accounts
        """
        return [a.get_referenced_object() for a in endpoint.MonetaryAccount.list().value]

    # Cache for a week
    @cache(ttl=604800)
    def get_payments(self) -> List[Tuple[BunqModel, List[Payment]]]:
        """
        Get a list of tuples:
        BankAccount, Payments
        """
        # Max allowed count is 200
        page_count = 200
        result = []
        for account in self.get_accounts():
            pagination = Pagination()
            pagination.count = page_count
            # For first query, only param is the count param
            params = pagination.url_params_count_only
            payments = []
            should_continue = True

            while should_continue:
                query_result = endpoint.Payment.list(monetary_account_id=account.id_,
                                                     params=params)
                payments.extend(query_result.value)
                should_continue = query_result.pagination.has_previous_page()
                if should_continue:
                    # Use previous_page since ordering is new to old
                    params = query_result.pagination.url_params_previous_page
            result.append((account, payments))
        return result
