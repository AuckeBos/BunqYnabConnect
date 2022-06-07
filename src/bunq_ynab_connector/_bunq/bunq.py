import json
import warnings
from typing import List

from bunq import Pagination
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.http.api_client import ApiClient
from bunq.sdk.model.generated import endpoint
from bunq.sdk.model.generated.endpoint import Payment

from bunq_ynab_connector._bunq.bunq_account import BunqAccount
from helpers.cache import cache
from helpers.helpers import log, get_config, get_ynab_connector, retry
from setup import BUNQ_CONFIG_FILE

warnings.filterwarnings('ignore')


class Bunq:
    """
    Class responsible for any _bunq connection functionality
    """

    def __init__(self):
        self._load()
        self._check_callback()

    @retry(2, message="Transaction not added")
    def add_transaction(self, transaction: dict):
        """
        Add a transaction to _ynab. Should be called by Flask, whenever _bunq calls
        webhook.
        """
        log(f"Adding transaction {transaction}")
        data = transaction['NotificationUrl']['object']['Payment']
        amount = float(data['amount']['value'])
        currency = data['amount']['currency']
        memo = data['description']
        if currency != get_config("currency"):
            memo += f' - Note: currency is {currency}'
        iban = data['alias']['iban']
        payee = data['counterparty_alias']['display_name']
        get_ynab_connector().add_transaction(iban, payee, amount, memo)
        log("Transaction added!")

    @cache(ttl=60 * 60 * 24)
    def get_bunq_accounts(self) -> List[BunqAccount]:
        """
        Get a list of all bunq accounts
        """
        return [BunqAccount(a) for a in endpoint.MonetaryAccount.list().value]

    def get_transactions(self, account_id: int) -> List[Payment]:
        """
        Get the payments of a BunqAccount
        """
        # Max allowed count is 200
        payments = []
        page_count = 200
        pagination = Pagination()
        pagination.count = page_count
        # For first query, only param is the count param
        params = pagination.url_params_count_only
        should_continue = True

        while should_continue:
            query_result = endpoint.Payment.list(monetary_account_id=account_id,
                                                 params=params)
            payments.extend(query_result.value)
            should_continue = query_result.pagination.has_previous_page()
            if should_continue:
                # Use previous_page since ordering is new to old
                params = query_result.pagination.url_params_previous_page
        return payments

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
