FROM python:3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN addgroup --system --gid 10001 tradeforge \
    && adduser --system --uid 10001 --ingroup tradeforge --home /app --no-create-home tradeforge

COPY pyproject.toml README.md requirements.lock /app/
COPY --chown=tradeforge:tradeforge src /app/src
COPY --chown=tradeforge:tradeforge data /app/data

RUN python -m pip install --no-cache-dir --constraint requirements.lock . \
    && mkdir -p /app/data/imports /app/data/reports /app/data/backups /app/data/automation \
    && chown -R tradeforge:tradeforge /app/data

USER tradeforge

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).read()"]

CMD ["tradeforge", "start-api", "--host", "0.0.0.0", "--port", "8000"]
