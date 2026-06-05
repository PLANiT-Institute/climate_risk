# 물리적 리스크 모델 기술 문서

> **용도**: 인수인계 / 감사 / 재검토
> **기준 코드**: `backend/app/services/physical_risk.py`, `backend/app/services/open_meteo.py`
> **모델 버전**: `analytical_v1`
> **작성 기준일**: 2026-06-05

---

## 목차

1. [모델 목적](#1-모델-목적)
2. [전체 계산 구조](#2-전체-계산-구조)
3. [입력값 정의](#3-입력값-정의)
4. [Hazard별 현재 구현 상태](#4-hazard별-현재-구현-상태)
5. [data_source 규칙](#5-data_source-규칙)
6. [Open-Meteo / ERA5 처리 방식](#6-open-meteo--era5-처리-방식)
7. [손실 항목 정의](#7-손실-항목-정의)
8. [알려진 버그 / 주의사항](#8-알려진-버그--주의사항)
9. [GRESB 대응 관점 해석](#9-gresb-대응-관점-해석)
10. [후속 작업 후보](#10-후속-작업-후보)

---

## 1. 모델 목적

- **GRESB Physical Risk 대응용** 자산/시설 단위 물리적 리스크 분석
- 5개 hazard(홍수, 태풍, 폭염, 가뭄, 해수면 상승)에 대해 연간 기대손실(EAL) 계산
- **현재 버전은 완전한 CLIMADA 구현이 아님.** CLIMADA의 Hazard × Exposure × Vulnerability 구조를 참고한 단순화 분석 모델임
  - CLIMADA와의 주요 차이: 확률분포 샘플링 없음 (점추정), 공간 해상도 단순화, 취약도 함수 단순화

---

## 2. 전체 계산 구조

```
[입력]
  facility (lat, lon, sector, assets_value, annual_revenue)
  scenario_id, assessment_year
  use_api_data (True/False)
        ↓
[기후 데이터]
  use_api_data=True  → Open-Meteo ERA5 API (홍수/폭염/가뭄)
  use_api_data=False → static_config 권역 평균값
  태풍/해수면 상승   → 항상 static_config
        ↓
[Hazard 강도 계산] × 5개
  + IPCC AR6 기반 시나리오별 온도 상승 → 빈도/강도 배율 적용
        ↓
[Vulnerability / Damage Function]
  홍수:  depth-damage curve (USACE/Kim&Lee 2019)
  태풍:  HAZUS-MH 풍속 피해율 테이블
  폭염:  ILO 2019 생산성 손실률
  가뭄:  업종별 수자원 의존도 (water_intensity)
  해수면: depth-damage curve × 0.3 (부분 적응 가정) / 30년 연환산
        ↓
[potential_loss] (hazard별)
  = direct_damage + BI_loss (hazard별 포함 여부 다름 — §7 참조)
        ↓
[compound risk 조정]
  분산-공분산 근사: total_EAL += Σ ρ_ij × √(EAL_i × EAL_j)
  상관계수 출처: KMA 1991-2020 공동발생 통계, IPCC AR6 Ch.11
        ↓
[total_expected_annual_loss] (시설 단위 합산)
        ↓
[출력]
  risk_level (High/Medium/Low), potential_loss, data_source, api_warnings
```

---

## 3. 입력값 정의

| 입력값 | 정의 | 사용처 |
|---|---|---|
| `facility_id` | 시설 고유 ID | 결과 식별, API warnings 로깅 |
| `facility_name` | 시설명 | 결과 표시 |
| `company` | 기업명 | 사이드바 필터링 (`get_facilities_by_company`) |
| `latitude` | 위도 (WGS84) | ERA5 API 좌표, 권역 분류 (`_region_type`) |
| `longitude` | 경도 (WGS84) | ERA5 API 좌표, 권역 분류 (`_region_type`) |
| `region_type` | 6개 권역 분류 (코드 내부 계산) | static_config 파라미터 조회 키 |
| `sector` | 업종 코드 (예: `real_estate`) | 폭염 실외노출 비율, 가뭄 수자원 의존도 |
| `assets_value` | 자산가치 (USD) | direct damage 계산, risk_level 분류 |
| `annual_revenue` | 연매출 (USD) | BI 손실, 폭염 장비효율 손실 계산 |
| `ebitda` | EBITDA (USD) | **현재 모델에서 직접 사용되지 않음** (확인 완료) |
| `scenario_id` | NGFS 시나리오 | 온도 상승량, 빈도/강도 배율 결정 |
| `assessment_year` | 평가 연도 | 온도 상승량 보간 |
| `use_api_data` | ERA5 API 사용 여부 (기본: `True`) | 홍수/폭염/가뭄 파라미터 소스 결정 |

**권역 분류 기준 (`_region_type`):**

| 권역 | 해당 지역 예시 |
|---|---|
| `coastal_south` | 부산, 여수, 광양 (위도 < 35.2, 경도 ≤ 128.5) |
| `coastal_east` | 포항, 울산 (경도 > 129.0 또는 위도 < 35.2 경도 > 128.5) |
| `coastal_west` | 인천, 당진 (경도 < 126.7) |
| `mountain` | 단양, 영월 (위도 > 36.5, 경도 > 128.0) |
| `inland_south` | 구미 (위도 < 36.5, 경도 > 127.5) |
| `inland_central` | 화성, 평택, 아산, 서울, 시흥 (나머지) |

---

## 4. Hazard별 현재 구현 상태

### 4.1 Flood (홍수)

| 항목 | 내용 |
|---|---|
| **데이터 소스** | ERA5 일강수량 (1994-2023, 30년) 또는 KMA 권역 Gumbel 파라미터 |
| **좌표 사용** | O (ERA5 API 모드) |
| **static_config 사용** | O (폴백 또는 API=False) — `FLOOD_GUMBEL_PARAMS` (예: inland_central: μ=160, σ=42) |
| **Open-Meteo/ERA5** | O — 좌표 기반 연최대 일강수량 MoM Gumbel 피팅 → μ, σ 추출 |
| **계산 방식** | Gumbel Type I 분위수 → 재현기간별 강수량(mm) → 침수심(cm) 변환 (유출계수 C=0.8) → depth-damage curve → 손실 |
| **재현기간** | 7개: 5, 10, 20, 50, 100, 200, 500년 |
| **direct damage** | O — `assets_value × damage_frac` |
| **BI 손실** | O — `_daily_revenue × bi_day_count` (침수심별 minor/moderate/severe/catastrophic) |
| **potential_loss** | `Σ (direct_damage + BI_loss) × prob_band` — **direct + BI 합산 EAL** |
| **business_interruption_cost 반환값** | **항상 0 (버그)** — 상세 내용 §8 참조 |
| **기후변화 배율** | 빈도 배율 × 강도 배율 복합 (IPCC AR6 WG1 Ch.8, +5.5%/°C) |
| **현재 한계** | 지형·배수·상류 기여 미반영. 강수→침수 변환이 단순 유출계수 방식 |
| **후속 개선 후보** | `bi_cost` 버그 수정, SCS Curve Number 적용, 배수 시스템 반영 |

### 4.2 Typhoon (태풍)

| 항목 | 내용 |
|---|---|
| **데이터 소스** | KMA NTC 1951-2023 권역별 상륙 빈도 통계 |
| **좌표 사용** | X — 권역 분류만 사용 |
| **static_config 사용** | O (항상) — `TYPHOON_ANNUAL_FREQUENCY` (예: inland_central: 0.3회/년) |
| **Open-Meteo/ERA5** | X — 연간 최대 풍속 데이터는 ±20% 빈도 보정에만 선택적 사용 (현재 구현에서 API 사용 시 wind_speed 보정 로직 있으나 data_source는 항상 static_config) |
| **계산 방식** | Poisson 빈도 × 카테고리별 피해율(HAZUS-MH) × 자산가치. 기후변화로 Cat 4-5 비율 증가 반영 (+13%/°C, IPCC AR6) |
| **direct damage** | O — `adjusted_freq × expected_damage_rate × assets_value` |
| **BI 손실** | O — `adjusted_freq × expected_bi_days × _daily_revenue` |
| **potential_loss** | `direct_eal + bi_eal` |
| **business_interruption_cost** | 정확 (`round(bi_eal)`) |
| **현재 한계** | 자산 좌표 미반영 (권역 평균). IBTrACS 미연동. 200km 반경 기준 |
| **후속 개선 후보** | IBTrACS 연동, 좌표 기반 경로 근접도 반영 |

### 4.3 Heatwave (폭염)

| 항목 | 내용 |
|---|---|
| **데이터 소스** | ERA5 일최고기온 (1994-2023) 또는 KMA 권역 기준일수 |
| **좌표 사용** | O (ERA5 API 모드) |
| **static_config 사용** | O (폴백) — `HEATWAVE_BASELINE_DAYS` (예: inland_central: 16일) |
| **Open-Meteo/ERA5** | O — 33°C 초과일 카운트 (KMA 폭염 온도 기준) |
| **계산 방식** | 폭염 일수 × (실외 비율 × 실외손실률 + 실내 비율 × 실내손실률) × 일매출 + 업종별 장비효율 손실 |
| **real_estate 실외 노출 비율** | 0.20 (20%) |
| **direct damage** | X — 자산 직접 손상 없음 |
| **BI 손실** | O — 모델 전체가 revenue 기반 (생산성 손실 + 장비효율 손실) |
| **potential_loss** | `productivity_loss + equipment_loss` — **전액 revenue 기반** |
| **business_interruption_cost** | `productivity_loss`만 반환 (equipment_loss 미포함) |
| **기후변화 배율** | +4.0일/°C (HEATWAVE_DAYS_PER_DEGREE) |
| **현재 한계** | 연속일수 기준 미적용 (KMA는 2일 이상 연속 요구). ERA5 격자 평균 사용 |
| **후속 개선 후보** | 연속일수 기준 적용, WBGT 기반 생산성 손실 모델 |

### 4.4 Drought (가뭄)

| 항목 | 내용 |
|---|---|
| **데이터 소스** | ERA5 일강수량 → 연간 최장 연속 무강수일 또는 KMA 권역 기준일수 |
| **좌표 사용** | O (ERA5 API 모드) |
| **static_config 사용** | O (폴백) — `DROUGHT_BASELINE_DAYS` (예: inland_central: 22일) |
| **Open-Meteo/ERA5** | O — 1mm 미만 연속일 최대값 |
| **계산 방식** | 가뭄일수 비례 매출 손실 (`revenue_at_risk`) + 심각도별 BI (`bi_cost`). 업종별 수자원 의존도(`water_intensity`) 가중 |
| **real_estate water_intensity** | 0.03 (3%) |
| **direct damage** | X |
| **BI 손실** | O — revenue × water_intensity 기반 |
| **potential_loss** | `revenue_at_risk + bi_cost` — **전액 revenue 기반** |
| **business_interruption_cost** | `bi_cost`만 반환 (`revenue_at_risk` 미포함) |
| **현재 한계** | K-water 공식 가뭄 지수와 다를 수 있음. 지하수·저수지 미반영 |
| **후속 개선 후보** | SPI/PDSI 지수 연동, 용수 공급 대안 반영 |

### 4.5 Sea Level Rise (해수면 상승)

| 항목 | 내용 |
|---|---|
| **데이터 소스** | IPCC AR6 WG1 Ch.9 시나리오별 해수면 상승량 |
| **좌표 사용** | X — 해안/내륙 이진 분류만 사용 (`region.startswith("coastal")`) |
| **static_config 사용** | O (항상) |
| **Open-Meteo/ERA5** | X |
| **계산 방식** | SLR(mm) → depth-damage curve → 피해율 × 0.3 (부분 적응 할인) / 30년 연환산 |
| **비해안 자산** | `potential_loss = 0` (coastal 권역이 아니면 즉시 0 반환) |
| **direct damage** | O — 자산가치 기반 만성 침수 손실 |
| **BI 손실** | X |
| **potential_loss** | `assets × damage_frac × 0.3 / 30` — **자산 기반만** |
| **business_interruption_cost** | 항상 0 (의도적) |
| **현재 한계** | 고도 데이터 미사용. 해안선 거리 미계산. 해안/내륙 이진 판단만 가능 |
| **후속 개선 후보** | DEM 기반 고도 확인, 해안선 거리 계산, CoastalDEM 연동 |

---

## 5. data_source 규칙

| hazard | ERA5 API 성공 시 | ERA5 API 실패 / use_api_data=False |
|---|---|---|
| flood | `open_meteo_era5` | `static_config` |
| heatwave | `open_meteo_era5` | `static_config` |
| drought | `open_meteo_era5` | `static_config` |
| typhoon | `static_config` (항상) | `static_config` (항상) |
| sea_level_rise | `static_config` (항상) | `static_config` (항상) |

> **주의**: API 부분 실패 시 같은 시설이라도 flood는 `open_meteo_era5`, typhoon은 `static_config`가 될 수 있음. Hazard_Results 시트의 `data_source` 컬럼을 반드시 확인할 것.

---

## 6. Open-Meteo / ERA5 처리 방식

### 기본 설정
- `use_api_data=True`가 기본값 (`assess_physical_risk()` 서명)
- ERA5 데이터 기간: 1994-01-01 ~ 2023-12-31 (30년)
- 요청 변수: 일강수량(`precipitation_sum`), 일최고기온(`temperature_2m_max`)

### 캐시 구조
```
캐시 키 = f"{lat:.4f}_{lon:.4f}_{start_date}_{end_date}_{variables}"
```
- 모듈 레벨 인메모리 딕셔너리 (`_cache: Dict[str, dict]`)
- start_date, end_date, variables가 키에 포함되어 설정 변경 시 자동 무효화
- 앱 재시작 시 캐시 초기화 (영구 저장 없음)

| 이벤트 | 동작 |
|---|---|
| Cache HIT | API 호출 없음, `_cache_meta.cache_hit = True` |
| Cache MISS | Open-Meteo API 호출, 결과 저장 |
| 캐시 히트 (rate limit 중) | rate limit 무관하게 정상 반환 |

### 429 Rate Limit 대응

```
429 수신
  → _rate_limited_at = time.time()  설정
  → 이후 is_rate_limited() = True 동안 API 호출 스킵 → None 반환 → static_config 폴백
  → 300초(5분) 후 is_rate_limited() = False
  → 다음 요청에서 프로브 1회 허용
  → 재429 시 _rate_limited_at 리셋
```

- 요청 간 1초 딜레이 (`time.sleep(1)`)
- `rate_limit_cooldown_remaining()`: 잔여 쿨다운 초 반환 (Streamlit UI 표시용)

### API 실패 시 결과 표시

| 조건 | api_warnings 내용 |
|---|---|
| 429 rate limit | `"{hazard}: Open-Meteo 요청 제한(429) — 일시적으로 정적 권역 기반 값 사용"` |
| 기타 API 오류 | `"{hazard}: API 오류 — 일시적으로 정적 권역 기반 값 사용"` |
| 정상 (ERA5 사용) | api_warnings 없음 |

---

## 7. 손실 항목 정의

### potential_loss 구성 (hazard별)

| hazard | direct_damage | BI 손실 | 구성 요약 |
|---|---|---|---|
| flood | O (자산 × damage_frac) | O (revenue × bi_days) | `Σ(direct + BI) × prob_band` |
| typhoon | O (자산 × damage_rate) | O (revenue × bi_days) | `direct_eal + bi_eal` |
| heatwave | X | O (revenue 기반 전체) | `productivity_loss + equipment_loss` |
| drought | X | O (revenue 기반 전체) | `revenue_at_risk + bi_cost` |
| sea_level_rise | O (자산 × damage_frac / 30) | X | `annual_loss` |

### total_expected_annual_loss

시설 단위 복합 리스크 조정 EAL:

```python
total_eal = Σ potential_loss[hazard] + Σ ρ_ij × √(EAL_i × EAL_j)
```

compound 상관계수 예시: flood-typhoon 0.40, drought-heatwave 0.35

### business_interruption_cost 반환값 현황

| hazard | 반환값 | 비고 |
|---|---|---|
| flood | **항상 0** | **버그** — BI는 EAL에 포함되지만 필드 값은 잘못됨 |
| typhoon | 정확 (`bi_eal`) | |
| heatwave | `productivity_loss`만 | equipment_loss 미포함 |
| drought | `bi_cost`만 | revenue_at_risk 미포함 |
| sea_level_rise | 0 | 의도적 |

---

## 8. 알려진 버그 / 주의사항

### [BUG-001] flood `business_interruption_cost` 항상 0 반환

**파일**: `backend/app/services/physical_risk.py`, `_flood_risk_model()`
**원인**: `bi_cost = 0.0`으로 초기화 후 루프 내에서 갱신되지 않음. BI는 `bi_loss`로 계산되어 `eal`에 합산되지만, `bi_cost` 변수는 초기값 0 그대로 반환됨.

```python
bi_cost = 0.0          # ← 초기화
for ...:
    bi_loss = ...      # ← 루프 내 계산
    eal += (loss + bi_loss) * prob_band  # ← eal에는 포함
# bi_cost는 갱신 안 됨
return {"business_interruption_cost": round(bi_cost)}  # ← 항상 0
```

**영향**: `potential_loss` 계산 자체는 BI를 포함하므로 EAL 결과는 정확함. 단, BI가 얼마인지 별도로 표시하는 기능만 고장난 상태.

---

### [BUG-002] potential_loss 정의가 hazard별로 불일치

| hazard | potential_loss 의미 |
|---|---|
| flood | EAL (재현기간 적분값) |
| typhoon | EAL (빈도 × 피해율) |
| heatwave | 연간 손실 (만성, 확률 적분 없음) |
| drought | 연간 손실 (만성, 확률 적분 없음) |
| sea_level_rise | 연간 손실 (30년 평균) |

홍수/태풍은 확률 가중 EAL, 나머지 3개는 결정론적 연간 손실로 개념이 다름.

---

### [주의-001] annual_revenue=0 자산

heatwave, drought의 `potential_loss`가 전액 revenue 기반이므로 `annual_revenue=0`이면 두 hazard 손실이 완전히 0이 됨. flood/typhoon은 자산 기반 direct_damage가 있어 정상 계산됨.

---

### [주의-002] typhoon 권역 기반 한계

서울(inland_central)과 시흥(inland_central)은 태풍 빈도가 동일 (0.3회/년). 자산 좌표는 태풍 계산에 영향을 주지 않음.

---

### [주의-003] sea_level_rise 해안/내륙 이진 판단

`region.startswith("coastal")` 여부만으로 노출을 결정. 고도, 해안선과의 거리, 제방 유무 등 미반영. 서울 도심 자산은 inland_central → SLR `potential_loss = 0`.

---

### [주의-004] API 부분 실패 시 혼재

같은 평가 실행 내에서도 일부 시설은 ERA5 기반, 일부 시설은 static_config 기반 값을 가질 수 있음. `data_source` 컬럼으로 개별 확인 필요.

---

## 9. GRESB 대응 관점 해석

### 설명 가능한 부분

| 항목 | 설명 |
|---|---|
| 홍수 데이터 근거 | ERA5 30년 일강수량 기반 Gumbel 피팅 → IPCC AR6 강도 배율 적용 |
| 폭염 데이터 근거 | ERA5 일최고기온 기반, KMA 33°C 폭염 기준 |
| 가뭄 데이터 근거 | ERA5 강수량 기반 연간 최장 연속 무강수일 |
| 시나리오 근거 | NGFS 시나리오 × IPCC AR6 온도 경로 |
| 결과 재현 가능성 | 코드, 입력값, 데이터 소스 모두 기록됨 |

### 설명 시 조심해야 하는 부분

| 항목 | 주의사항 |
|---|---|
| 태풍 | "좌표 기반 분석"이라고 말하면 안 됨 — 권역 평균값 사용 |
| 해수면 상승 | 고도 기반 노출 분석 아님 — 해안/내륙 이진 분류 |
| 신뢰구간 | 없음 — 모든 수치는 점추정 |
| 검증 여부 | 외부 기관 검증 없음 — 내부 개발 모델 |

### 고객사에 말할 수 있는 문구 (예시)

> "홍수, 폭염, 가뭄은 자산 좌표 기반 ERA5 30년 실측 기후 데이터를 사용하여 계산되었으며, IPCC AR6 기반 시나리오별 기후변화 배율이 적용되었습니다. 태풍 및 해수면 상승은 현재 권역 기반 정적 모델을 사용하고 있으며, 향후 개선 예정입니다."

### 말하면 안 되는 표현

| 표현 | 이유 |
|---|---|
| "CLIMADA 기반" | CLIMADA 구조를 참고한 단순화 모델이며 완전한 구현이 아님 |
| "site-specific 분석" | 태풍/해수면 상승은 권역 평균값 |
| "불확실성 범위 포함" | 신뢰구간 없음 |
| "engineering-grade" | 스크리닝 수준의 추정 모델 |

---

## 10. 후속 작업 후보

### 우선순위 High

| 항목 | 파일 | 내용 |
|---|---|---|
| flood `bi_cost` 버그 수정 | `physical_risk.py` | `bi_cost` 루프 내 누적 계산으로 수정 |
| `potential_loss` 정의 통일 | `physical_risk.py` | hazard별 EAL vs 연간손실 개념 정리 및 필드명 분리 |
| Excel export 시나리오 파라미터화 | `export_physical_risk_feature.py` | `current_policies` 하드코딩 제거 |

### 우선순위 Medium

| 항목 | 파일 | 내용 |
|---|---|---|
| BI 손실 포함 여부 정책 결정 | `physical_risk.py` | BI를 EAL에 포함할지 별도 표기할지 결정 |
| typhoon IBTrACS 적용 | `physical_risk.py`, `open_meteo.py` | 자산 좌표 기반 태풍 경로 근접도 반영 |
| heatwave `business_interruption_cost`에 equipment_loss 포함 여부 | `physical_risk.py` | 현재 productivity_loss만 반환 |

### 우선순위 Low

| 항목 | 내용 |
|---|---|
| sea_level_rise 고도/해안거리 기반 개선 | CoastalDEM 또는 국토부 수치표고모델 연동 |
| 가뭄 SPI/PDSI 지수 연동 | K-water 공식 지수와 일치 여부 검토 |
| EAL 신뢰구간 추가 | Gumbel 파라미터 불확실성 전파 (+/-30%) |
| 결과 export 자동화 | Streamlit에서 직접 Excel 다운로드 |
