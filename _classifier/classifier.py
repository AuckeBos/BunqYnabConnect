from typing import List, Tuple

from _bunq.bunq_account import BunqAccount
from _classifier.dataset import Dataset
from helpers.helpers import get_bunq_connector, get_ynab_connector
from _ynab.ynab_account import YnabAccount


class Classifier:

    def __init__(self):
        self.load_datasets()


    def load_datasets(self):
        budgets = get_ynab_connector().get_budgets()
        for budget in budgets:
            if budget.budget_info.name != 'Aucke':
                continue

            dataset = Dataset(budget.load_info())