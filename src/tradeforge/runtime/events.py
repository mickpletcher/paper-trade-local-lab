from __future__ import annotations

import heapq
from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class EventKind(str, Enum):
    BAR = "bar"
    TICK = "tick"
    NEWS = "news"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class Event:
    timestamp: datetime
    kind: EventKind
    payload: Mapping[str, object] = field(default_factory=dict)
    source: str = "tradeforge"

    def __post_init__(self) -> None:
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("Event timestamps must be timezone aware.")
        if not self.source.strip():
            raise ValueError("Event source must not be empty.")


EventHandler = Callable[[Event], None]


class EventRuntime:
    def __init__(self) -> None:
        self._queue: list[tuple[datetime, int, Event]] = []
        self._handlers: dict[EventKind, list[EventHandler]] = defaultdict(list)
        self._sequence = 0

    def subscribe(self, kind: EventKind, handler: EventHandler) -> None:
        if handler not in self._handlers[kind]:
            self._handlers[kind].append(handler)

    def publish(self, event: Event) -> None:
        heapq.heappush(self._queue, (event.timestamp, self._sequence, event))
        self._sequence += 1

    def run(self, max_events: int | None = None) -> list[Event]:
        if max_events is not None and max_events < 0:
            raise ValueError("max_events must be nonnegative.")
        processed: list[Event] = []
        while self._queue and (max_events is None or len(processed) < max_events):
            _, _, event = heapq.heappop(self._queue)
            for handler in self._handlers[event.kind]:
                handler(event)
            processed.append(event)
        return processed

    @property
    def pending_count(self) -> int:
        return len(self._queue)
