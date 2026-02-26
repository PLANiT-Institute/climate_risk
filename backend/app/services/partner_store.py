"""SQLite-backed partner session store with TTL."""

import time
import uuid
import json
import sqlite3
from typing import Optional
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "partner_sessions.db"
_DEFAULT_TTL = 7200  # 2 hours

def _get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_conn() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                partner_id TEXT PRIMARY KEY,
                company_name TEXT,
                facilities_json TEXT,
                created_at REAL,
                expires_at REAL
            )
        ''')
        # Cleanup expired on startup
        conn.execute('DELETE FROM sessions WHERE expires_at < ?', (time.time(),))

_init_db()

def create_session(
    company_name: str, facilities: list[dict], ttl: int = _DEFAULT_TTL
) -> dict:
    pid = str(uuid.uuid4())
    now = time.time()
    expires_at = now + ttl
    
    with _get_conn() as conn:
        conn.execute(
            'INSERT INTO sessions (partner_id, company_name, facilities_json, created_at, expires_at) VALUES (?, ?, ?, ?, ?)',
            (pid, company_name, json.dumps(facilities), now, expires_at)
        )
        
    return {
        "partner_id": pid,
        "company_name": company_name,
        "facilities": facilities,
        "created_at": now,
        "expires_at": expires_at,
    }

def get_session(partner_id: str) -> Optional[dict]:
    with _get_conn() as conn:
        conn.execute('DELETE FROM sessions WHERE expires_at < ?', (time.time(),))
        row = conn.execute(
            'SELECT * FROM sessions WHERE partner_id = ?', 
            (partner_id,)
        ).fetchone()
        
    if not row:
        return None
        
    return {
        "partner_id": row["partner_id"],
        "company_name": row["company_name"],
        "facilities": json.loads(row["facilities_json"]),
        "created_at": row["created_at"],
        "expires_at": row["expires_at"],
    }

def get_facilities(partner_id: str) -> Optional[list[dict]]:
    s = get_session(partner_id)
    return s["facilities"] if s else None

def delete_session(partner_id: str) -> bool:
    with _get_conn() as conn:
        cursor = conn.execute('DELETE FROM sessions WHERE partner_id = ?', (partner_id,))
        return cursor.rowcount > 0
