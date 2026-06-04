"""Export climate risk Excel report for Client RE Fund.

Generates a 4-sheet XLSX report from the physical and transition risk
services. Run from the repository root:

    python sandbox/export_excel.py

Output: outputs/client_re_fund_climate_risk.xlsx
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — must run from repo root; backend lives at ./backend
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "backend"))

from openpyxl import Workbook  # noqa: E402
from openpyxl.styles import Alignment, Font, PatternFill  # noqa: E402
from openpyxl.utils import get_column_letter  # noqa: E402

from app.services.physical_risk import assess_physical_risk  # noqa: E402
from app.services.transition_risk import analyse_scenario  # noqa: E402

# ---------------------------------------------------------------------------
# Style constants
# ---------------------------------------------------------------------------
_FILL_HEADER = PatternFill("solid", fgColor="BDD7EE")   # light blue
_FILL_SECTION = PatternFill("solid", fgColor="D9D9D9")  # light gray
_FONT_BOLD = Font(bold=True)
_ALIGN_CENTER = Alignment(horizontal="center")
_FMT_COMMA = "#,##0"

_HAZARD_KO: dict[str, str] = {
    "flood": "홍수",
    "typhoon": "태풍",
    "heatwave": "폭염",
    "drought": "가뭄",
    "sea_level_rise": "해수면 상승",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _style_header(cell: object) -> None:
    """Apply bold + light-blue fill to a header cell."""
    cell.font = _FONT_BOLD  # type: ignore[union-attr]
    cell.fill = _FILL_HEADER


def _style_section(cell: object) -> None:
    """Apply bold + light-gray fill to a section-title cell."""
    cell.font = _FONT_BOLD  # type: ignore[union-attr]
    cell.fill = _FILL_SECTION


def _autofit(ws: object, min_width: int = 15) -> None:
    """Set column widths to the maximum content length, at least min_width."""
    col_widths: dict[str, int] = {}
    for row in ws.iter_rows():  # type: ignore[union-attr]
        for cell in row:
            if cell.value is not None:
                col_letter = get_column_letter(cell.column)
                length = len(str(cell.value))
                col_widths[col_letter] = max(col_widths.get(col_letter, 0), length)
    for col_letter, width in col_widths.items():
        ws.column_dimensions[col_letter].width = max(width + 2, min_width)  # type: ignore[union-attr]


def _set_comma(ws: object, row: int, cols: list[int]) -> None:
    """Apply comma number format to specified columns in a row."""
    for col in cols:
        ws.cell(row=row, column=col).number_format = _FMT_COMMA  # type: ignore[union-attr]


# ---------------------------------------------------------------------------
# Sheet 1 — 요약 (Summary)
# ---------------------------------------------------------------------------
def _write_summary(
    wb: Workbook,
    pr: dict,
    tr: dict,
) -> None:
    ws = wb.create_sheet("요약")

    # Title
    ws["A1"] = "기후리스크 분석 보고서 — Client RE Fund"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"생성일: {date.today().isoformat()}"

    # Build lookup maps from API results
    pr_map: dict[str, dict] = {f["facility_name"]: f for f in pr["facilities"]}
    tr_map: dict[str, dict] = {f["facility_name"]: f for f in tr["facilities"]}

    # Header row
    header_row = 4
    headers = [
        "자산명", "위치", "물리적 리스크 등급", "총 EAL (USD)",
        "전환 리스크 등급", "NPV 영향 (USD)",
    ]
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col, value=h)
        _style_header(cell)

    # Data rows — one per facility in pr order
    for i, fac_pr in enumerate(pr["facilities"]):
        name = fac_pr["facility_name"]
        fac_tr = tr_map.get(name, {})
        data_row = header_row + 1 + i

        ws.cell(row=data_row, column=1, value=name)
        ws.cell(row=data_row, column=2, value=fac_pr["location"])
        ws.cell(row=data_row, column=3, value=fac_pr["overall_risk_level"])
        ws.cell(row=data_row, column=4, value=fac_pr["total_expected_annual_loss"])
        ws.cell(row=data_row, column=5, value=fac_tr.get("risk_level", "N/A"))
        ws.cell(row=data_row, column=6, value=fac_tr.get("delta_npv", 0))
        _set_comma(ws, data_row, [4, 6])

    # Disclaimer note at the bottom
    note_row = header_row + 1 + len(pr["facilities"]) + 2
    ws.cell(
        row=note_row,
        column=1,
        value="* 배출량 및 재무 수치는 테스트용 가정값입니다.",
    )
    ws.cell(row=note_row, column=1).font = Font(italic=True, color="808080")

    _autofit(ws)


# ---------------------------------------------------------------------------
# Sheet 2 — 물리적 리스크 (Physical Risk)
# ---------------------------------------------------------------------------
def _write_physical_risk(wb: Workbook, pr: dict) -> None:
    ws = wb.create_sheet("물리적 리스크")
    current_row = 1

    hazard_headers = [
        "재해 유형", "위험 등급", "발생확률",
        "예상손실 (USD)", "재현기간 (년)", "기후변화 배율",
    ]

    for fac in pr["facilities"]:
        # Section title: facility name
        cell = ws.cell(row=current_row, column=1, value=fac["facility_name"])
        _style_section(cell)
        current_row += 1

        # Overall summary
        ws.cell(row=current_row, column=1, value="종합 위험 등급")
        ws.cell(row=current_row, column=2, value=fac["overall_risk_level"])
        current_row += 1

        ws.cell(row=current_row, column=1, value="총 연간 기대손실 (EAL, USD)")
        eal_cell = ws.cell(row=current_row, column=2, value=fac["total_expected_annual_loss"])
        eal_cell.number_format = _FMT_COMMA
        current_row += 2

        # Hazard detail table header
        for col, h in enumerate(hazard_headers, start=1):
            cell = ws.cell(row=current_row, column=col, value=h)
            _style_header(cell)
        current_row += 1

        # Hazard rows
        for hazard in fac["hazards"]:
            ws.cell(
                row=current_row, column=1,
                value=_HAZARD_KO.get(hazard["hazard_type"], hazard["hazard_type"]),
            )
            ws.cell(row=current_row, column=2, value=hazard["risk_level"])
            ws.cell(row=current_row, column=3, value=hazard["probability"])
            loss_cell = ws.cell(row=current_row, column=4, value=hazard["potential_loss"])
            loss_cell.number_format = _FMT_COMMA
            ws.cell(row=current_row, column=5, value=hazard["return_period_years"])
            ws.cell(row=current_row, column=6, value=hazard["climate_change_multiplier"])
            current_row += 1

        current_row += 2  # blank spacer between facilities

    _autofit(ws)


# ---------------------------------------------------------------------------
# Sheet 3 — 전환 리스크 (Transition Risk)
# ---------------------------------------------------------------------------
def _write_transition_risk(wb: Workbook, tr: dict) -> None:
    ws = wb.create_sheet("전환 리스크")
    current_row = 1

    annual_headers = [
        "연도", "탄소비용", "에너지비용 증가",
        "EBITDA 영향", "총 배출량 (tCO2e)",
    ]

    for fac in tr["facilities"]:
        # Section title
        cell = ws.cell(row=current_row, column=1, value=fac["facility_name"])
        _style_section(cell)
        current_row += 1

        # Facility-level summary
        ws.cell(row=current_row, column=1, value="위험 등급")
        ws.cell(row=current_row, column=2, value=fac["risk_level"])
        current_row += 1

        ws.cell(row=current_row, column=1, value="NPV 영향 (USD)")
        npv_cell = ws.cell(row=current_row, column=2, value=fac["delta_npv"])
        npv_cell.number_format = _FMT_COMMA
        current_row += 1

        ws.cell(row=current_row, column=1, value="NPV / 자산 (%)")
        ws.cell(row=current_row, column=2, value=fac["npv_as_pct_of_assets"])
        current_row += 2

        # Annual impacts table header
        for col, h in enumerate(annual_headers, start=1):
            cell = ws.cell(row=current_row, column=col, value=h)
            _style_header(cell)
        current_row += 1

        for ai in fac["annual_impacts"]:
            ws.cell(row=current_row, column=1, value=ai["year"])
            for col_idx, key in enumerate(
                ["carbon_cost", "energy_cost_increase", "delta_ebitda", "total_emissions"],
                start=2,
            ):
                val_cell = ws.cell(row=current_row, column=col_idx, value=ai[key])
                val_cell.number_format = _FMT_COMMA
            current_row += 1

        current_row += 2

    _autofit(ws)


# ---------------------------------------------------------------------------
# Sheet 4 — 배출경로 (Emission Pathway)
# ---------------------------------------------------------------------------
def _write_emission_pathway(wb: Workbook, tr: dict) -> None:
    ws = wb.create_sheet("배출경로")
    current_row = 1

    pathway_headers = ["연도", "Scope 1", "Scope 2", "합계", "감축률"]

    for fac in tr["facilities"]:
        cell = ws.cell(row=current_row, column=1, value=fac["facility_name"])
        _style_section(cell)
        current_row += 1

        for col, h in enumerate(pathway_headers, start=1):
            cell = ws.cell(row=current_row, column=col, value=h)
            _style_header(cell)
        current_row += 1

        for pt in fac["emission_pathway"]:
            ws.cell(row=current_row, column=1, value=pt["year"])
            for col_idx, key in enumerate(
                ["scope1_emissions", "scope2_emissions", "total_emissions"],
                start=2,
            ):
                val_cell = ws.cell(row=current_row, column=col_idx, value=pt[key])
                val_cell.number_format = _FMT_COMMA
            # Reduction rate as percentage string
            reduction_pct = round(pt["reduction_factor"] * 100, 1)
            ws.cell(row=current_row, column=5, value=f"{reduction_pct}%")
            current_row += 1

        current_row += 2

    _autofit(ws)


# ---------------------------------------------------------------------------
# Sheet 5 — 입력값 (Input Parameters)
# ---------------------------------------------------------------------------
def _write_inputs(wb: Workbook, pr: dict) -> None:
    ws = wb.create_sheet("입력값")

    # Title
    cell = ws.cell(row=1, column=1, value="분석 입력값")
    cell.font = Font(bold=True, size=12)

    ws.cell(row=2, column=1, value=f"시나리오: {pr['scenario']}")
    ws.cell(row=3, column=1, value=f"평가 연도: {pr['assessment_year']}")
    ws.cell(row=4, column=1, value=f"산업화 대비 온난화: +{pr['warming_above_preindustrial']}°C")

    # Facility input table header
    headers = [
        "facility_id", "자산명", "회사", "업종", "위치",
        "위도", "경도",
        "Scope 1 (tCO2e)", "Scope 2 (tCO2e)", "Scope 3 (tCO2e)",
        "연간 매출 (USD)", "EBITDA (USD)", "자산 가치 (USD)",
    ]
    header_row = 6
    for col, h in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col, value=h)
        _style_header(cell)

    # One row per facility (from backend data)
    from app.data.sample_facilities import get_all_facilities
    for i, fac in enumerate(get_all_facilities()):
        r = header_row + 1 + i
        ws.cell(row=r, column=1, value=fac["facility_id"])
        ws.cell(row=r, column=2, value=fac["name"])
        ws.cell(row=r, column=3, value=fac["company"])
        ws.cell(row=r, column=4, value=fac["sector"])
        ws.cell(row=r, column=5, value=fac["location"])
        ws.cell(row=r, column=6, value=fac["latitude"])
        ws.cell(row=r, column=7, value=fac["longitude"])
        ws.cell(row=r, column=8, value=fac["current_emissions_scope1"])
        ws.cell(row=r, column=9, value=fac["current_emissions_scope2"])
        ws.cell(row=r, column=10, value=fac["current_emissions_scope3"])
        rev_cell = ws.cell(row=r, column=11, value=fac["annual_revenue"])
        rev_cell.number_format = _FMT_COMMA
        ebitda_cell = ws.cell(row=r, column=12, value=fac["ebitda"])
        ebitda_cell.number_format = _FMT_COMMA
        assets_cell = ws.cell(row=r, column=13, value=fac["assets_value"])
        assets_cell.number_format = _FMT_COMMA

    # Disclaimer
    note_row = header_row + 1 + len(get_all_facilities()) + 2
    ws.cell(row=note_row, column=1, value="* 배출량 및 재무 수치는 테스트용 가정값입니다. 실제 공시 데이터가 아닙니다.")
    ws.cell(row=note_row, column=1).font = Font(italic=True, color="808080")

    _autofit(ws)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    """Fetch risk data and write the Excel report."""
    print("물리적 리스크 데이터 로딩 중...")
    pr = assess_physical_risk(scenario_id="current_policies", year=2030)

    print("전환 리스크 데이터 로딩 중...")
    tr = analyse_scenario("current_policies", pricing_regime="global")

    wb = Workbook()
    # Remove default empty sheet created by openpyxl
    default_sheet = wb.active
    if default_sheet is not None:
        wb.remove(default_sheet)

    print("Excel 시트 작성 중...")
    _write_summary(wb, pr, tr)
    _write_physical_risk(wb, pr)
    _write_transition_risk(wb, tr)
    _write_emission_pathway(wb, tr)
    _write_inputs(wb, pr)

    output_dir = _REPO_ROOT / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "client_re_fund_climate_risk.xlsx"
    wb.save(output_path)

    print(f"저장 완료: {output_path}")


if __name__ == "__main__":
    main()
