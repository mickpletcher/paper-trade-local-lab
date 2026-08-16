from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class DataQualityFinding:
    severity: str
    issue_type: str
    message: str
    repair_action: str | None = None


def validate_and_repair_ohlcv(
    frame: pd.DataFrame,
    *,
    max_gap_days: int,
    max_return_ratio: float,
) -> tuple[pd.DataFrame, list[DataQualityFinding]]:
    findings: list[DataQualityFinding] = []
    raw_dates = frame["date"].astype(str)
    naive_count = int(raw_dates.str.match(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2})?)?$").sum())
    if naive_count:
        findings.append(
            DataQualityFinding(
                "info",
                "timezone_normalized",
                f"Normalized {naive_count} timezone-naive timestamp(s) to UTC",
                "assume_utc",
            )
        )

    repaired = frame.copy()
    repaired["date"] = pd.to_datetime(repaired["date"], utc=True, errors="coerce")
    duplicate_count = int(repaired.duplicated(subset=["date"], keep="last").sum())
    if duplicate_count:
        repaired = repaired.drop_duplicates(subset=["date"], keep="last")
        findings.append(
            DataQualityFinding(
                "warning",
                "duplicate_timestamp",
                f"Removed {duplicate_count} duplicate timestamp row(s)",
                "keep_last",
            )
        )

    repaired = repaired.sort_values("date").reset_index(drop=True)
    valid_dates = repaired["date"].dropna()
    if len(valid_dates) > 1:
        largest_gap = valid_dates.diff().dropna().max()
        if largest_gap > pd.Timedelta(days=max_gap_days):
            findings.append(
                DataQualityFinding(
                    "warning",
                    "timestamp_gap",
                    f"Largest timestamp gap is {largest_gap}",
                    "record_only",
                )
            )

    numeric_close = pd.to_numeric(repaired["close"], errors="coerce")
    returns = numeric_close.pct_change(fill_method=None).abs()
    outliers = returns[returns > max_return_ratio]
    if not outliers.empty:
        row_numbers = ", ".join(str(int(index) + 2) for index in outliers.index)
        raise ValueError(f"CSV contains close price outliers above {max_return_ratio:.0%} on row(s): {row_numbers}")

    return repaired, findings
