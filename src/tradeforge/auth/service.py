from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from tradeforge.database.models import APIKey, Tenant

ROLES = {"viewer": 1, "operator": 2, "admin": 3}


class AuthenticationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AuthContext:
    api_key_id: str
    tenant_id: str
    role: str

    def allows(self, required_role: str) -> bool:
        if required_role not in ROLES:
            raise ValueError(f"Unknown required role: {required_role}")
        return ROLES[self.role] >= ROLES[required_role]


def create_tenant(session: Session, name: str) -> Tenant:
    normalized = name.strip()
    if not normalized:
        raise ValueError("Tenant name must not be empty.")
    if session.scalar(select(Tenant.id).where(Tenant.name == normalized)) is not None:
        raise ValueError(f"Tenant already exists: {normalized}")
    tenant = Tenant(name=normalized)
    session.add(tenant)
    session.flush()
    return tenant


def create_api_key(
    session: Session,
    tenant_id: str,
    name: str,
    role: str,
    expires_at: datetime | None = None,
) -> tuple[APIKey, str]:
    tenant = session.get(Tenant, tenant_id)
    if tenant is None or not tenant.is_active:
        raise ValueError("API keys require an active tenant.")
    normalized_name = name.strip()
    normalized_role = role.strip().lower()
    if not normalized_name:
        raise ValueError("API key name must not be empty.")
    if normalized_role not in ROLES:
        raise ValueError(f"API key role must be one of: {', '.join(ROLES)}.")
    normalized_expiration = _utc(expires_at) if expires_at is not None else None
    if normalized_expiration is not None and normalized_expiration <= datetime.now(timezone.utc):
        raise ValueError("API key expiration must be in the future.")
    raw_key = f"tf_{secrets.token_urlsafe(32)}"
    api_key = APIKey(
        tenant_id=tenant.id,
        name=normalized_name,
        key_hash=_hash_key(raw_key),
        role=normalized_role,
        expires_at=normalized_expiration,
    )
    session.add(api_key)
    session.flush()
    return api_key, raw_key


def authenticate_api_key(session: Session, raw_key: str, now: datetime | None = None) -> AuthContext:
    if not raw_key.startswith("tf_"):
        raise AuthenticationError("Invalid API key.")
    api_key = session.scalar(select(APIKey).where(APIKey.key_hash == _hash_key(raw_key)))
    current_time = _utc(now or datetime.now(timezone.utc))
    if api_key is None or api_key.revoked_at is not None:
        raise AuthenticationError("Invalid API key.")
    if api_key.expires_at is not None and _utc(api_key.expires_at) <= current_time:
        raise AuthenticationError("API key has expired.")
    if not api_key.tenant.is_active:
        raise AuthenticationError("API key tenant is inactive.")
    api_key.last_used_at = current_time
    session.flush()
    return AuthContext(api_key.id, api_key.tenant_id, api_key.role)


def rotate_api_key(session: Session, api_key_id: str, expires_at: datetime | None = None) -> tuple[APIKey, str]:
    current = session.get(APIKey, api_key_id)
    if current is None or current.revoked_at is not None:
        raise ValueError("Active API key not found.")
    current.revoked_at = datetime.now(timezone.utc)
    return create_api_key(session, current.tenant_id, current.name, current.role, expires_at)


def revoke_api_key(session: Session, api_key_id: str) -> APIKey:
    api_key = session.get(APIKey, api_key_id)
    if api_key is None:
        raise ValueError("API key not found.")
    if api_key.revoked_at is None:
        api_key.revoked_at = datetime.now(timezone.utc)
    session.flush()
    return api_key


def _hash_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
