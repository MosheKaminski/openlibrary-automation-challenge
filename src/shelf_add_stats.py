"""Tracks how many books were added to each shelf in the last add_books run."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ShelfAddStats:
    want_to_read: int = field(default=0)
    already_read: int = field(default=0)

    def reset(self) -> None:
        self.want_to_read = 0
        self.already_read = 0


_LAST_RUN = ShelfAddStats()


def last_shelf_add_stats() -> ShelfAddStats:
    """Use after add_books_to_reading_list: assert Want shelf against want_to_read only."""
    return _LAST_RUN


def reset_shelf_add_stats() -> None:
    _LAST_RUN.reset()
