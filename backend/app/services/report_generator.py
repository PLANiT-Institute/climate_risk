"""Excel disclosure report generator.

Generates a multi-sheet Excel workbook structured around the four TCFD/ISSB/KSSB
core pillars: Governance, Strategy, Risk Management, Metrics & Targets.
Additional sheets provide gap analysis, regulatory timeline, and raw data.

Uses xlsxwriter for formatting (header colours, status colour-coding, number formats).
"""

import io
from datetime import date

import xlsxwriter

from ..data.sample_facilities import get_all_facilities
from ..services.esg_compliance import assess_framework, get_disclosure_data
from ..services.transition_risk import analyse_scenario, get_summary
from ..services.physical_risk import assess_physical_risk


# ── Colour palette ────────────────────────────────────────────────────
_COLOURS = {
    "header_bg": "#1E3A5F",
    "header_font": "#FFFFFF",
    "green": "#C6EFCE",
    "green_font": "#006100",
    "yellow": "#FFEB9C",
    "yellow_font": "#9C5700",
    "red": "#FFC7CE",
    "red_font": "#9C0006",
    "light_grey": "#F2F2F2",
    "blue_bg": "#D6E4F0",
    "blue_font": "#1E3A5F",
}


def _status_format(wb: xlsxwriter.Workbook, status: str):
    """Return a cell format for compliance status values."""
    if status in ("compliant", "준수", "충족"):
        return wb.add_format({"bg_color": _COLOURS["green"], "font_color": _COLOURS["green_font"]})
    if status in ("partial", "부분 준수", "부분"):
        return wb.add_format({"bg_color": _COLOURS["yellow"], "font_color": _COLOURS["yellow_font"]})
    return wb.add_format({"bg_color": _COLOURS["red"], "font_color": _COLOURS["red_font"]})


# ── Main entry point ──────────────────────────────────────────────────

def generate_disclosure_excel(
    framework: str = "kssb",
    scenario: str = "net_zero_2050",
    pricing_regime: str = "global",
    year: int = 2030,
    facilities: list | None = None,
) -> io.BytesIO:
    """Generate a disclosure Excel workbook and return it as an in-memory buffer."""
    facilities = facilities if facilities is not None else get_all_facilities()

    # ── Gather data from existing services ──
    esg = assess_framework(framework, facilities=facilities)
    disclosure = get_disclosure_data(framework, facilities=facilities)
    transition = analyse_scenario(scenario, pricing_regime=pricing_regime, facilities=facilities)
    summary = get_summary(scenario, pricing_regime=pricing_regime, facilities=facilities)
    physical = assess_physical_risk(scenario_id=scenario, year=year, facilities=facilities)

    # ── Create workbook ──
    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {"in_memory": True})

    # Shared formats
    hdr = wb.add_format({
        "bold": True,
        "bg_color": _COLOURS["header_bg"],
        "font_color": _COLOURS["header_font"],
        "border": 1,
        "text_wrap": True,
        "valign": "vcenter",
    })
    bold = wb.add_format({"bold": True})
    wrap = wb.add_format({"text_wrap": True, "valign": "top"})
    num_fmt = wb.add_format({"num_format": "#,##0"})
    pct_fmt = wb.add_format({"num_format": "0.0%"})
    money_fmt = wb.add_format({"num_format": "#,##0.00"})
    alt_row = wb.add_format({"bg_color": _COLOURS["light_grey"]})
    title_fmt = wb.add_format({
        "bold": True, "font_size": 14,
        "bg_color": _COLOURS["blue_bg"], "font_color": _COLOURS["blue_font"],
        "border": 1,
    })
    subtitle_fmt = wb.add_format({"bold": True, "font_size": 11})

    # ───────────────────────────────────────────────────────────────────
    # Sheet 1: Executive Summary
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("Executive Summary")
    ws.set_column("A:A", 30)
    ws.set_column("B:B", 40)

    ws.merge_range("A1:B1", f"기후 공시 보고서 — {esg['framework_name']}", title_fmt)
    ws.write("A3", "작성일", bold)
    ws.write("B3", date.today().isoformat())
    ws.write("A4", "프레임워크", bold)
    ws.write("B4", esg["framework_name"])
    ws.write("A5", "분석 시나리오", bold)
    ws.write("B5", scenario)
    ws.write("A6", "탄소가격 체제", bold)
    ws.write("B6", pricing_regime.upper())
    ws.write("A7", "분석 연도", bold)
    ws.write("B7", year)

    ws.write("A9", "종합 점수", bold)
    ws.write("B9", esg["overall_score"])
    ws.write("A10", "준수 수준", bold)
    ws.write("B10", esg["compliance_level"])
    if esg.get("maturity_level"):
        ws.write("A11", "성숙도 레벨", bold)
        ml = esg["maturity_level"]
        ws.write("B11", f"Level {ml['level']} — {ml['name']}: {ml['description']}")

    row = 13
    ws.write(row, 0, "카테고리별 점수", subtitle_fmt)
    row += 1
    ws.write_row(row, 0, ["카테고리", "점수", "최대 점수", "상태"], hdr)
    row += 1
    for cat in esg["categories"]:
        ws.write(row, 0, cat["category"])
        ws.write(row, 1, cat["score"])
        ws.write(row, 2, cat["max_score"])
        ws.write(row, 3, cat["status"], _status_format(wb, cat["status"]))
        row += 1

    # ───────────────────────────────────────────────────────────────────
    # Sheet 2: Governance
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("거버넌스")
    ws.set_column("A:A", 50)
    ws.set_column("B:B", 15)
    ws.set_column("C:C", 60)

    ws.merge_range("A1:C1", "거버넌스 — Governance", title_fmt)
    ws.write("A3", "서술", subtitle_fmt)
    ws.merge_range("A4:C4", disclosure["narrative_sections"].get("governance", ""), wrap)

    row = 6
    ws.write(row, 0, "공시 체크리스트", subtitle_fmt)
    row += 1
    ws.write_row(row, 0, ["항목", "상태", "권고사항"], hdr)
    row += 1
    for item in esg["checklist"]:
        ws.write(row, 0, item["item"], wrap)
        status_label = {"compliant": "준수", "partial": "부분 준수", "non_compliant": "미준수"}.get(
            item["status"], item["status"]
        )
        ws.write(row, 1, status_label, _status_format(wb, item["status"]))
        ws.write(row, 2, item.get("recommendation", ""), wrap)
        row += 1

    # ───────────────────────────────────────────────────────────────────
    # Sheet 3: Strategy
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("전략")
    ws.set_column("A:A", 25)
    ws.set_column("B:F", 20)

    ws.merge_range("A1:F1", "전략 — Strategy", title_fmt)
    ws.write("A3", "서술", subtitle_fmt)
    ws.merge_range("A4:F4", disclosure["narrative_sections"].get("strategy", ""), wrap)

    row = 6
    ws.write(row, 0, "시나리오 분석 요약", subtitle_fmt)
    row += 1
    ws.write(row, 0, "시나리오", bold)
    ws.write(row, 1, transition.get("scenario_name", scenario))
    row += 1
    ws.write(row, 0, "전환 리스크 NPV 합계", bold)
    ws.write(row, 1, transition.get("total_npv", 0), money_fmt)
    row += 1
    ws.write(row, 0, "평균 리스크 수준", bold)
    ws.write(row, 1, transition.get("avg_risk_level", ""))
    row += 2

    ws.write(row, 0, "시설별 전환 리스크", subtitle_fmt)
    row += 1
    headers = ["시설 ID", "시설명", "섹터", "리스크 수준", "NPV (USD)", "자산 대비 (%)"]
    ws.write_row(row, 0, headers, hdr)
    row += 1
    for fac in transition.get("facilities", []):
        bg = alt_row if (row % 2 == 0) else None
        ws.write(row, 0, fac["facility_id"], bg)
        ws.write(row, 1, fac["facility_name"], bg)
        ws.write(row, 2, fac["sector"], bg)
        ws.write(row, 3, fac["risk_level"], bg)
        ws.write(row, 4, fac["delta_npv"], money_fmt)
        ws.write(row, 5, fac["npv_as_pct_of_assets"] / 100 if fac["npv_as_pct_of_assets"] else 0, pct_fmt)
        row += 1

    # ───────────────────────────────────────────────────────────────────
    # Sheet 4: Risk Management
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("리스크 관리")
    ws.set_column("A:A", 25)
    ws.set_column("B:H", 18)

    ws.merge_range("A1:H1", "리스크 관리 — Risk Management", title_fmt)
    ws.write("A3", "서술", subtitle_fmt)
    ws.merge_range("A4:H4", disclosure["narrative_sections"].get("risk_management", ""), wrap)

    row = 6
    ws.write(row, 0, "물리적 리스크 평가", subtitle_fmt)
    row += 1
    ws.write(row, 0, "분석 연도", bold)
    ws.write(row, 1, physical.get("assessment_year", year))
    row += 1
    ws.write(row, 0, "모델 상태", bold)
    ws.write(row, 1, physical.get("model_status", ""))
    row += 1
    ws.write(row, 0, "산업화 대비 온난화", bold)
    ws.write(row, 1, physical.get("warming_above_preindustrial", ""))
    row += 2

    ws.write(row, 0, "시설별 물리적 리스크", subtitle_fmt)
    row += 1
    headers = ["시설 ID", "시설명", "위치", "리스크 수준", "연간 예상 손실 (USD)", "홍수", "태풍", "폭염", "가뭄", "해수면 상승"]
    for col_i, h in enumerate(headers):
        ws.write(row, col_i, h, hdr)
    row += 1
    for fac in physical.get("facilities", []):
        ws.write(row, 0, fac["facility_id"])
        ws.write(row, 1, fac["facility_name"])
        ws.write(row, 2, fac.get("location", ""))
        ws.write(row, 3, fac["overall_risk_level"])
        ws.write(row, 4, fac["total_expected_annual_loss"], money_fmt)
        # Per-hazard EAL
        hazard_map = {h["hazard_type"]: h for h in fac.get("hazards", [])}
        for col_i, ht in enumerate(["flood", "typhoon", "heatwave", "drought", "sea_level_rise"], start=5):
            h = hazard_map.get(ht)
            ws.write(row, col_i, h["potential_loss"] if h else 0, num_fmt)
        row += 1

    # ───────────────────────────────────────────────────────────────────
    # Sheet 5: Metrics & Targets
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("지표 및 목표")
    ws.set_column("A:A", 35)
    ws.set_column("B:B", 25)

    ws.merge_range("A1:B1", "지표 및 목표 — Metrics & Targets", title_fmt)
    ws.write("A3", "서술", subtitle_fmt)
    ws.merge_range("A4:B4", disclosure["narrative_sections"].get("metrics_and_targets", ""), wrap)

    row = 6
    metrics = disclosure.get("metrics", {})

    # Emissions
    em = metrics.get("emissions", {})
    ws.write(row, 0, "온실가스 배출량", subtitle_fmt)
    row += 1
    for label, key in [
        ("Scope 1 (tCO2e)", "scope1_tco2e"),
        ("Scope 2 (tCO2e)", "scope2_tco2e"),
        ("Scope 3 (tCO2e)", "scope3_tco2e"),
        ("총 배출량 (tCO2e)", "total_tco2e"),
        ("원단위 (tCO2e/매출 백만)", "intensity_tco2e_per_revenue"),
    ]:
        ws.write(row, 0, label)
        ws.write(row, 1, em.get(key, 0), num_fmt)
        row += 1

    row += 1
    # Targets
    tgt = metrics.get("targets", {})
    ws.write(row, 0, "감축 목표", subtitle_fmt)
    row += 1
    ws.write(row, 0, "기준연도")
    ws.write(row, 1, tgt.get("base_year", ""))
    row += 1
    ws.write(row, 0, "목표연도")
    ws.write(row, 1, tgt.get("target_year", ""))
    row += 1
    ws.write(row, 0, "감축 목표 (%)")
    ws.write(row, 1, tgt.get("reduction_target_pct", 0))
    row += 1
    ws.write(row, 0, "과학기반 (SBTi)")
    ws.write(row, 1, "예" if tgt.get("science_based") else "아니오")

    # ───────────────────────────────────────────────────────────────────
    # Sheet 6: Gap Analysis
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("갭 분석")
    ws.set_column("A:A", 20)
    ws.set_column("B:F", 14)
    ws.set_column("G:G", 50)

    ws.merge_range("A1:G1", "갭 분석 — Gap Analysis", title_fmt)
    row = 2
    headers = ["카테고리", "현재 점수", "목표 점수", "갭", "노력", "우선순위", "권고 조치"]
    ws.write_row(row, 0, headers, hdr)
    row += 1
    for gap in esg.get("gap_analysis", []):
        ws.write(row, 0, gap["category"])
        ws.write(row, 1, gap["current_score"])
        ws.write(row, 2, gap["target_score"])
        ws.write(row, 3, gap["gap"])
        effort_labels = {"low": "낮음", "medium": "중간", "high": "높음"}
        ws.write(row, 4, effort_labels.get(gap["effort"], gap["effort"]))
        ws.write(row, 5, gap["priority_score"])
        actions = ", ".join(gap.get("recommended_actions", []))
        ws.write(row, 6, actions, wrap)
        row += 1

    # ───────────────────────────────────────────────────────────────────
    # Sheet 7: Regulatory Timeline
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("규제 일정")
    ws.set_column("A:A", 30)
    ws.set_column("B:B", 15)
    ws.set_column("C:C", 50)
    ws.set_column("D:D", 25)

    ws.merge_range("A1:D1", "규제 일정 — Regulatory Timeline", title_fmt)
    row = 2
    ws.write_row(row, 0, ["규제명", "일자", "설명", "출처"], hdr)
    row += 1
    for dl in esg.get("regulatory_deadlines", []):
        ws.write(row, 0, dl.get("name", ""))
        ws.write(row, 1, dl.get("date", ""))
        ws.write(row, 2, dl.get("description", ""), wrap)
        ws.write(row, 3, dl.get("source", ""))
        row += 1

    # ───────────────────────────────────────────────────────────────────
    # Sheet 8: Raw Data
    # ───────────────────────────────────────────────────────────────────
    ws = wb.add_worksheet("Raw Data")
    ws.set_column("A:A", 15)
    ws.set_column("B:N", 18)

    ws.merge_range("A1:N1", "시설별 원시 데이터", title_fmt)
    row = 2
    headers = [
        "시설 ID", "시설명", "섹터", "위치",
        "Scope 1", "Scope 2", "Scope 3",
        "매출 (USD)", "EBITDA", "자산가치",
        "전환 NPV", "자산 대비 (%)",
        "물리 EAL", "물리 리스크",
    ]
    ws.write_row(row, 0, headers, hdr)
    row += 1

    # Build lookup maps for transition and physical results
    tr_map = {f["facility_id"]: f for f in transition.get("facilities", [])}
    pr_map = {f["facility_id"]: f for f in physical.get("facilities", [])}

    for fac in facilities:
        fid = fac["facility_id"]
        tr = tr_map.get(fid, {})
        pr = pr_map.get(fid, {})
        bg = alt_row if (row % 2 == 0) else None
        ws.write(row, 0, fid, bg)
        ws.write(row, 1, fac.get("name", ""), bg)
        ws.write(row, 2, fac.get("sector", ""), bg)
        ws.write(row, 3, fac.get("location", ""), bg)
        ws.write(row, 4, fac.get("current_emissions_scope1", 0), num_fmt)
        ws.write(row, 5, fac.get("current_emissions_scope2", 0), num_fmt)
        ws.write(row, 6, fac.get("current_emissions_scope3", 0), num_fmt)
        ws.write(row, 7, fac.get("annual_revenue", 0), num_fmt)
        ws.write(row, 8, fac.get("ebitda", 0), num_fmt)
        ws.write(row, 9, fac.get("assets_value", 0), num_fmt)
        ws.write(row, 10, tr.get("delta_npv", 0), money_fmt)
        ws.write(row, 11, (tr.get("npv_as_pct_of_assets", 0) or 0) / 100, pct_fmt)
        ws.write(row, 12, pr.get("total_expected_annual_loss", 0), money_fmt)
        ws.write(row, 13, pr.get("overall_risk_level", ""), bg)
        row += 1

    wb.close()
    buf.seek(0)
    return buf
