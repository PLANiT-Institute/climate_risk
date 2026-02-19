"""In-memory partner session store with TTL."""

import time
import uuid
from typing import Optional

_store: dict[str, dict] = {}
_DEFAULT_TTL = 7200  # 2 hours


def create_session(
    company_name: str, facilities: list[dict], ttl: int = _DEFAULT_TTL
) -> dict:
    pid = str(uuid.uuid4())
    now = time.time()
    _store[pid] = {
        "partner_id": pid,
        "company_name": company_name,
        "facilities": facilities,
        "created_at": now,
        "expires_at": now + ttl,
    }
    return _store[pid]


def get_session(partner_id: str) -> Optional[dict]:
    s = _store.get(partner_id)
    if not s:
        return None
    if time.time() > s["expires_at"]:
        del _store[partner_id]
        return None
    return s


def get_facilities(partner_id: str) -> Optional[list[dict]]:
    s = get_session(partner_id)
    return s["facilities"] if s else None


def delete_session(partner_id: str) -> bool:
    return _store.pop(partner_id, None) is not None
