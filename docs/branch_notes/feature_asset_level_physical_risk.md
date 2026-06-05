# 브랜치 노트: feature/asset-level-physical-risk

## 브랜치 생성 배경

`main` 브랜치에서 분기. 기존 물리적 리스크 모델은 한국을 6개 권역으로 나눈 정적(static) 평균값을 사용했기 때문에, **같은 권역 안의 모든 자산이 동일한 위험값을 가지는 문제**가 있었다. Client RE Fund의 두 자산(서울 종로구, 경기 시흥시)이 모두 `inland_central` 권역으로 분류되어 동일한 홍수/폭염/가뭄 값이 나왔고, 이를 자산 좌표 기반의 실제 기후 데이터로 개선하기 위해 생성되었다.

---

## 이 브랜치에서 해결하려던 문제

1. **좌표 무관 동일값 문제**: 서울과 시흥이 같은 권역으로 묶여 홍수/폭염/가뭄 손실이 완전히 동일하게 계산됨
2. **정적 권역 모델의 한계**: KMA 권역 평균값은 자산별 미기후(microclimate) 차이를 반영 불가
3. **데이터 출처 불투명**: 어떤 hazard가 API 기반인지 정적 모델 기반인지 결과에 표시되지 않음
4. **API 안정성**: Open-Meteo 429 에러 발생 시 앱이 실패하거나 오류 없이 잘못된 값을 반환할 위험

---

## 주요 변경사항

### 1. 홍수·폭염·가뭄 → ERA5 좌표 기반 계산으로 전환 (`6514b73`, `bd36bdd`)
- `open_meteo.py`의 `get_api_derived_baselines(lat, lon)` 함수가 자산 좌표로 ERA5 30년 데이터를 호출
- 반환값:
  - `gumbel_params`: 홍수용 Gumbel 분포 파라미터 (연최대 일강수량 기반 MoM 피팅)
  - `heatwave_days`: 33°C 초과일 카운트 (KMA 폭염 기준)
  - `drought_days`: 연간 최장 연속 무강수일 (1mm 미만)
- `assess_physical_risk()` 기본값이 `use_api_data=True`로 변경됨

### 2. 태풍·해수면 상승은 여전히 정적 권역 기반
- 태풍: KMA NTC 1951-2023 통계 기반 권역 평균 빈도 사용 (Open-Meteo에 태풍 경로 데이터 없음)
- 해수면 상승: IPCC AR6 WG1 Ch.9 기반 시나리오별 상승량 + 해안/내륙 이진 분류
- 두 hazard는 구조적으로 API 연동이 불가하므로 의도적으로 정적 모델 유지

### 3. `data_source` 및 `api_warnings` 필드 추가 (`6514b73`, `8438246`)
- 각 hazard 결과 dict에 `data_source` 필드 추가: `"open_meteo_era5"` 또는 `"static_config"`
- API 실패로 폴백된 hazard는 `api_warnings` 리스트에 기록
- Streamlit 물리적 리스크 페이지에 경고 배너 및 영향 시설/hazard 표 추가

### 4. Open-Meteo 캐시 개선 (`498483c`)
- 캐시 키에 `start_date`, `end_date`, `variables`를 포함하여 설정 변경 시 자동 무효화
- 캐시 히트/미스 통계 (`_cache_stats`) 추적
- 결과 dict에 `_cache_meta.cache_hit` 필드 포함

### 5. 429 Rate Limit 대응 (`2bd6d61`, `f990ae6`)
- HTTP 429 감지 시 모듈 레벨 플래그 설정 → 이후 API 호출 즉시 스킵
- 캐시 히트는 rate-limit 무관하게 정상 서비스
- 요청 간 1초 딜레이 추가
- **300초(5분) 쿨다운 윈도우**: 쿨다운 만료 후 프로브 요청 1회 허용, 재429 시 쿨다운 리셋
- `rate_limit_cooldown_remaining()` 함수로 UI에 남은 대기 시간 표시
- Streamlit 페이지에 쿨다운 카운트다운 배너 추가

### 6. Excel export 스크립트 생성 (`4599b1e`, `9a59b4b`)
- `sandbox/export_physical_risk_feature.py`: Client RE Fund 물리적 리스크 결과를 5개 시트 Excel로 저장
- 시트 구성: Summary / Input_Facilities / Hazard_Results / Data_Source_Explanation / Methodology_Notes
- Hazard_Results에 `risk_level_criteria`, `eal_as_pct_of_assets` 컬럼 포함
- `has_api_warning`, `cache_hit`, `diff_pct` 컬럼은 고객사 발송용 파일에서 제거
- 태풍·해수면 상승은 모델 특성상 항상 `static_config`로 표시됨

### 7. 기타
- `scatter_mapbox` → `scatter_map` 마이그레이션 (Plotly 6.x 변경) 후 롤백 (`d798fc5`, `6167ffe`)
- 내부 hazard dict 키(`_cache_meta`, `_api_status`)가 DataFrame에 노출되는 버그 수정 (`ab52066`)
- 검증 및 디버그 스크립트 추가: `validate_hazards.py`, `debug_streamlit_data.py`

---

## 변경된 주요 파일

| 파일 | 변경 내용 |
|---|---|
| `backend/app/services/open_meteo.py` | ERA5 API 호출, 캐시 개선, 429 대응, 쿨다운 로직 |
| `backend/app/services/physical_risk.py` | `data_source` 추적, `api_warnings` 생성, `use_api_data=True` 기본값 |
| `streamlit_app/pages/3_물리적_리스크.py` | `data_source` 표시, 429 경고 배너, 쿨다운 카운트다운 |
| `streamlit_app/utils/company_data.py` | `get_cached_physical()`에 `use_api_data` 파라미터 노출 |
| `sandbox/export_physical_risk_feature.py` | 신규 생성 — Excel export |
| `backend/sandbox/validate_hazards.py` | 신규 생성 — hazard 계산 검증 스크립트 |
| `backend/sandbox/debug_streamlit_data.py` | 신규 생성 — Streamlit 데이터 디버그 |
| `sandbox/test_api_default.py` | 신규 생성 |
| `sandbox/test_api_status.py` | 신규 생성 |
| `sandbox/test_cache.py` | 신규 생성 |
| `sandbox/validate_physical_risk.py` | 신규 생성 |
| `docs/physical_risk_asset_level_update.md` | 신규 생성 — 방법론 업데이트 요약 |

---

## 모델/데이터 측면에서 달라진 점

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 홍수 Gumbel 파라미터 | KMA 6개 권역 평균 (static_config) | 자산 좌표 ERA5 30년 일강수량 MoM 피팅 |
| 폭염 기준일수 | KMA 권역 평균 | 자산 좌표 ERA5 33°C 초과일 직접 카운트 |
| 가뭄 기준일수 | KMA 권역 평균 | 자산 좌표 ERA5 연간 최장 연속 무강수일 |
| 태풍 | 권역 기반 (변경 없음) | 동일 |
| 해수면 상승 | IPCC AR6 기반 (변경 없음) | 동일 |
| `use_api_data` 기본값 | `False` | `True` |

---

## UI/Streamlit 측면에서 달라진 점

- 물리적 리스크 페이지에 hazard별 `data_source` 컬럼 추가 (어떤 hazard가 ERA5 기반인지 표시)
- API 실패/429 시 경고 배너 표시: 영향받은 시설·hazard 목록, 쿨다운 잔여 시간
- 데이터 소스 안내 `st.info` 박스 추가

---

## 고객사 또는 분석 결과에 미치는 영향

- 서울 종로구(Concordian)와 경기 시흥시(Logisco Siheung)의 홍수·폭염·가뭄 값이 서로 다르게 계산됨 (기존에는 동일)
- Excel 결과물의 `data_source` 컬럼으로 각 hazard의 데이터 근거 명시 가능
- GRESB 2025 Physical Risk 평가 시 ERA5 근거 제시 가능 (홍수·폭염·가뭄 한정)

---

## 의도적으로 남겨둔 한계

1. **태풍·해수면 상승의 정적 모델 유지**: Open-Meteo에 태풍 경로 데이터 없음. IBTrACS 연동 미구현.
2. **BI / revenue-based loss 정의 추가 검토 필요**:
   - flood의 `business_interruption_cost` 필드가 항상 0을 반환하는 버그 존재 (EAL 계산 자체는 BI 포함되어 정확함 — `bi_cost` 변수가 루프 내 `bi_loss`와 별개로 관리되는 코드 구조 문제)
   - heatwave는 모델 전체가 revenue 기반이어서 `annual_revenue=0`이면 손실이 전부 0
   - drought의 BI 계산이 revenue × water_intensity 기반이므로 동일하게 revenue=0 시 0
3. **강수→침수 변환 단순화**: 유출계수(rational method) 방식, 지형·배수·상류 기여 미반영
4. **ERA5 해상도 한계**: 0.1° 격자 평균값 사용, 도시 내 미기후 차이 미반영
5. **시나리오 하드코딩**: Excel export 스크립트는 `current_policies`, 2030년으로 고정 (Streamlit 사이드바 연동 안 됨)

---

## 후속 작업 후보

- [ ] flood `bi_cost` 버그 수정 (`physical_risk.py` `_flood_risk_model`)
- [ ] 태풍 모델 IBTrACS 또는 좌표 기반으로 전환
- [ ] Excel export 시나리오/연도 파라미터화 (하드코딩 제거)
- [ ] revenue=0 자산에 대한 BI 손실 처리 방침 결정
- [ ] EAL 신뢰구간 추가 (현재 점추정치만 있음)

---

## 관련 커밋 목록

| 커밋 해시 | 날짜 | 내용 |
|---|---|---|
| `6b86203` | 2026-06-04 | chore: add .gitignore to exclude pycache, outputs, .env, .claude |
| `6514b73` | 2026-06-04 | feat: add per-hazard data_source tracking and API fallback warnings |
| `498483c` | 2026-06-04 | feat: improve cache key and add hit/miss tracking in open_meteo.py |
| `8438246` | 2026-06-04 | feat: show data_source and api_warnings in physical risk Streamlit page |
| `bd36bdd` | 2026-06-04 | feat: set use_api_data=True as default in assess_physical_risk() |
| `9cdc62d` | 2026-06-04 | feat: restore Client RE Fund facilities and add validation script |
| `e77e9df` | 2026-06-04 | docs: add CLAUDE.md with main merge restriction rule |
| `b33c0c1` | 2026-06-04 | docs: add physical risk asset-level update summary |
| `9ec97b0` | 2026-06-04 | docs: add methodology info box to physical risk page |
| `4599b1e` | 2026-06-04 | feat: add Client RE Fund physical risk Excel export script |
| `ab52066` | 2026-06-04 | fix: strip internal hazard keys before DataFrame build in physical risk page |
| `d798fc5` | 2026-06-04 | fix: migrate scatter_mapbox to scatter_map (Plotly 6.x deprecation) |
| `6167ffe` | 2026-06-04 | Revert: migrate scatter_mapbox to scatter_map |
| `2bd6d61` | 2026-06-04 | feat: add 429 rate-limit handling for Open-Meteo API |
| `f990ae6` | 2026-06-05 | fix: replace permanent rate-limit flag with 5-minute cooldown window |
| `ef1d45a` | 2026-06-05 | chore: add sandbox debug and validation scripts |
| `9a59b4b` | 2026-06-05 | fix: set Client RE Fund annual_revenue and ebitda to 0; clean up Excel export columns |

> 이 브랜치는 Mastern으로 병합 완료 (`6f84251`, 2026-06-05).
