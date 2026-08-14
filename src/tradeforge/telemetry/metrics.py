from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from threading import Lock
from time import time


@dataclass(frozen=True)
class HttpMetric:
    method: str
    path: str
    status_code: int


class MetricsRegistry:
    def __init__(self) -> None:
        self._started_at = time()
        self._counts: Counter[HttpMetric] = Counter()
        self._duration_seconds: Counter[HttpMetric] = Counter()
        self._lock = Lock()

    def record_http_request(self, method: str, path: str, status_code: int, duration_seconds: float) -> None:
        key = HttpMetric(method=method, path=path, status_code=status_code)
        with self._lock:
            self._counts[key] += 1
            self._duration_seconds[key] += duration_seconds

    def render_prometheus(self) -> str:
        with self._lock:
            counts = dict(self._counts)
            durations = dict(self._duration_seconds)
        lines = [
            "# HELP tradeforge_http_requests_total Total HTTP requests processed.",
            "# TYPE tradeforge_http_requests_total counter",
        ]
        for metric, value in sorted(
            counts.items(), key=lambda item: (item[0].path, item[0].method, item[0].status_code)
        ):
            lines.append(
                f'tradeforge_http_requests_total{{method="{metric.method}",path="{metric.path}",status="{metric.status_code}"}} {value}'
            )
        lines.extend(
            [
                "# HELP tradeforge_http_request_duration_seconds_total Total request duration accumulated by route.",
                "# TYPE tradeforge_http_request_duration_seconds_total counter",
            ]
        )
        for metric, value in sorted(
            durations.items(), key=lambda item: (item[0].path, item[0].method, item[0].status_code)
        ):
            lines.append(
                f'tradeforge_http_request_duration_seconds_total{{method="{metric.method}",path="{metric.path}",status="{metric.status_code}"}} {value:.6f}'
            )
        lines.extend(
            [
                "# HELP tradeforge_process_uptime_seconds Process uptime in seconds.",
                "# TYPE tradeforge_process_uptime_seconds gauge",
                f"tradeforge_process_uptime_seconds {time() - self._started_at:.6f}",
            ]
        )
        return "\n".join(lines) + "\n"


metrics_registry = MetricsRegistry()
