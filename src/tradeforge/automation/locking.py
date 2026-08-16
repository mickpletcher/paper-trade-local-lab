from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from time import monotonic


class MaintenanceLockError(RuntimeError):
    pass


class MaintenanceLock:
    def __init__(self, path: Path, stale_seconds: int):
        self.path = path.resolve()
        self.stale_seconds = stale_seconds
        self.wait_ms = 0
        self._owned = False

    def __enter__(self) -> "MaintenanceLock":
        started = monotonic()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for attempt in range(2):
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError as exc:
                if attempt == 0 and self._is_stale():
                    self.path.unlink(missing_ok=True)
                    continue
                owner = self._read_owner()
                raise MaintenanceLockError(f"Maintenance is already running ({owner}).") from exc
            payload = {
                "pid": os.getpid(),
                "started_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            }
            with os.fdopen(descriptor, "w", encoding="utf-8") as lock_file:
                json.dump(payload, lock_file, sort_keys=True)
                lock_file.write("\n")
                lock_file.flush()
                os.fsync(lock_file.fileno())
            self._owned = True
            self.wait_ms = int((monotonic() - started) * 1_000)
            return self
        raise MaintenanceLockError("Maintenance lock could not be acquired.")

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        if self._owned:
            self.path.unlink(missing_ok=True)
            self._owned = False

    def _is_stale(self) -> bool:
        try:
            age_seconds = datetime.now(UTC).timestamp() - self.path.stat().st_mtime
        except FileNotFoundError:
            return False
        return age_seconds > self.stale_seconds

    def _read_owner(self) -> str:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return f"lock file {self.path}"
        return f"pid={payload.get('pid', 'unknown')} started_at={payload.get('started_at', 'unknown')}"
