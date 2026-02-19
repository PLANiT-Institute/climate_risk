"""Tests for Partner API – session management and partner-scoped analyses."""

import time
import pytest
from fastapi.testclient import TestClient

from ..main import app
from ..services import partner_store

client = TestClient(app)


# ── Test Fixtures ─────────────────────────────────────────────────────

_VALID_FACILITY = {
    "facility_id": "P001",
    "name": "Partner Steel Plant",
    "company": "Partner Corp",
    "sector": "steel",
    "latitude": 35.5,
    "longitude": 129.0,
    "current_emissions_scope1": 500_000,
    "current_emissions_scope2": 200_000,
    "annual_revenue": 800_000_000,
    "ebitda": 80_000_000,
    "assets_value": 1_200_000_000,
    "current_emissions_scope3": 100_000,
    "location": "Ulsan",
}

_VALID_FACILITY_2 = {
    "facility_id": "P002",
    "name": "Partner Cement Plant",
    "company": "Partner Corp",
    "sector": "cement",
    "latitude": 36.0,
    "longitude": 127.5,
    "current_emissions_scope1": 300_000,
    "current_emissions_scope2": 100_000,
    "annual_revenue": 400_000_000,
    "ebitda": 40_000_000,
    "assets_value": 600_000_000,
}


def _create_session(facilities=None):
    """Helper: create a session and return the response JSON."""
    if facilities is None:
        facilities = [_VALID_FACILITY, _VALID_FACILITY_2]
    body = {"company_name": "Partner Corp", "facilities": facilities}
    resp = client.post("/api/v1/partner/sessions", json=body)
    return resp


# ── Session Management Tests ──────────────────────────────────────────

def test_create_session():
    resp = _create_session()
    assert resp.status_code == 201
    data = resp.json()
    assert data["company_name"] == "Partner Corp"
    assert data["facility_count"] == 2
    assert "steel" in data["sectors"]
    assert "cement" in data["sectors"]
    assert data["expires_in_seconds"] > 7000
    assert len(data["partner_id"]) > 0
    assert data["sector_warnings"] == []


def test_create_session_unknown_sector_warning():
    fac = {**_VALID_FACILITY, "facility_id": "P099", "sector": "aerospace"}
    resp = _create_session(facilities=[fac])
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["sector_warnings"]) == 1
    assert "aerospace" in data["sector_warnings"][0]


def test_create_session_missing_field():
    bad = {"company_name": "X", "facilities": [{"facility_id": "P001"}]}
    resp = client.post("/api/v1/partner/sessions", json=bad)
    assert resp.status_code == 422


def test_create_session_empty_facilities():
    body = {"company_name": "X", "facilities": []}
    resp = client.post("/api/v1/partner/sessions", json=body)
    assert resp.status_code == 422


def test_create_session_duplicate_facility_ids():
    fac1 = {**_VALID_FACILITY, "facility_id": "DUP"}
    fac2 = {**_VALID_FACILITY_2, "facility_id": "DUP"}
    resp = _create_session(facilities=[fac1, fac2])
    assert resp.status_code == 422
    assert "Duplicate" in resp.json()["detail"]


def test_get_session():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}")
    assert resp.status_code == 200
    assert resp.json()["partner_id"] == pid
    assert resp.json()["facility_count"] == 2


def test_get_session_not_found():
    resp = client.get("/api/v1/partner/sessions/nonexistent-uuid")
    assert resp.status_code == 404


def test_delete_session():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.delete(f"/api/v1/partner/sessions/{pid}")
    assert resp.status_code == 204
    # Verify deleted
    resp2 = client.get(f"/api/v1/partner/sessions/{pid}")
    assert resp2.status_code == 404


def test_delete_session_not_found():
    resp = client.delete("/api/v1/partner/sessions/nonexistent-uuid")
    assert resp.status_code == 404


def test_list_facilities():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/facilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert len(data["facilities"]) == 2
    ids = {f["facility_id"] for f in data["facilities"]}
    assert ids == {"P001", "P002"}


# ── Partner Transition Risk Analysis ──────────────────────────────────

def test_partner_transition_analysis():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/transition-risk/analysis?scenario=net_zero_2050")
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario"] == "net_zero_2050"
    # Only partner facilities (2, not 17)
    assert len(data["facilities"]) == 2
    fac_ids = {f["facility_id"] for f in data["facilities"]}
    assert fac_ids == {"P001", "P002"}
    assert data["total_npv"] < 0


def test_partner_transition_summary():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/transition-risk/summary?scenario=net_zero_2050")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_facilities"] == 2


def test_partner_transition_comparison():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/transition-risk/comparison")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["scenarios"]) == 4


# ── Partner Physical Risk Analysis ────────────────────────────────────

def test_partner_physical_risk():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/physical-risk/assessment?scenario=net_zero_2050&year=2030")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_facilities"] == 2
    assert data["model_status"] == "analytical_v1"
    fac_ids = {f["facility_id"] for f in data["facilities"]}
    assert fac_ids == {"P001", "P002"}


# ── Partner ESG Assessment ────────────────────────────────────────────

def test_partner_esg_assessment():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/esg/assessment?framework=tcfd")
    assert resp.status_code == 200
    data = resp.json()
    assert data["framework"] == "tcfd"
    assert data["overall_score"] > 0


def test_partner_esg_disclosure_data():
    create_resp = _create_session()
    pid = create_resp.json()["partner_id"]
    resp = client.get(f"/api/v1/partner/sessions/{pid}/esg/disclosure-data?framework=tcfd")
    assert resp.status_code == 200
    data = resp.json()
    assert data["framework"] == "tcfd"
    assert "emissions" in data["metrics"]


# ── Expired Session ───────────────────────────────────────────────────

def test_expired_session_returns_404():
    # Create a session with 0 TTL (expires immediately)
    fac_dicts = [_VALID_FACILITY]
    session = partner_store.create_session("Expired Corp", fac_dicts, ttl=0)
    pid = session["partner_id"]
    time.sleep(0.01)  # Ensure expiry
    resp = client.get(f"/api/v1/partner/sessions/{pid}")
    assert resp.status_code == 404


# ── Existing Endpoints Unaffected ─────────────────────────────────────

def test_existing_transition_analysis_unchanged():
    """Ensure existing endpoints still use all 17 sample facilities."""
    resp = client.get("/api/v1/transition-risk/analysis?scenario=current_policies")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["facilities"]) == 17


def test_existing_physical_risk_unchanged():
    resp = client.get("/api/v1/physical-risk/assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_facilities"] == 17
