from __future__ import annotations

from dataclasses import asdict

from .models import JobBoardManagerConfig


class JobBoardManager:

    @classmethod
    def from_config(cls, config: JobBoardManagerConfig) -> JobBoardManager:
        return cls(**asdict(config))

    def __init__(self, job_boards):
        self.job_boards = job_boards

    def __delitem__(self, index):
        del self.job_boards[index]

    def __getattr__(self, name):
        if name in self.job_boards:
            return self.job_boards[name]
        raise AttributeError(f"'JobBoardManager' object has no attribute '{name}'")

    def __getitem__(self, index):
        if index in self.job_boards:
            return self.job_boards[index]
        raise IndexError(f"Index {index} is out of range")

    def __len__(self):
        return len(self.job_boards)

    def __setitem__(self, index, value):
        self.job_boards[index] = value
