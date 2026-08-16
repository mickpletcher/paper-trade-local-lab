from __future__ import annotations

import json
from math import isfinite
from pathlib import Path
from typing import Any, cast

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.config import get_settings
from tradeforge.database.models import DataQualityEvent, PriceBar
from tradeforge.market_data.providers import get_or_create_symbol
from tradeforge.market_data.quality import validate_and_repair_ohlcv

REQUIRED_COLUMNS = ["date", "open", "high", "low", "close", "volume"]


def import_ohlcv_csv(session: Session, symbol: str, file_path: str | Path) -> int:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)

    frame = pd.read_csv(path)
    missing = set(REQUIRED_COLUMNS).difference(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

    frame = frame[REQUIRED_COLUMNS].copy()
    settings = get_settings()
    frame, findings = validate_and_repair_ohlcv(
        frame,
        max_gap_days=settings.data_quality_max_gap_days,
        max_return_ratio=settings.data_quality_max_return_ratio,
    )
    numeric_columns = ["open", "high", "low", "close", "volume"]
    for column in numeric_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if frame.isna().any().any():
        raise ValueError("CSV contains missing or invalid OHLCV data")

    for row_number, raw_row in enumerate(frame.itertuples(index=False), start=2):
        row = cast(Any, raw_row)
        prices = [float(row.open), float(row.high), float(row.low), float(row.close)]
        volume = float(row.volume)
        if not all(isfinite(price) and price > 0 for price in prices):
            raise ValueError(f"CSV row {row_number} contains a nonpositive or nonfinite price")
        if row.high < row.low or not row.low <= row.open <= row.high or not row.low <= row.close <= row.high:
            raise ValueError(f"CSV row {row_number} contains invalid OHLC relationships")
        if not isfinite(volume) or volume < 0 or not volume.is_integer():
            raise ValueError(f"CSV row {row_number} volume must be a nonnegative integer")

    frame = frame.sort_values("date")
    db_symbol = get_or_create_symbol(session, symbol)
    for finding in findings:
        session.add(
            DataQualityEvent(
                symbol_id=db_symbol.id,
                source_file=path.name,
                severity=finding.severity,
                issue_type=finding.issue_type,
                message=finding.message,
                repair_action=finding.repair_action,
                payload_json=json.dumps({"source": str(path)}, sort_keys=True),
            )
        )
    imported = 0

    for raw_row in frame.itertuples(index=False):
        row = cast(Any, raw_row)
        timestamp = row.date.to_pydatetime()
        bar = session.scalar(
            select(PriceBar).where(PriceBar.symbol_id == db_symbol.id, PriceBar.timestamp == timestamp)
        )
        values = {
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "volume": int(row.volume),
        }
        if bar is None:
            session.add(PriceBar(symbol_id=db_symbol.id, timestamp=timestamp, **values))
        else:
            for key, value in values.items():
                setattr(bar, key, value)
        imported += 1

    session.flush()
    return imported
