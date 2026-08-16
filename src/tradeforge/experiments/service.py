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
    bars = list(
        session.scalars(
            select(PriceBar)
            .where(
                PriceBar.symbol_id == run.symbol_id,
                PriceBar.timestamp >= run.start_date,
                PriceBar.timestamp <= run.end_date,
            )
            .order_by(PriceBar.timestamp.asc())
        )
    )
    dataset = [
        {
            "timestamp": bar.timestamp.isoformat(),
            "open": bar.open,
            "high": bar.high,
            "low": bar.low,
            "close": bar.close,
            "volume": bar.volume,
        }
        for bar in bars
    ]
    dataset_digest = hashlib.sha256(
        json.dumps(dataset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
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
                sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            )
        )
    session.flush()
    return experiment
