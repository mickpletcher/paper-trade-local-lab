from __future__ import annotations

from math import isfinite
from pathlib import Path
from typing import Any, cast

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.database.models import PriceBar
from tradeforge.market_data.providers import get_or_create_symbol

REQUIRED_COLUMNS = {"date", "open", "high", "low", "close", "volume"}


def import_ohlcv_csv(session: Session, symbol: str, file_path: str | Path) -> int:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(path)

    frame = pd.read_csv(path)
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

    frame = frame[list(REQUIRED_COLUMNS)].copy()
    frame["date"] = pd.to_datetime(frame["date"], utc=True, errors="coerce")
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
