# TradeForge

[![CI](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/ci.yml)
[![Docs](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/docs.yml/badge.svg)](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/docs.yml)
[![Security](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/security.yml/badge.svg)](https://github.com/mickpletcher/paper-trade-local-lab/actions/workflows/security.yml)
[![Python](https://img.shields.io/badge/python-3.11--3.14-blue.svg)](./pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](./LICENSE)

TradeForge is a local paper trading and historical backtesting lab. It imports price data, runs simulated strategies, stores results in SQLite, values simulated positions with optional live quotes, and automates local maintenance.

TradeForge does not connect to a brokerage account and does not place live trades.

> [!WARNING]
> TradeForge is research software. It is not financial advice. Backtest results are not a promise of future performance. API authentication is disabled by default, so keep the API on your own computer unless you deliberately enable API keys.

## Contents

* [What TradeForge does](#what-tradeforge-does)
* [Before you start](#before-you-start)
* [Windows installation](#windows-installation)
* [First backtest](#first-backtest)
* [Portfolio and research workflows](#portfolio-and-research-workflows)
* [Understanding results](#understanding-results)
* [Files and folders](#files-and-folders)
* [Configuration](#configuration)
* [Importing your own price data](#importing-your-own-price-data)
* [Using live quotes](#using-live-quotes)
* [Using the local API](#using-the-local-api)
* [Automated maintenance](#automated-maintenance)
* [Health checks and failure recovery](#health-checks-and-failure-recovery)
* [Backups and database restoration](#backups-and-database-restoration)
* [Corporate actions](#corporate-actions)
* [Docker setup](#docker-setup)
* [Updating, resetting, and removing TradeForge](#updating-resetting-and-removing-tradeforge)
* [Troubleshooting](#troubleshooting)
* [Command reference](#command-reference)
* [Developer validation](#developer-validation)
* [Further documentation](#further-documentation)

## What TradeForge does

TradeForge currently provides:

* a Windows friendly command line interface
* historical OHLCV CSV import with data quality checks
* bundled AAPL sample data for a no credential first run
* a moving average crossover strategy
* allocated multi symbol portfolio backtests
* event ordered bars, ticks, news, and system messages
* rolling risk, beta, factor, and market regime analytics
* immutable experiment records with dataset and report hashes
* allowlisted strategy, broker, indicator, and report plugins
* market, limit, stop, and stop limit order simulation
* configurable commissions, slippage, volume limits, and quantity increments
* position, exposure, drawdown, order size, and kill switch risk controls
* SQLite storage with Alembic schema migrations
* Markdown backtest reports
* optional Alpaca live quote retrieval for local valuation
* a read only FastAPI service and local dashboard with optional tenant API keys
* unattended import processing, backups, restore drills, reports, retries, and alerts
* a Windows Task Scheduler installer for daily maintenance

The current limitations matter:

* only one built in strategy is available
* portfolio runs isolate capital into one single symbol engine per allocation
* execution uses completed OHLCV bars, not an exchange order book
* money is stored as floating point values
* live quote retrieval supports Alpaca only
* API authentication is opt in and the API has no pagination or versioning

See [ASSESSMENT.md](./ASSESSMENT.md) for the current one minute project status.

## Before you start

### Terms used in this manual

* **Repository** means the `paper-trade-local-lab` project folder.
* **PowerShell** means the blue or black command window where you type commands.
* **Project root** means the repository folder containing `README.md` and `pyproject.toml`.
* **Virtual environment** means the private `.venv` Python installation used only by this project.
* **CLI** means the `tradeforge` command line program.
* **OHLCV** means open, high, low, close, and volume price data.
* **Paper trading** means simulated trading with no real orders or money.

Unless a step says otherwise, run every command from the project root with the virtual environment activated.

### Required Windows software

Install these programs before continuing:

1. Git for Windows.
2. Python 3.11, 3.12, 3.13, or 3.14. Python 3.13 is a good default.
3. Node.js with npm. The bootstrap process uses npm for Markdown validation tools.
4. PowerShell. Windows PowerShell 5.1 works, but PowerShell 7 is recommended.

Docker Desktop is optional. It is needed only for the container setup.

Open PowerShell and verify the required tools:

```powershell
git --version
py --version
node --version
npm --version
```

Each command must print a version. If a command is not recognized, install or repair that program, close PowerShell, open a new PowerShell window, and try again.

List the Python versions Windows can find:

```powershell
py -0p
```

Use one of the supported versions shown in that list.

### Safe operating rules

* Never commit `.env`. It can contain credentials.
* Never commit files under `data/`. They can contain market data and research results.
* Never expose port 8000 to the internet without an authenticated reverse proxy.
* Stop the API and scheduled maintenance before manually replacing the database.
* Keep a backup before an upgrade, reset, or manual database restore.
* Do not use research results as the only basis for a financial decision.

## Windows installation

### Step 1: Download the repository

Choose a folder where you keep source code. This example uses your Documents folder:

```powershell
Set-Location "$env:USERPROFILE\Documents"
git clone https://github.com/mickpletcher/paper-trade-local-lab.git
Set-Location .\paper-trade-local-lab
```

If you already cloned the repository, open PowerShell in that folder and confirm the location:

```powershell
Get-Location
Get-ChildItem README.md, pyproject.toml
```

Both files must be listed.

### Step 2: Create the Python virtual environment

This example uses Python 3.13:

```powershell
py -3.13 -m venv .venv
```

If Python 3.13 is not installed, replace `3.13` with another supported version from `py -0p`.

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`.

You must activate this environment every time you open a new PowerShell window to work with TradeForge.

### Step 3: Install locked dependencies

Run the repository bootstrap:

```powershell
python scripts/bootstrap.py
```

The bootstrap performs four jobs:

1. installs the locked Pip version
2. installs TradeForge and its development tools into `.venv`
3. installs the locked Node validation tools
4. runs `tradeforge doctor` to compare the environment with the lock

Installation is successful when the command ends without a red traceback and the final doctor output reports a healthy environment and verified provenance.

### Step 4: Create the local configuration

Copy the safe example configuration:

```powershell
Copy-Item .env.example .env
```

The sample backtest does not need an Alpaca account or API credentials. Leave the two Alpaca credential values blank until you want live quote refresh.

The `.env` file is ignored by Git. Do not override that protection.

### Step 5: Create and verify the database

Create or migrate the SQLite database:

```powershell
tradeforge init-db
tradeforge db-current
```

The first command should print:

```text
Initialized TradeForge database.
```

The second command prints JSON. `current_version` and `head_version` should match. The database is stored at `data\tradeforge.db` unless `.env` changes its location.

### Step 6: Load the sample data

Load the bundled AAPL dataset:

```powershell
tradeforge seed-sample-data
```

Expected result:

```text
Seeded 8 sample bars for AAPL.
```

It is safe to run this command again. Existing bars for the same timestamps are updated.

### Step 7: Verify the installed command

```powershell
tradeforge --help
tradeforge doctor
```

The help command should show the TradeForge command list. Doctor exits with code 0 only when the active environment matches the lock and the lock provenance file is valid.

You can display the last exit code in PowerShell:

```powershell
$LASTEXITCODE
```

`0` means success. Any other value means the command reported a problem.

## First backtest

Run this exact sample from the project root:

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
```

The command prints a JSON object with four top level fields:

* `strategy_run_id` is the unique ID for this backtest.
* `experiment_id` is the immutable input and artifact provenance record.
* `metrics` contains the calculated performance values.
* `report_path` points to the generated Markdown report.

The report is written to `data\reports\<strategy_run_id>.md`.

Inspect the simulated activity:

```powershell
tradeforge show-orders
tradeforge show-positions
tradeforge show-pnl
```

Open the newest Markdown report in Notepad:

```powershell
$latestBacktestReport = Get-ChildItem .\data\reports\*.md |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
notepad $latestBacktestReport.FullName
```

The sample is deliberately small. It proves that installation, migrations, data import, strategy execution, simulated orders, result persistence, and report generation work. It is not a meaningful strategy evaluation.

## Portfolio and research workflows

Load another sample symbol before trying the portfolio command:

```powershell
tradeforge seed-sample-data --symbol MSFT
```

Run the same strategy across two independently funded sleeves:

```powershell
tradeforge run-portfolio-backtest --symbol AAPL --symbol MSFT --start 2023-01-01 --end 2023-01-08 --total-cash 100000 --short-window 2 --long-window 3 --order-size 2
```

The default `equal` allocation gives each symbol half of the cash. Use fixed weights when you need an explicit allocation. The JSON must contain every requested symbol and the values must total exactly `1`:

```powershell
tradeforge run-portfolio-backtest --symbol AAPL --symbol MSFT --start 2023-01-01 --end 2023-01-08 --total-cash 100000 --allocation fixed --weights-json '{"AAPL":0.7,"MSFT":0.3}' --short-window 2 --long-window 3 --order-size 2
```

Portfolio output includes total starting cash, ending equity, return, per symbol allocations, one strategy run and report per symbol, and the number of processed lifecycle events. Each sleeve has isolated cash. This is not yet a shared account where one symbol can consume another symbol's unused capital.

Every completed backtest automatically creates an immutable experiment record. It hashes the exact stored bars used by the run and the generated report. List the records without exposing report contents:

```powershell
tradeforge show-experiments
```

Calculate rolling risk, beta, and market regimes from stored bars:

```powershell
tradeforge analyze-symbol --symbol AAPL --benchmark-symbol MSFT --window 2
```

Use a larger window, such as `20`, with real daily history. Both symbols must cover the same number of stored returns. The result labels each price as `insufficient`, `bull`, `bear`, `sideways`, or `high_volatility` based on the configured rolling window.

Confirm the vectorized moving average path stays inside its runtime budget:

```powershell
tradeforge benchmark-performance --rows 100000 --maximum-seconds 5
```

List built in plugins and available connector adapters:

```powershell
tradeforge list-plugins
tradeforge list-connectors
```

Connector entries describe request and normalization adapters only. `live_order_routing` is `false` for every connector. TradeForge never transmits the paper signals they produce.

## Understanding results

The most important report fields are:

| Field | Meaning |
| --- | --- |
| `starting_cash` | Simulated cash available when the run began. |
| `ending_equity` | Final cash plus the last bar value of any open position. |
| `total_return` | Percentage change expressed as a decimal. `0.05` means 5 percent. |
| `cagr` | Annualized compound return. Very short tests can make this misleading. |
| `volatility` | Annualized variation in periodic returns. Higher is less stable. |
| `sharpe_ratio` | Return divided by total variability using a zero risk free rate. |
| `sortino_ratio` | Return divided by downside variability using a zero risk free rate. |
| `max_drawdown` | Largest peak to trough equity decline. `-0.10` means a 10 percent decline. |
| `number_of_fills` | Individual simulated executions. One order can have several fills. |
| `number_of_trades` | Fully closed position lifecycles. |
| `open_trades` | Position lifecycles still open at the end. |
| `win_rate` | Winning closed trades divided by all closed trades. |
| `profit_factor` | Gross winning P/L divided by gross losing P/L. |
| `exposure` | Fraction of snapshots where capital was in a position. |
| `buy_and_hold_return` | Return from holding the symbol over the same dates. |
| `realized_pnl` | Profit or loss from closed simulated positions. |
| `unrealized_pnl` | Marked profit or loss still held at the final historical bar. |

A `null` value is intentional when a ratio cannot be calculated honestly. For example, profit factor is `null` when there are no losing trades.

Before trusting a comparison, use enough data, include realistic fees and slippage, inspect open trades, compare against buy and hold, and test periods that were not used to choose the parameters.

## Files and folders

| Path | Purpose | Commit it? |
| --- | --- | --- |
| `.env.example` | Safe inventory of supported settings. | Yes. |
| `.env` | Your local settings and optional secrets. | No. |
| `.venv\` | Project specific Python environment. | No. |
| `data\tradeforge.db` | Default SQLite database. | No. |
| `data\reports\` | Generated backtest reports. | No. |
| `data\imports\` | Pending files for automated import. | No. |
| `data\imports\processed\` | Timestamped successful imports. | No. |
| `data\imports\quarantine\` | Failed imports and error details. | No. |
| `data\backups\` | Integrity checked database backups. | No. |
| `data\automation\latest.json` | Latest maintenance result. | No. |
| `docs\` | Detailed product and operator documentation. | Yes. |
| `src\tradeforge\` | Application source code. | Yes. |
| `tests\` | Automated tests. | Yes. |

Local data and secrets are excluded through `.gitignore` and `.dockerignore`. Check `git status --short` before every commit.

## Configuration

TradeForge reads `.env` when a CLI or API process starts. Stop and restart a long running process after changing `.env`.

### Safe starter configuration

The copied `.env.example` works for sample data, local backtesting, and maintenance when there are no open positions. The main defaults are:

```text
Starting cash:        $100,000
Fixed fee per order:  $1.00
Slippage:             1 basis point
Bar fill limit:       25 percent of volume
Quantity increment:   1 whole share
Database:             data/tradeforge.db
Backup retention:     7 files
Report retention:     30 timestamped reports
API metrics:          disabled
```

### Execution controls

Edit `.env` in VSCode or Notepad. These settings change simulated execution:

* `TRADEFORGE_STARTING_CASH` sets initial simulated cash.
* `TRADEFORGE_COMMISSION_MODEL` accepts `fixed` or `per_share`.
* `TRADEFORGE_FEE_PER_ORDER` sets the fixed commission.
* `TRADEFORGE_COMMISSION_PER_SHARE` and `TRADEFORGE_COMMISSION_MINIMUM` configure per share commissions.
* `TRADEFORGE_SLIPPAGE_BPS` sets default adverse fill movement in basis points.
* `TRADEFORGE_SYMBOL_SLIPPAGE_RULES_JSON` sets ticker specific overrides such as `{"AAPL": 2.5}`.
* `TRADEFORGE_MAX_BAR_FILL_RATIO` caps aggregate fills against one bar from `0` through `1`.
* `TRADEFORGE_QUANTITY_INCREMENT` defaults to `1` for whole shares.

### Risk controls

The following settings reject simulated orders outside the declared policy:

* `TRADEFORGE_RISK_MAX_ORDER_NOTIONAL`
* `TRADEFORGE_RISK_MAX_POSITION_QUANTITY`
* `TRADEFORGE_RISK_MAX_GROSS_EXPOSURE`
* `TRADEFORGE_RISK_MAX_DRAWDOWN_RATIO`
* `TRADEFORGE_RISK_KILL_SWITCH`

Set `TRADEFORGE_RISK_KILL_SWITCH=true` to reject new simulated execution. This does not delete existing research data.

See [the configuration reference](./docs/configuration/README.md) for every setting and valid range.

## Importing your own price data

### Required CSV format

The first line must contain these exact lowercase column names:

```csv
date,open,high,low,close,volume
2026-01-02,100.00,103.00,99.50,102.25,1250000
2026-01-03,102.20,104.10,101.80,103.75,1100000
```

Each row must meet these rules:

* `date` must be parseable as a date or datetime
* prices must be finite and greater than zero
* `high` must not be below `low`
* `open` and `close` must be between `low` and `high`
* `volume` must be a nonnegative whole number
* extreme returns beyond the configured quality threshold are rejected

TradeForge sorts rows by date, normalizes timestamps, repairs safe duplicate timestamp cases, records quality findings, and updates an existing symbol and timestamp instead of creating a duplicate bar.

### Direct one file import

Import a file immediately:

```powershell
tradeforge import-csv --symbol MSFT --file "C:\MarketData\msft-daily.csv"
```

Success looks like:

```text
Imported 250 bars for MSFT.
```

Use your actual row count and path. Then run a backtest with dates covered by that file:

```powershell
tradeforge run-backtest --strategy moving-average-cross --symbol MSFT --start 2025-01-01 --end 2025-12-31
```

### Automated import queue

For unattended import, name each file after its ticker and copy it to `data\imports`:

```powershell
Copy-Item "C:\MarketData\MSFT.csv" .\data\imports\MSFT.csv
tradeforge run-maintenance
```

Successful files move to `data\imports\processed` with a UTC timestamp and SHA-256 recorded in the maintenance report.

Failed files move to `data\imports\quarantine`. A matching `.error.json` sidecar explains the failure. Maintenance exits with code 1 so a scheduler or monitoring tool can detect it.

## Using live quotes

Live quotes are optional and are used only for local valuation. They do not send orders to Alpaca.

### Configure Alpaca credentials

Open `.env` and set:

```text
TRADEFORGE_ALPACA_API_KEY_ID=your_key_id
TRADEFORGE_ALPACA_API_SECRET_KEY=your_secret_key
TRADEFORGE_ALPACA_FEED=iex
```

Do not add quotes around the values. Do not paste the completed `.env` into an issue, chat, report, or commit.

### Refresh and inspect quotes

The symbol must already exist through sample data or CSV import:

```powershell
tradeforge refresh-quotes --symbol AAPL
tradeforge show-quotes
tradeforge show-valuation
```

Refresh more than one symbol by repeating the option:

```powershell
tradeforge refresh-quotes --symbol AAPL --symbol MSFT
```

Without `--symbol`, TradeForge refreshes symbols with open positions. It fails clearly when neither explicit symbols nor open positions exist.

Quote output distinguishes market timestamp age from retrieval age and marks stale data. Retries use bounded exponential backoff with jitter. Repeated provider failures open a persistent circuit breaker that closes itself after the configured reset period.

## Using the local API

Start the API from an activated environment:

```powershell
tradeforge start-api
```

Keep that PowerShell window open. Use `Ctrl+C` to stop the server.

Open these local pages in a browser:

* API documentation: `http://127.0.0.1:8000/docs`
* API health: `http://127.0.0.1:8000/health`
* local dashboard: `http://127.0.0.1:8000/dashboard`

You can also test health from another PowerShell window:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Current read only endpoints include:

* `/health`
* `/symbols`
* `/quotes`
* `/portfolio`
* `/positions`
* `/orders`
* `/strategy-runs`
* `/experiments`
* `/dashboard`
* `/metrics` when metrics are enabled

Use a different local port if 8000 is occupied:

```powershell
tradeforge start-api --port 8001
```

Authentication is disabled by default for the simplest loopback only first run. Enable it before allowing another device to reach the API.

Create a tenant and a least privilege API identity:

```powershell
$tenant = tradeforge create-tenant --name personal | ConvertFrom-Json
$identity = tradeforge create-api-key --tenant-id $tenant.id --name local-dashboard --role viewer | ConvertFrom-Json
$identity.api_key
```

Copy the printed `tf_...` secret into a password manager. TradeForge stores only a per key salted PBKDF2-HMAC-SHA-256 verifier and cannot display the secret again. Do not place the secret in Git, screenshots, shell transcripts, URLs, or issue comments.

Set this value in `.env`, then restart the API:

```text
TRADEFORGE_API_AUTH_ENABLED=true
```

The health and interactive documentation routes remain public. Other routes require the configured `X-TradeForge-Key` header. Test the new identity from PowerShell:

```powershell
$headers = @{ "X-TradeForge-Key" = $identity.api_key }
Invoke-RestMethod http://127.0.0.1:8000/positions -Headers $headers
```

Roles are cumulative:

* `viewer` reads tenant scoped research data and the dashboard.
* `operator` also reads process metrics when metrics are enabled.
* `admin` currently has the same read access and is reserved for future administrative endpoints.

Each key can see only positions, orders, runs, experiments, and valuation for its tenant. Symbols and quotes are shared market data. Give each automated process its own key so you can revoke it without interrupting another process.

Rotate a key before it expires:

```powershell
$replacement = tradeforge rotate-api-key --api-key-id $identity.id | ConvertFrom-Json
$replacement.api_key
```

Rotation revokes the old key immediately. Update the caller with the replacement secret before its next request. Revoke a compromised or retired key:

```powershell
tradeforge revoke-api-key --api-key-id $replacement.id
tradeforge show-api-keys --tenant-id $tenant.id
```

The metadata listing never returns stored secrets. Keys expire after 90 days by default. Change `TRADEFORGE_API_KEY_ROTATION_DAYS` before issuing a key or pass `--expires-in-days` to the creation or rotation command.

Do not use `--host 0.0.0.0` on a normal workstation. API keys do not provide TLS. If the service must cross a network, put it behind an HTTPS reverse proxy and retain the API key requirement. Compose uses `0.0.0.0` inside the container but binds the host side to loopback only.

## Automated maintenance

### Maintenance sequence

One command performs the complete unattended workflow:

```powershell
tradeforge run-maintenance
```

It performs these actions in order:

1. acquires an atomic maintenance lock
2. creates or migrates the configured database
3. imports every `data\imports\<TICKER>.csv`
4. archives successful imports and quarantines failures
5. refreshes live quotes for open positions
6. checks SQLite integrity, lock response, and WAL state
7. creates and integrity checks an online SQLite backup
8. restores that backup into memory as a recovery drill
9. applies backup and report retention
10. writes a timestamped report and `data\automation\latest.json`

A failed run exits with code 1 and still tries to write a detailed local report. Optional HTTPS webhook, Teams, and SMTP settings can report failures without exposing the full local report.

If open positions exist, configure Alpaca credentials before scheduling maintenance. Quote refresh is part of the same fail closed workflow.

### Inspect the latest maintenance report

```powershell
$maintenance = Get-Content .\data\automation\latest.json -Raw | ConvertFrom-Json
$maintenance.status
$maintenance.backup_path
$maintenance.restore_drill
```

`status` should be `success`. The restore drill should report `verified`.

### Install daily Windows scheduling

First run maintenance manually and fix any error. Then install the task from an activated environment:

```powershell
.\scripts\Install-TradeForgeScheduledTask.ps1 -DailyAt "02:00" -RunNow
```

This creates `TradeForge Daily Maintenance`. It runs the exact `tradeforge.exe` from the current virtual environment with the repository as its working directory.

The task:

* runs every day at the selected local time
* starts a missed run when the computer becomes available
* retries a failed run three times at five minute intervals
* stops a run after one hour

Do not move the repository or delete `.venv` while the task is installed. Reinstall the task after either path changes.

If registration returns Access Denied, open PowerShell as Administrator, activate the environment, return to the project root, and repeat the installer command.

### Verify the scheduled task

```powershell
Get-ScheduledTask -TaskName "TradeForge Daily Maintenance"
Get-ScheduledTaskInfo -TaskName "TradeForge Daily Maintenance"
```

`LastTaskResult` equal to `0` means the last completed run succeeded. Also verify `data\automation\latest.json` because it contains the application level result.

Start a test run:

```powershell
Start-ScheduledTask -TaskName "TradeForge Daily Maintenance"
Start-Sleep -Seconds 5
Get-ScheduledTaskInfo -TaskName "TradeForge Daily Maintenance"
```

### Pause, resume, or remove scheduling

```powershell
Disable-ScheduledTask -TaskName "TradeForge Daily Maintenance"
Enable-ScheduledTask -TaskName "TradeForge Daily Maintenance"
Unregister-ScheduledTask -TaskName "TradeForge Daily Maintenance" -Confirm:$false
```

The removal command deletes only the scheduled task. It does not delete the repository, database, reports, or backups.

## Health checks and failure recovery

### Read local health

```powershell
tradeforge health
$LASTEXITCODE
```

Health is `healthy` only when the database integrity check passes and the latest maintenance report says `success`. Before the first maintenance run, `attention_required` is expected even if installation is correct.

The health output also reports:

* database existence, integrity, and journal mode
* latest maintenance details
* backup count and newest backup
* pending and quarantined import counts
* whether the maintenance lock exists

Use the exit code in scripts and monitoring. `0` is healthy. `1` requires attention.

### Recover a quarantined import

List failed files:

```powershell
Get-ChildItem .\data\imports\quarantine
```

Read the matching error sidecar:

```powershell
Get-Content ".\data\imports\quarantine\<timestamp>-MSFT.csv.error.json"
```

Replace `<timestamp>-MSFT.csv` with the actual filename. Correct the quarantined CSV, then return it to the pending queue:

```powershell
tradeforge acknowledge-import --file "<timestamp>-MSFT.csv" --retry
tradeforge run-maintenance
```

TradeForge restores the original ticker filename from the error sidecar before retrying it.

If the file should not be retried, acknowledge and archive it:

```powershell
tradeforge acknowledge-import --file "<timestamp>-MSFT.csv"
```

### Respond to a maintenance failure

1. Run `tradeforge health`.
2. Open `data\automation\latest.json`.
3. Fix the specific reported problem.
4. Check `data\imports\quarantine` if an import failed.
5. Check Alpaca credentials and connectivity if quote refresh failed.
6. Run `tradeforge run-maintenance` manually.
7. Confirm `tradeforge health` returns exit code 0.

Do not silently delete `data\automation\maintenance.lock`. Another process may still own it. Stop duplicate TradeForge processes first. The lock automatically recovers after its configured stale interval when the recorded owner is no longer valid.

## Backups and database restoration

### Automatic backup behavior

Every successful maintenance run creates `data\backups\tradeforge-<UTC timestamp>.db`. The backup is created with SQLite's online backup API and passes an integrity check before its temporary file is promoted.

Maintenance also restores the new backup into memory, checks integrity and application table presence, and records recovery time. This drill proves the file can be opened. It does not replace the active database.

The default retention is the newest seven backups. Change `TRADEFORGE_BACKUP_RETENTION_COUNT` in `.env` to keep from 1 through 365.

List backups newest first:

```powershell
Get-ChildItem .\data\backups\tradeforge-*.db |
    Sort-Object LastWriteTime -Descending
```

Run a separate recovery objective drill at any time:

```powershell
tradeforge run-dr-drill
```

The command selects the newest backup, restores it into memory, verifies integrity and application tables, measures the backup age as recovery point age, measures restore duration, and writes `data\automation\dr-latest.json`. It returns exit code 1 when either target is missed. Defaults are a 24 hour recovery point objective and a 60 second recovery time objective:

```text
TRADEFORGE_DR_RPO_TARGET_SECONDS=86400
TRADEFORGE_DR_RTO_TARGET_SECONDS=60
```

This is a local recoverability drill. It does not protect against loss of the entire workstation. Copy verified backups to encrypted off device storage using a separate approved process.

### Manual restore procedure

Use this only when the active database is damaged or you intentionally need an older state.

1. Disable the scheduled task if it exists.

   ```powershell
   Disable-ScheduledTask -TaskName "TradeForge Daily Maintenance"
   ```

2. Stop the API with `Ctrl+C` and close any other TradeForge processes.

3. Select the newest backup and confirm the path.

   ```powershell
   $restoreSource = Get-ChildItem .\data\backups\tradeforge-*.db |
       Sort-Object LastWriteTime -Descending |
       Select-Object -First 1
   $restoreSource.FullName
   ```

4. Move the current database and its SQLite companion files into a dated archive before restoring.

   ```powershell
   $restoreStamp = Get-Date -Format "yyyyMMdd-HHmmss"
   $preRestoreArchive = ".\data\before-restore-$restoreStamp"
   New-Item -ItemType Directory -Path $preRestoreArchive
   Get-ChildItem .\data\tradeforge.db* -ErrorAction SilentlyContinue |
       Move-Item -Destination $preRestoreArchive
   ```

5. Copy the selected backup into the active database path.

   ```powershell
   Copy-Item -LiteralPath $restoreSource.FullName -Destination .\data\tradeforge.db -Force
   ```

6. Upgrade the restored schema if needed and verify it.

   ```powershell
   tradeforge init-db
   tradeforge db-current
   tradeforge run-maintenance
   tradeforge health
   ```

7. Reenable scheduling after health returns exit code 0.

   ```powershell
   Enable-ScheduledTask -TaskName "TradeForge Daily Maintenance"
   ```

The `before-restore` archive is ignored by Git. Keep it until the restored database is proven good.

For off device protection, copy verified backup files to storage you control. TradeForge does not currently encrypt or upload backups.

## Corporate actions

Corporate actions are persistent research inputs. Record them only when the symbol already exists and the effective date belongs in the historical dataset.

Record a two for one split:

```powershell
tradeforge record-corporate-action --symbol AAPL --type split --effective-at 2025-06-01 --ratio 2
```

Record a per share cash dividend:

```powershell
tradeforge record-corporate-action --symbol AAPL --type dividend --effective-at 2025-08-15 --cash-amount 0.25
```

Record a ticker change:

```powershell
tradeforge record-corporate-action --symbol ABC --type symbol_change --effective-at 2025-09-01 --new-ticker XYZ
```

Record a delisting with a simulated liquidation value per share:

```powershell
tradeforge record-corporate-action --symbol XYZ --type delisting --effective-at 2025-10-01 --cash-amount 5.00
```

Backtests apply actions in timestamp order. Splits adjust positions and pending orders. Dividends credit simulated cash. Symbol changes update the ticker. Delistings liquidate the position, cancel pending orders, close the trade, and stop later strategy execution for that symbol.

Back up the database before experimenting with corporate action records. There is no public delete command.

## Docker setup

Use Docker when you want an isolated API service instead of a local virtual environment. Docker Desktop must be installed and running.

### Start the container

```powershell
Copy-Item .env.example .env -ErrorAction SilentlyContinue
docker compose up --build --detach
docker compose ps
```

Compose builds the image, starts the API, binds it to `127.0.0.1:8000`, uses a named volume for `/app/data`, restarts after failure or reboot, runs as a nonroot user, and uses a read only root filesystem.

Open `http://127.0.0.1:8000/docs` or verify health:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

### Run CLI commands in the container

```powershell
docker compose exec tradeforge tradeforge seed-sample-data
docker compose exec tradeforge tradeforge run-backtest --strategy moving-average-cross --symbol AAPL --start 2023-01-01 --end 2023-01-08 --short-window 2 --long-window 3 --order-size 2
docker compose exec tradeforge tradeforge run-maintenance
docker compose exec tradeforge tradeforge health
```

### Inspect and stop the container

```powershell
docker compose logs --tail 100 tradeforge
docker compose down
```

`docker compose down` stops and removes the container but preserves the named data volume.

This command also deletes the named volume and all databases, reports, imports, and backups inside it:

```powershell
docker compose down --volumes
```

Do not run the volume deletion command unless you have intentionally exported anything you need.

## Updating, resetting, and removing TradeForge

### Update an existing checkout

Check for local changes first:

```powershell
git status --short
```

Do not overwrite work shown by that command. Stop the API, allow maintenance to finish, activate `.venv`, and create a current backup:

```powershell
tradeforge run-maintenance
```

Then update and validate:

```powershell
git pull --ff-only
python scripts/bootstrap.py
tradeforge init-db
tradeforge db-current
tradeforge doctor
tradeforge run-maintenance
tradeforge health
```

If the scheduled task points to a moved repository or recreated virtual environment, reinstall it.

### Recoverably reset local data

Stop the API and disable scheduled maintenance first. Move the current database and its SQLite companion files into a dated archive:

```powershell
$resetStamp = Get-Date -Format "yyyyMMdd-HHmmss"
$resetArchive = ".\data\reset-$resetStamp"
New-Item -ItemType Directory -Path $resetArchive
Get-ChildItem .\data\tradeforge.db* -ErrorAction SilentlyContinue |
    Move-Item -Destination $resetArchive
tradeforge init-db
tradeforge seed-sample-data
```

This keeps the previous database files under `data\reset-<timestamp>` so the reset can be reversed.

### Remove a local installation

1. Unregister the scheduled task if you installed it.
2. Stop the API and deactivate the environment with `deactivate`.
3. Copy any database, report, or backup you need outside the repository.
4. Delete the repository folder through File Explorer.

TradeForge has no cloud account or hosted service to cancel. Alpaca credentials remain managed in your Alpaca account.

## Troubleshooting

### `tradeforge` is not recognized

Activate the environment and retry:

```powershell
Set-Location C:\path\to\paper-trade-local-lab
.\.venv\Scripts\Activate.ps1
tradeforge --help
```

If the command is still unavailable, run:

```powershell
python -m tradeforge.cli --help
python scripts/bootstrap.py
```

### PowerShell blocks `Activate.ps1`

Allow scripts only for the current PowerShell process, then activate again:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

This does not change the machine wide execution policy.

### Bootstrap says npm is not installed

Install Node.js with npm, close PowerShell, open a new window, activate `.venv`, and rerun `python scripts/bootstrap.py`.

### Doctor reports missing, mismatched, or undeclared packages

First rerun the bootstrap. If drift remains, preserve the old environment and create a clean one:

```powershell
deactivate
Move-Item .venv .venv-old
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python scripts/bootstrap.py
```

Delete `.venv-old` through File Explorer only after the clean environment passes `tradeforge doctor`.

### Database tables are missing

```powershell
tradeforge init-db
tradeforge db-current
```

The current and head migration versions should match.

### A backtest reports an unknown symbol

Load the sample or import your file before running the backtest:

```powershell
tradeforge seed-sample-data --symbol AAPL
tradeforge import-csv --symbol MSFT --file "C:\MarketData\msft-daily.csv"
```

### A backtest reports missing bars or an invalid date range

Use ISO dates, make the start earlier than the end, and choose dates covered by the imported file. The bundled sample covers 2023-01-01 through 2023-01-08.

### Quote refresh reports missing Alpaca credentials

Set both credential values in `.env`, save the file, and run the command again in a new process. Never print the values while troubleshooting.

### Quote refresh says the circuit is open

The provider failed repeatedly. Read `data\automation\quote-circuit.json`, fix the credential or connectivity problem, and wait for `TRADEFORGE_QUOTE_CIRCUIT_RESET_SECONDS` before retrying. Do not create an aggressive retry loop.

### Health says `attention_required`

This is expected before the first maintenance run. Otherwise read `data\automation\latest.json`, resolve the reported error, run maintenance again, and repeat health.

### Maintenance says it is already running

Check Task Manager and Task Scheduler for another TradeForge process. Wait for it to finish. A valid lock prevents overlapping imports and backups. Stale lock recovery is automatic when the owner is gone and the configured stale interval has passed.

### SQLite reports that the database is locked

Stop duplicate API, CLI, and scheduled processes. Wait for the current operation to finish, then retry. `TRADEFORGE_SQLITE_BUSY_TIMEOUT_MS` controls the bounded wait and defaults to 5000 milliseconds.

### The API port is already in use

Start on another loopback port:

```powershell
tradeforge start-api --host 127.0.0.1 --port 8001
```

### Docker Compose says `.env` is missing

```powershell
Copy-Item .env.example .env
docker compose up --build --detach
```

### The scheduled task returns a nonzero result

Activate the same virtual environment, run `tradeforge run-maintenance` manually, and read `data\automation\latest.json`. The manual run exposes the same failure without waiting for Task Scheduler.

### A Markdown validation command cannot find Markdownlint

Run the full bootstrap or install the declared Node packages:

```powershell
npm ci --ignore-scripts
.\scripts\Test-Markdown.ps1
```

If the problem is not covered here, read [SUPPORT.md](./SUPPORT.md) before opening an issue. Remove credentials, private data, and local paths from any shared logs.

## Command reference

| Command | Purpose |
| --- | --- |
| `tradeforge init-db` | Create or migrate the configured database. |
| `tradeforge db-current` | Show current and head database revisions. |
| `tradeforge db-revision` | Developer command to create an Alembic revision. |
| `tradeforge import-csv` | Import one OHLCV CSV immediately. |
| `tradeforge seed-sample-data` | Load the bundled eight row AAPL sample. |
| `tradeforge run-backtest` | Run one historical strategy simulation. |
| `tradeforge run-portfolio-backtest` | Run allocated backtests across repeated symbols. |
| `tradeforge analyze-symbol` | Calculate rolling risk, beta, factor, and regime analytics. |
| `tradeforge benchmark-performance` | Enforce the vectorized signal runtime budget. |
| `tradeforge list-plugins` | List built in and explicitly allowlisted plugins. |
| `tradeforge list-connectors` | List connector capabilities and routing safety state. |
| `tradeforge refresh-quotes` | Retrieve and store Alpaca quotes. |
| `tradeforge run-maintenance` | Run imports, quotes, health checks, backup, restore drill, and reporting. |
| `tradeforge run-dr-drill` | Measure latest backup recovery point and recovery time objectives. |
| `tradeforge create-tenant` | Create an isolated research and API tenant. |
| `tradeforge create-api-key` | Issue a time limited least privilege API identity secret once. |
| `tradeforge rotate-api-key` | Revoke one key and issue its replacement. |
| `tradeforge revoke-api-key` | Revoke an API identity immediately. |
| `tradeforge show-api-keys` | List identity metadata without secrets. |
| `tradeforge show-experiments` | List immutable backtest provenance records. |
| `tradeforge record-corporate-action` | Store a split, dividend, symbol change, or delisting. |
| `tradeforge acknowledge-import` | Archive or retry one quarantined import. |
| `tradeforge health` | Return exit coded database and automation health. |
| `tradeforge doctor` | Compare the active environment with the lock and provenance. |
| `tradeforge start-api` | Start the local read only FastAPI service. |
| `tradeforge show-quotes` | Print stored live quotes. |
| `tradeforge show-valuation` | Value one strategy run from stored quotes. |
| `tradeforge show-positions` | Print simulated positions. |
| `tradeforge show-orders` | Print simulated orders. |
| `tradeforge show-pnl` | Print strategy run profit and loss summaries. |

Get exact options for any command:

```powershell
tradeforge run-backtest --help
tradeforge run-maintenance --help
```

## Developer validation

The bootstrap installs all declared validation tools. Before handing off a change, run:

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy
python -m pytest -q --cov=tradeforge --cov-report=term-missing
.\scripts\Test-Markdown.ps1
.\scripts\Test-ProjectGovernance.ps1 -CheckWorkingTree
```

Tests treat warnings as errors and enforce at least 88 percent statement coverage. The governance check requires every repository change to update the four living root files:

* [CHANGELOG.md](./CHANGELOG.md)
* [ASSESSMENT.md](./ASSESSMENT.md)
* [FUTURE-UPGRADES.md](./FUTURE-UPGRADES.md)
* [COMPLETED-UPGRADES.md](./COMPLETED-UPGRADES.md)

See [CONTRIBUTING.md](./CONTRIBUTING.md) before changing source code, migrations, workflows, or project policy.

## Further documentation

Use these entry points after completing the first run:

* [Documentation hub](./docs/README.md)
* [Installation details](./docs/installation/README.md)
* [Configuration reference](./docs/configuration/README.md)
* [Automation operations](./docs/automation/README.md)
* [Backtesting rules](./docs/backtesting/README.md)
* [Market data behavior](./docs/market-data/README.md)
* [Database behavior](./docs/database/README.md)
* [Architecture](./docs/architecture/README.md)
* [Security policy](./SECURITY.md)
* [Support guide](./SUPPORT.md)
* [Roadmap](./FUTURE-UPGRADES.md)

TradeForge is licensed under the [MIT License](./LICENSE).
