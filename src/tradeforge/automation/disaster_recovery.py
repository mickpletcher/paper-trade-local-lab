from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from tradeforge.automation.maintenance import restore_backup_drill
from tradeforge.config import Settings, get_settings


def run_disaster_recovery_drill(
    settings: Settings | None = None,
    now: datetime | None = None,
) -> dict[str, object]:
    current_settings = settings or get_settings()
    backups = sorted(current_settings.backup_dir.glob("tradeforge-*.db"), key=lambda path: path.name, reverse=True)
    if not backups:
        raise FileNotFoundError("No TradeForge backup is available for a disaster recovery drill.")
    result = measure_recovery_objectives(backups[0], current_settings, now)
    report_path = current_settings.automation_report_dir / "dr-latest.json"
    _atomic_write(report_path, json.dumps(result, indent=2, sort_keys=True) + "\n")
    result["report_path"] = str(report_path)
    return result


def measure_recovery_objectives(
    backup_path: Path,
    settings: Settings,
    now: datetime | None = None,
) -> dict[str, object]:
    current_time = _utc(now or datetime.now(timezone.utc))
    drill = restore_backup_drill(backup_path)
    backup_time = datetime.fromtimestamp(backup_path.stat().st_mtime, timezone.utc)
    recovery_point_age_seconds = max((current_time - backup_time).total_seconds(), 0.0)
    recovery_time_value = drill["recovery_time_ms"]
    if not isinstance(recovery_time_value, (int, float)) or isinstance(recovery_time_value, bool):
        raise TypeError("Recovery drill duration must be numeric.")
    recovery_time_seconds = float(recovery_time_value) / 1_000
    rpo_met = recovery_point_age_seconds <= settings.dr_rpo_target_seconds
    rto_met = recovery_time_seconds <= settings.dr_rto_target_seconds
    return {
        **drill,
        "backup_path": str(backup_path),
        "measured_at": current_time.isoformat(),
        "recovery_point_age_seconds": round(recovery_point_age_seconds, 3),
        "recovery_time_seconds": round(recovery_time_seconds, 3),
        "rpo_target_seconds": settings.dr_rpo_target_seconds,
        "rto_target_seconds": settings.dr_rto_target_seconds,
        "rpo_met": rpo_met,
        "rto_met": rto_met,
        "objectives_met": rpo_met and rto_met,
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
