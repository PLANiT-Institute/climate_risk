"""Sample Korean company facility data for Phase 1.

Data provided by the client.

"""

FACILITIES = [
    # ── Real Estate (고객사 테스트용 — 수치는 가정값, 공시 데이터 아님) ──
    {
        "facility_id": "KR-RE-001",
        "name": "Concordian",
        "company": "Client RE Fund",
        "sector": "real_estate",
        "location": "서울 종로구",
        "latitude": 37.570280,
        "longitude": 126.976914,
        "current_emissions_scope1": 10_000,
        "current_emissions_scope2": 50_000,
        "current_emissions_scope3": 100_000,
        "annual_revenue": 1_000_000_000,
        "ebitda": 200_000_000,
        "assets_value": 100_000_000_000,
    },
    {
        "facility_id": "KR-RE-002",
        "name": "Logisco Siheung",
        "company": "Client RE Fund",
        "sector": "real_estate",
        "location": "경기 시흥시",
        "latitude": 37.343924,
        "longitude": 126.730880,
        "current_emissions_scope1": 10_000,
        "current_emissions_scope2": 50_000,
        "current_emissions_scope3": 100_000,
        "annual_revenue": 1_000_000_000,
        "ebitda": 200_000_000,
        "assets_value": 100_000_000_000,
    },
]


def get_all_facilities() -> list:
    return FACILITIES


def get_facility_by_id(facility_id: str) -> dict | None:
    for f in FACILITIES:
        if f["facility_id"] == facility_id:
            return f
    return None


def get_facilities_by_sector(sector: str) -> list:
    return [f for f in FACILITIES if f["sector"] == sector]


def get_company_list() -> list[str]:
    """Return sorted list of unique company names."""
    return sorted(set(f["company"] for f in FACILITIES))


def get_facilities_by_company(company: str) -> list[dict]:
    """Return facilities belonging to a specific company."""
    return [f for f in FACILITIES if f["company"] == company]


def get_company_summary(company: str) -> dict:
    """Aggregate company-level metrics: total emissions, revenue, assets, facility count, sectors."""
    facs = get_facilities_by_company(company)
    if not facs:
        return {}
    sectors = sorted(set(f["sector"] for f in facs))
    return {
        "company": company,
        "facility_count": len(facs),
        "sectors": sectors,
        "primary_sector": sectors[0],
        "total_scope1": sum(f["current_emissions_scope1"] for f in facs),
        "total_scope2": sum(f["current_emissions_scope2"] for f in facs),
        "total_scope3": sum(f["current_emissions_scope3"] for f in facs),
        "total_revenue": sum(f["annual_revenue"] for f in facs),
        "total_ebitda": sum(f["ebitda"] for f in facs),
        "total_assets": sum(f["assets_value"] for f in facs),
    }
