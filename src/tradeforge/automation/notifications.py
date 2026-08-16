from __future__ import annotations

import hashlib
import json
import os
import smtplib
import ssl
from datetime import UTC, datetime
from email.message import EmailMessage
from pathlib import Path
from time import sleep
from typing import Any, Callable
from urllib.request import HTTPRedirectHandler, Request, build_opener

from tradeforge.config import Settings, validate_outbound_https_url


class _RejectNotificationRedirects(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        raise RuntimeError("Notification redirects are not allowed.")


def send_escalations(settings: Settings, report: dict[str, object]) -> dict[str, str]:
    channels: list[tuple[str, Callable[[], None]]] = []
    if settings.failure_teams_webhook_url:
        channels.append(("teams", lambda: _send_teams(settings.failure_teams_webhook_url or "", report)))
    if settings.smtp_host or settings.smtp_to:
        channels.append(("email", lambda: _send_email(settings, report)))
    if not channels:
        return {}

    state = _load_state(settings.notification_state_path)
    fingerprint = _fingerprint(report)
    now = datetime.now(UTC).timestamp()
    results: dict[str, str] = {}
    for channel, deliver in channels:
        previous = state.get(channel)
        if (
            isinstance(previous, dict)
            and previous.get("fingerprint") == fingerprint
            and isinstance(previous.get("sent_at"), (int, float))
            and now - float(previous["sent_at"]) < settings.notification_dedupe_seconds
        ):
            results[channel] = "suppressed_duplicate"
            continue
        _deliver_with_retry(deliver, settings.notification_retry_attempts)
        state[channel] = {"fingerprint": fingerprint, "sent_at": now}
        results[channel] = "sent"
    _write_state(settings.notification_state_path, state)
    return results


def _deliver_with_retry(deliver: Callable[[], None], attempts: int) -> None:
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            deliver()
            return
        except Exception as exc:
            last_error = exc
            if attempt + 1 < attempts:
                sleep(min(2**attempt, 30))
    if last_error is not None:
        raise last_error


def _send_teams(webhook_url: str, report: dict[str, object]) -> None:
    url = validate_outbound_https_url(webhook_url, "TRADEFORGE_FAILURE_TEAMS_WEBHOOK_URL")
    payload = json.dumps(
        {
            "text": (
                "TradeForge maintenance failed. "
                f"Started: {report.get('started_at', 'unknown')}. "
                f"Completed: {report.get('completed_at', 'unknown')}."
            )
        }
    ).encode("utf-8")
    request = Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with build_opener(_RejectNotificationRedirects()).open(request, timeout=10) as response:
        if response.status >= 400:
            raise RuntimeError(f"Teams notification returned HTTP {response.status}.")


def _send_email(settings: Settings, report: dict[str, object]) -> None:
    required = {
        "TRADEFORGE_SMTP_HOST": settings.smtp_host,
        "TRADEFORGE_SMTP_FROM": settings.smtp_from,
        "TRADEFORGE_SMTP_TO": settings.smtp_to,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(f"Email escalation requires {', '.join(missing)}.")
    recipients = [item.strip() for item in (settings.smtp_to or "").split(",") if item.strip()]
    if not recipients:
        raise ValueError("TRADEFORGE_SMTP_TO must contain at least one address.")
    message = EmailMessage()
    message["Subject"] = "TradeForge maintenance failed"
    message["From"] = settings.smtp_from
    message["To"] = ", ".join(recipients)
    message.set_content(
        "TradeForge maintenance failed.\n"
        f"Started: {report.get('started_at', 'unknown')}\n"
        f"Completed: {report.get('completed_at', 'unknown')}\n"
    )
    with smtplib.SMTP(settings.smtp_host or "", settings.smtp_port, timeout=10) as client:
        client.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            client.login(settings.smtp_username, settings.smtp_password or "")
        client.send_message(message, to_addrs=recipients)


def _fingerprint(report: dict[str, object]) -> str:
    stable = json.dumps(
        {
            "event": "tradeforge_maintenance_failed",
            "status": report.get("status"),
            "error": report.get("error"),
        },
        sort_keys=True,
    )
    return hashlib.sha256(stable.encode("utf-8")).hexdigest()


def _load_state(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_state(path: Path, state: dict[str, object]) -> None:
    target = path.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temporary, target)
