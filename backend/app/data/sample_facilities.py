"""Sample Korean company facility data for Phase 1.

Data represents stylized Korean industrial facilities modeled on major
companies. Financial figures (revenue, EBITDA, assets) are illustrative
approximations, not actual reported values.

Sources for sector-typical financial ratios:
- Steel: POSCO 2023 Annual Report (EBITDA margin ~15%)
- Petrochemical: SK Innovation 2023 (margin ~12%)
- Automotive: Hyundai Motor 2023 (margin ~12%)
- Electronics: Samsung Electronics 2023 (margin ~30% for semicon)
- Utilities: KEPCO/Gencos 2023 (margin ~10% for regulated coal)
- Cement: Korea Cement Association industry data (margin ~20%)
- Shipping: HMM 2023 (margin ~12%, varies with freight rates)
- Oil & Gas: SK Energy 2023 (margin ~7%)

Scope 3 notes:
- Electronics Scope 3 (~25% of total) may underestimate typical
  semiconductor supply chain (industry average 30-40%).
- Automotive Scope 3 (~40% of total) excludes use-phase vehicle
  emissions which can be 5-10x manufacturing emissions.
"""

FACILITIES = [
    # ── Steel (포스코형) ──
    {
        "facility_id": "KR-STL-001",
        "name": "포항제철소",
        "company": "K-Steel Corp",
        "sector": "steel",
        "location": "경북 포항시",
        "latitude": 36.0190,
        "longitude": 129.3435,
        "current_emissions_scope1": 28_000_000,
        "current_emissions_scope2": 5_200_000,
        "current_emissions_scope3": 8_400_000,
        "annual_revenue": 32_000_000_000,
        "ebitda": 4_800_000_000,
        "assets_value": 25_000_000_000,
    },
    {
        "facility_id": "KR-STL-002",
        "name": "광양제철소",
        "company": "K-Steel Corp",
        "sector": "steel",
        "location": "전남 광양시",
        "latitude": 34.9407,
        "longitude": 127.6959,
        "current_emissions_scope1": 24_000_000,
        "current_emissions_scope2": 4_600_000,
        "current_emissions_scope3": 7_200_000,
        "annual_revenue": 28_000_000_000,
        "ebitda": 4_200_000_000,
        "assets_value": 22_000_000_000,
    },
    # ── Petrochemical (SK이노베이션형) ──
    {
        "facility_id": "KR-PCH-001",
        "name": "울산석유화학단지",
        "company": "K-Petrochem Inc",
        "sector": "petrochemical",
        "location": "울산 남구",
        "latitude": 35.5384,
        "longitude": 129.3114,
        "current_emissions_scope1": 12_000_000,
        "current_emissions_scope2": 3_800_000,
        "current_emissions_scope3": 18_000_000,
        "annual_revenue": 45_000_000_000,
        "ebitda": 5_400_000_000,
        "assets_value": 20_000_000_000,
    },
    {
        "facility_id": "KR-PCH-002",
        "name": "여수석유화학단지",
        "company": "K-Petrochem Inc",
        "sector": "petrochemical",
        "location": "전남 여수시",
        "latitude": 34.7604,
        "longitude": 127.6622,
        "current_emissions_scope1": 9_500_000,
        "current_emissions_scope2": 2_900_000,
        "current_emissions_scope3": 14_000_000,
        "annual_revenue": 38_000_000_000,
        "ebitda": 4_560_000_000,
        "assets_value": 17_000_000_000,
    },
    # ── Automotive (현대차형) ──
    {
        "facility_id": "KR-AUT-001",
        "name": "울산자동차공장",
        "company": "K-Motors Co",
        "sector": "automotive",
        "location": "울산 북구",
        "latitude": 35.5825,
        "longitude": 129.3612,
        "current_emissions_scope1": 1_800_000,
        "current_emissions_scope2": 2_200_000,
        "current_emissions_scope3": 15_000_000,
        "annual_revenue": 55_000_000_000,
        "ebitda": 6_600_000_000,
        "assets_value": 18_000_000_000,
    },
    {
        "facility_id": "KR-AUT-002",
        "name": "아산자동차공장",
        "company": "K-Motors Co",
        "sector": "automotive",
        "location": "충남 아산시",
        "latitude": 36.7898,
        "longitude": 127.0018,
        "current_emissions_scope1": 950_000,
        "current_emissions_scope2": 1_100_000,
        "current_emissions_scope3": 8_500_000,
        "annual_revenue": 28_000_000_000,
        "ebitda": 3_360_000_000,
        "assets_value": 10_000_000_000,
    },
    # ── Electronics (삼성형) ──
    {
        "facility_id": "KR-ELC-001",
        "name": "화성반도체공장",
        "company": "K-Electronics Ltd",
        "sector": "electronics",
        "location": "경기 화성시",
        "latitude": 37.2064,
        "longitude": 127.0714,
        "current_emissions_scope1": 3_200_000,
        "current_emissions_scope2": 8_500_000,
        "current_emissions_scope3": 5_600_000,
        "annual_revenue": 120_000_000_000,
        "ebitda": 36_000_000_000,
        "assets_value": 80_000_000_000,
    },
    {
        "facility_id": "KR-ELC-002",
        "name": "평택반도체공장",
        "company": "K-Electronics Ltd",
        "sector": "electronics",
        "location": "경기 평택시",
        "latitude": 36.9922,
        "longitude": 127.0892,
        "current_emissions_scope1": 2_800_000,
        "current_emissions_scope2": 7_200_000,
        "current_emissions_scope3": 4_800_000,
        "annual_revenue": 95_000_000_000,
        "ebitda": 28_500_000_000,
        "assets_value": 65_000_000_000,
    },
    {
        "facility_id": "KR-ELC-003",
        "name": "구미디스플레이공장",
        "company": "K-Display Corp",
        "sector": "electronics",
        "location": "경북 구미시",
        "latitude": 36.1198,
        "longitude": 128.3444,
        "current_emissions_scope1": 1_500_000,
        "current_emissions_scope2": 4_200_000,
        "current_emissions_scope3": 3_100_000,
        "annual_revenue": 42_000_000_000,
        "ebitda": 5_040_000_000,
        "assets_value": 28_000_000_000,
    },
    # ── Utilities / Power (한전형) ──
    {
        "facility_id": "KR-UTL-001",
        "name": "당진화력발전소",
        "company": "K-Power Corp",
        "sector": "utilities",
        "location": "충남 당진시",
        "latitude": 36.8898,
        "longitude": 126.6294,
        "current_emissions_scope1": 18_000_000,
        "current_emissions_scope2": 500_000,
        "current_emissions_scope3": 2_200_000,
        "annual_revenue": 8_000_000_000,
        "ebitda": 800_000_000,       # ~10% margin (KEPCO regulated rate structure)
        "assets_value": 12_000_000_000,
    },
    {
        "facility_id": "KR-UTL-002",
        "name": "태안화력발전소",
        "company": "K-Power Corp",
        "sector": "utilities",
        "location": "충남 태안군",
        "latitude": 36.7450,
        "longitude": 126.2969,
        "current_emissions_scope1": 15_000_000,
        "current_emissions_scope2": 400_000,
        "current_emissions_scope3": 1_800_000,
        "annual_revenue": 6_500_000_000,
        "ebitda": 650_000_000,       # ~10% margin (KEPCO regulated rate structure)
        "assets_value": 9_500_000_000,
    },
    {
        "facility_id": "KR-UTL-003",
        "name": "영흥화력발전소",
        "company": "K-Power Corp",
        "sector": "utilities",
        "location": "인천 옹진군",
        "latitude": 37.2500,
        "longitude": 126.4833,
        "current_emissions_scope1": 12_000_000,
        "current_emissions_scope2": 350_000,
        "current_emissions_scope3": 1_500_000,
        "annual_revenue": 5_200_000_000,
        "ebitda": 520_000_000,       # ~10% margin (KEPCO regulated rate structure)
        "assets_value": 8_000_000_000,
    },
    # ── Cement ──
    {
        "facility_id": "KR-CMT-001",
        "name": "단양시멘트공장",
        "company": "K-Cement Corp",
        "sector": "cement",
        "location": "충북 단양군",
        "latitude": 36.9847,
        "longitude": 128.3654,
        "current_emissions_scope1": 6_500_000,
        "current_emissions_scope2": 1_200_000,
        "current_emissions_scope3": 2_800_000,
        "annual_revenue": 3_800_000_000,
        "ebitda": 760_000_000,
        "assets_value": 5_000_000_000,
    },
    {
        "facility_id": "KR-CMT-002",
        "name": "영월시멘트공장",
        "company": "K-Cement Corp",
        "sector": "cement",
        "location": "강원 영월군",
        "latitude": 37.1839,
        "longitude": 128.4617,
        "current_emissions_scope1": 5_200_000,
        "current_emissions_scope2": 980_000,
        "current_emissions_scope3": 2_200_000,
        "annual_revenue": 3_000_000_000,
        "ebitda": 600_000_000,
        "assets_value": 4_000_000_000,
    },
    # ── Shipping ──
    {
        "facility_id": "KR-SHP-001",
        "name": "부산항 해운기지",
        "company": "K-Shipping Lines",
        "sector": "shipping",
        "location": "부산 영도구",
        "latitude": 35.0756,
        "longitude": 129.0681,
        "current_emissions_scope1": 4_200_000,
        "current_emissions_scope2": 350_000,
        "current_emissions_scope3": 6_800_000,
        "annual_revenue": 12_000_000_000,
        "ebitda": 1_440_000_000,
        "assets_value": 8_500_000_000,
    },
    # ── Oil & Gas (정유) ──
    {
        "facility_id": "KR-OG-001",
        "name": "울산정유공장",
        "company": "K-Refinery Corp",
        "sector": "oil_gas",
        "location": "울산 울주군",
        "latitude": 35.4929,
        "longitude": 129.2278,
        "current_emissions_scope1": 8_500_000,
        "current_emissions_scope2": 2_100_000,
        "current_emissions_scope3": 22_000_000,
        "annual_revenue": 52_000_000_000,
        "ebitda": 3_640_000_000,
        "assets_value": 15_000_000_000,
    },
    {
        "facility_id": "KR-OG-002",
        "name": "대산정유공장",
        "company": "K-Refinery Corp",
        "sector": "oil_gas",
        "location": "충남 서산시",
        "latitude": 36.9167,
        "longitude": 126.3833,
        "current_emissions_scope1": 6_800_000,
        "current_emissions_scope2": 1_700_000,
        "current_emissions_scope3": 18_000_000,
        "annual_revenue": 40_000_000_000,
        "ebitda": 2_800_000_000,
        "assets_value": 12_000_000_000,
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
