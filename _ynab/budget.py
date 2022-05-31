from typing import Any


class Budget:
    budget_info: Any
    id: int

    def __init__(self, budget_info: Any):
        self.budget_info = budget_info

    @property
    def id(self):
        return self.budget_info.id
