from __future__ import annotations

from ..models import Campaign


class CampaignManager:

    def __init__(self, campaigns: list[Campaign] | None = None):
        self._campaigns = campaigns or []

    def __delitem__(self, index):
        del self._campaigns[index]

    def __getattr__(self, name):
        if name in self._campaigns:
            return self._campaigns[name]
        raise AttributeError(f"'CampaignManager' object has no attribute '{name}'")

    def __getitem__(self, index):
        if index in self._campaigns:
            return self._campaigns[index]
        raise IndexError(f"Index {index} is out of range")

    def __len__(self):
        return len(self._campaigns)

    def __setitem__(self, index, value):
        self._campaigns[index] = value
