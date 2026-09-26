from __future__ import annotations

from dataclasses import asdict

from .models import CampaignManagerConfig


class CampaignManager:

    @classmethod
    def from_config(cls, config: CampaignManagerConfig) -> CampaignManager:
        return cls(**asdict(config))

    def __init__(self, campaigns):
        self.campaigns = campaigns

    def __delitem__(self, index):
        del self.campaigns[index]

    def __getattr__(self, name):
        if name in self.campaigns:
            return self.campaigns[name]
        raise AttributeError(f"'CampaignManager' object has no attribute '{name}'")

    def __getitem__(self, index):
        if index in self.campaigns:
            return self.campaigns[index]
        raise IndexError(f"Index {index} is out of range")

    def __len__(self):
        return len(self.campaigns)

    def __setitem__(self, index, value):
        self.campaigns[index] = value
