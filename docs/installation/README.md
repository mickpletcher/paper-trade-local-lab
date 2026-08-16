# Installation

TradeForge supports Python 3.11 or newer. Python 3.11 is the dependency lock reference version. Strict typing covers Python 3.11 through 3.14, and tests cover Python 3.11, 3.13, and 3.14.

## Local Python

### Windows PowerShell

```powershell
git clone https://github.com/mickpletcher/paper-trade-local-lab.git
Set-Location paper-trade-local-lab
py -3.13 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python scripts/bootstrap.py
Copy-Item .env.example .env
tradeforge init-db
tradeforge seed-sample-data
```

### Linux Or macOS

```bash
git clone https://github.com/mickpletcher/paper-trade-local-lab.git
cd paper-trade-local-lab
python3 -m venv .venv
. .venv/bin/activate
python scripts/bootstrap.py
cp .env.example .env
tradeforge init-db
tradeforge seed-sample-data
```

Run a first backtest with the command in the root [README](../../README.md#quick-start).

## Docker

```bash
cp .env.example .env
docker compose up --build -d
```

Open `http://localhost:8000/docs`. The compose file mounts `./data` into the container and restarts the service unless it is explicitly stopped.

The image runs as UID 10001 and uses `/health` for container health. Ensure the host `data` directory is writable by that UID before starting Compose.

The API has no authentication. Do not publish port `8000` to an untrusted network without an authenticated reverse proxy and firewall controls.

## Upgrade

After pulling a newer commit:

```bash
python scripts/bootstrap.py
tradeforge init-db
```

`init-db` applies pending Alembic migrations. Back up `data/tradeforge.db` before upgrading important local data.

## Troubleshooting

* Confirm the virtual environment is active and `python --version` is 3.11 or newer.
* Confirm `.env` exists when using Docker Compose.
* Ensure the host user can write to `data/`.
* Run `tradeforge db-current` and compare the current and head migration revisions.
* Run `tradeforge doctor` for dependency drift and lock provenance.
* Run `tradeforge health` for the latest maintenance, backup, import, quarantine, and database state.
* Use [SUPPORT.md](../../SUPPORT.md) when opening a reproducible issue.

## Cross Links

* [configuration](../configuration/README.md)
* [automation](../automation/README.md)
