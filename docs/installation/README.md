# Installation

## Purpose

This section explains how to install and run TradeForge in development, local lab, and future packaged environments.

## Intended Contents

* host prerequisites
* Python setup
* Docker setup
* first run flow
* upgrade flow
* troubleshooting

## Current Setup

```powershell
py -3.13 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --constraint requirements.lock -e ".[dev]"
tradeforge init-db
```

For the hardened container profile:

```powershell
Copy-Item .env.example .env
docker compose up --build --detach
docker compose ps
```

Compose binds the API to `127.0.0.1:8000`, restarts it unless stopped, and uses `/health` for container health. The process runs as UID 10001. Docker initializes the managed `tradeforge-data` volume from the image with ownership that lets this unprivileged user create and update the database.

## Suggested Future Topics

* windows-setup.md
* linux-setup.md
* docker-setup.md
* upgrade-playbook.md
* offline-installation.md

## Naming Conventions

* setup guides end with `setup`
* operational procedures end with `playbook`
* platform specific files start with the platform name

## File Examples

* `windows-setup.md`
* `docker-setup.md`
* `upgrade-playbook.md`

## Cross Links

* [configuration](../configuration/README.md)
* [automation](../automation/README.md)
