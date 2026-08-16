from __future__ import annotations

import builtins
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib.metadata import EntryPoint, entry_points
from re import fullmatch


class PluginKind(str, Enum):
    STRATEGY = "strategy"
    BROKER = "broker"
    INDICATOR = "indicator"
    REPORT = "report"


ENTRY_POINT_GROUPS = {
    PluginKind.STRATEGY: "tradeforge.strategies",
    PluginKind.BROKER: "tradeforge.brokers",
    PluginKind.INDICATOR: "tradeforge.indicators",
    PluginKind.REPORT: "tradeforge.reports",
}


@dataclass(frozen=True, slots=True)
class PluginDescriptor:
    kind: PluginKind
    name: str
    version: str
    source: str
    plugin: object


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins: dict[tuple[PluginKind, str], PluginDescriptor] = {}

    def register(
        self,
        kind: PluginKind,
        name: str,
        plugin: object,
        *,
        version: str = "unknown",
        source: str = "local",
    ) -> PluginDescriptor:
        normalized = _normalize_name(name)
        key = (kind, normalized)
        if key in self._plugins:
            raise ValueError(f"Plugin is already registered: {kind.value}/{normalized}")
        descriptor = PluginDescriptor(kind, normalized, version.strip() or "unknown", source.strip() or "local", plugin)
        self._plugins[key] = descriptor
        return descriptor

    def get(self, kind: PluginKind, name: str) -> object:
        normalized = _normalize_name(name)
        try:
            return self._plugins[(kind, normalized)].plugin
        except KeyError as exc:
            available = ", ".join(item.name for item in self.list(kind)) or "none"
            raise KeyError(f"Unknown {kind.value} '{name}'. Available: {available}.") from exc

    def list(self, kind: PluginKind | None = None) -> list[PluginDescriptor]:
        return sorted(
            (item for item in self._plugins.values() if kind is None or item.kind is kind),
            key=lambda item: (item.kind.value, item.name),
        )

    def discover(self, allowed_names: set[str]) -> builtins.list[PluginDescriptor]:
        normalized_allowlist = {_normalize_name(name) for name in allowed_names}
        discovered: list[PluginDescriptor] = []
        all_entry_points = entry_points()
        for kind, group in ENTRY_POINT_GROUPS.items():
            for entry_point in all_entry_points.select(group=group):
                normalized = _normalize_name(entry_point.name)
                if normalized not in normalized_allowlist:
                    continue
                discovered.append(self._register_entry_point(kind, entry_point))
        return discovered

    def _register_entry_point(self, kind: PluginKind, entry_point: EntryPoint) -> PluginDescriptor:
        distribution = entry_point.dist
        version = distribution.version if distribution is not None else "unknown"
        source = distribution.name if distribution is not None else entry_point.module
        return self.register(kind, entry_point.name, entry_point.load(), version=version, source=source)


@lru_cache(maxsize=1)
def get_default_registry() -> PluginRegistry:
    return create_default_registry()


def create_default_registry() -> PluginRegistry:
    from tradeforge.broker_sim.execution import SimBroker
    from tradeforge.reporting.reports import write_markdown_report
    from tradeforge.strategies.moving_average_cross import MovingAverageCrossStrategy

    registry = PluginRegistry()
    registry.register(PluginKind.STRATEGY, "moving-average-cross", MovingAverageCrossStrategy, version="1")
    registry.register(PluginKind.BROKER, "simulated", SimBroker, version="1")
    registry.register(PluginKind.INDICATOR, "simple-moving-average", _simple_moving_average, version="1")
    registry.register(PluginKind.REPORT, "markdown", write_markdown_report, version="1")
    return registry


def _normalize_name(name: str) -> str:
    normalized = name.strip().lower()
    if fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", normalized) is None:
        raise ValueError("Plugin names must use lowercase letters, numbers, and single hyphens.")
    return normalized


def _simple_moving_average(values: list[float], window: int) -> list[float | None]:
    if window <= 0:
        raise ValueError("window must be positive.")
    return [
        None if index + 1 < window else sum(values[index + 1 - window : index + 1]) / window
        for index in range(len(values))
    ]
