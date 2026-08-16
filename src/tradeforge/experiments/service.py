from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.database.models import Experiment, ExperimentArtifact, PriceBar, StrategyRun


def track_strategy_run(
    session: Session,
    strategy_run_id: str,
    strategy_version: str,
    artifacts: Mapping[str, Path] | None = None,
) -> Experiment:
    run = session.get(StrategyRun, strategy_run_id)
    if run is None:
        raise ValueError(f"Unknown strategy run: {strategy_run_id}")
    existing = session.scalar(select(Experiment).where(Experiment.strategy_run_id == strategy_run_id))
    if existing is not None:
        return existing
    normalized_version = strategy_version.strip()
    if not normalized_version:
        raise ValueError("strategy_version must not be empty.")
    dataset_digest = _dataset_sha256(session, run)
    experiment = Experiment(
        tenant_id=run.tenant_id,
        strategy_run_id=run.id,
        strategy_version=normalized_version,
        parameters_json=run.parameters_json,
        dataset_sha256=dataset_digest,
    )
    session.add(experiment)
    session.flush()
    for artifact_type, artifact_path in sorted((artifacts or {}).items()):
        normalized_type = artifact_type.strip().lower()
        path = Path(artifact_path)
        if not normalized_type or not path.is_file():
            raise ValueError(f"Experiment artifact is invalid: {artifact_type}={path}")
        session.add(
            ExperimentArtifact(
                experiment_id=experiment.id,
                artifact_type=normalized_type,
                path=str(path),
                sha256=_file_sha256(path),
            )
        )
    session.flush()
    return experiment


def _dataset_sha256(session: Session, run: StrategyRun) -> str:
    statement = (
        select(
            PriceBar.timestamp,
            PriceBar.open,
            PriceBar.high,
            PriceBar.low,
            PriceBar.close,
            PriceBar.volume,
        )
        .where(
            PriceBar.symbol_id == run.symbol_id,
            PriceBar.timestamp >= run.start_date,
            PriceBar.timestamp <= run.end_date,
        )
        .order_by(PriceBar.timestamp.asc())
        .execution_options(yield_per=1_000)
    )
    digest = hashlib.sha256()
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"))
    digest.update(b"[")
    first = True
    for timestamp, open_price, high, low, close, volume in session.execute(statement):
        if not first:
            digest.update(b",")
        first = False
        payload = {
            "timestamp": timestamp.isoformat(),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }
        for chunk in encoder.iterencode(payload):
            digest.update(chunk.encode("utf-8"))
    digest.update(b"]")
    return digest.hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
