from __future__ import annotations

from collections.abc import Iterator
from typing import overload

from ..models.campaign_model import Campaign


class CampaignManager:
    """
    Orchestrates and manages polling campaigns.
    Provides dictionary-like named access, list-like indexing, and iteration.
    """

    def __init__(self, campaigns: list[Campaign] | None = None) -> None:
        # Store internally as a dictionary mapped by campaign.name for O(1) lookups.
        # Python dicts preserve insertion order natively.
        self._campaigns: dict[str, Campaign] = {}

        if campaigns:
            for campaign in campaigns:
                self.add(campaign)

    def add(self, campaign: Campaign) -> None:
        """Registers a new campaign."""
        if not isinstance(campaign, Campaign):
            raise TypeError(f"Expected Campaign object, got {type(campaign).__name__}")
        self._campaigns[campaign.name] = campaign

    def remove(self, name: str) -> None:
        """Safely removes a campaign by its name."""
        self._campaigns.pop(name, None)

    def get(self, name: str) -> Campaign | None:
        """Safely retrieve a campaign by name without raising exceptions."""
        return self._campaigns.get(name)

    # --- Magic Methods for Pythonic Access ---

    def __iter__(self) -> Iterator[Campaign]:
        """Allows direct iteration: `for campaign in manager:`"""
        return iter(self._campaigns.values())

    def __len__(self) -> int:
        """Allows: `len(manager)`"""
        return len(self._campaigns)

    def __contains__(self, name: str) -> bool:
        """Allows: `if "tribology" in manager:`"""
        return name in self._campaigns

    def __getattr__(self, name: str) -> Campaign:
        """
        Allows dot-notation access: `manager.tribology_campaign`
        Note: This only works if the campaign name is a valid Python identifier.
        """
        if name in self._campaigns:
            return self._campaigns[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute or campaign named '{name}'")

    @overload
    def __getitem__(self, index: str) -> Campaign: ...

    @overload
    def __getitem__(self, index: int) -> Campaign: ...

    def __getitem__(self, index: str | int) -> Campaign:
        """Allows bracket access by name (str) or insertion order (int)."""
        if isinstance(index, str):
            if index not in self._campaigns:
                raise KeyError(f"No campaign found with name: '{index}'")
            return self._campaigns[index]

        if isinstance(index, int):
            try:
                # Cast values to list to support legacy integer indexing
                return list(self._campaigns.values())[index]
            except IndexError as e:
                raise IndexError(f"Campaign index {index} is out of range.") from e

        raise TypeError(f"Invalid index type: {type(index).__name__}")

    def __setitem__(self, key: str, value: Campaign) -> None:
        """Allows: `manager["new_campaign"] = campaign_obj`"""
        if not isinstance(value, Campaign):
            raise TypeError(f"Value must be a Campaign instance, got {type(value).__name__}")

        # Enforce that the dict key matches the campaign name to prevent split-brain bugs
        if key != value.name:
            raise ValueError(f"Key '{key}' must match the campaign name '{value.name}'")

        self._campaigns[key] = value

    def __delitem__(self, key: str | int) -> None:
        """Allows: `del manager["tribology"]` or `del manager[0]`"""
        if isinstance(key, str):
            if key not in self._campaigns:
                raise KeyError(f"No campaign found with name: '{key}'")
            del self._campaigns[key]

        elif isinstance(key, int):
            try:
                name_key = list(self._campaigns.keys())[key]
                del self._campaigns[name_key]
            except IndexError as e:
                raise IndexError(f"Campaign index {key} is out of range.") from e

        else:
            raise TypeError(f"Invalid index type: {type(key).__name__}")
