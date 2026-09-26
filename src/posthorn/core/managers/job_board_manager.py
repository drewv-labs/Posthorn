from __future__ import annotations

from collections.abc import Iterator
from typing import overload

from ..interfaces.job_board import JobBoard


class JobBoardManager:
    """
    Orchestrates and manages job board polling adapters.
    Provides dictionary-like named access, list-like indexing, and iteration.
    """

    def __init__(self, job_boards: list[JobBoard] | None = None) -> None:
        # Store internally as a dictionary mapped by board.name for O(1) lookups.
        self._job_boards: dict[str, JobBoard] = {}

        if job_boards:
            for board in job_boards:
                self.add(board)

    def add(self, board: JobBoard) -> None:
        """Registers a new job board adapter."""
        if not hasattr(board, "name"):
            raise TypeError(f"Adapter {type(board).__name__} is missing the required 'name' property.")
        self._job_boards[board.name] = board

    def remove(self, name: str) -> None:
        """Safely removes a job board adapter by its name."""
        self._job_boards.pop(name, None)

    def get(self, name: str) -> JobBoard | None:
        """Safely retrieve a job board adapter by name without raising exceptions."""
        return self._job_boards.get(name)

    # --- Magic Methods for Pythonic Access ---

    def __iter__(self) -> Iterator[JobBoard]:
        """Allows direct iteration: `for board in manager:`"""
        return iter(self._job_boards.values())

    def __len__(self) -> int:
        """Allows: `len(manager)`"""
        return len(self._job_boards)

    def __contains__(self, name: str) -> bool:
        """Allows: `if "linkedin" in manager:`"""
        return name in self._job_boards

    def __getattr__(self, name: str) -> JobBoard:
        """
        Allows dot-notation access: `manager.linkedin`
        """
        if name in self._job_boards:
            return self._job_boards[name]
        raise AttributeError(f"'{self.__class__.__name__}' has no attribute or board named '{name}'")

    @overload
    def __getitem__(self, index: str) -> JobBoard: ...

    @overload
    def __getitem__(self, index: int) -> JobBoard: ...

    def __getitem__(self, index: str | int) -> JobBoard:
        """Allows bracket access by name (str) or insertion order (int)."""
        if isinstance(index, str):
            if index not in self._job_boards:
                raise KeyError(f"No job board found with name: '{index}'")
            return self._job_boards[index]

        if isinstance(index, int):
            try:
                # Cast values to list to support integer indexing
                return list(self._job_boards.values())[index]
            except IndexError as e:
                raise IndexError(f"Job board index {index} is out of range.") from e

        raise TypeError(f"Invalid index type: {type(index).__name__}")

    def __setitem__(self, key: str, value: JobBoard) -> None:
        """Allows: `manager["new_board"] = board_obj`"""
        if not hasattr(value, "name"):
            raise TypeError(f"Adapter {type(value).__name__} is missing the required 'name' property.")

        # Enforce that the dict key matches the board name to prevent split-brain bugs
        if key != getattr(value, "name"):
            raise ValueError(f"Key '{key}' must match the job board name '{getattr(value, 'name')}'")

        self._job_boards[key] = value

    def __delitem__(self, key: str | int) -> None:
        """Allows: `del manager["linkedin"]` or `del manager[0]`"""
        if isinstance(key, str):
            if key not in self._job_boards:
                raise KeyError(f"No job board found with name: '{key}'")
            del self._job_boards[key]

        elif isinstance(key, int):
            try:
                name_key = list(self._job_boards.keys())[key]
                del self._job_boards[name_key]
            except IndexError as e:
                raise IndexError(f"Job board index {key} is out of range.") from e

        else:
            raise TypeError(f"Invalid index type: {type(key).__name__}")
