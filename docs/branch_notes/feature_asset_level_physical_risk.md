# feature/asset-level-physical-risk 브랜치 노트

**작성일**: 2026-06-05  
**작성자**: Joowon Kweon (PLANiT Institute for Energy and Climate Policy)  
**브랜치 기반**: main

---

## 목차

1. [브랜치 목적](#1-브랜치-목적)
2. [작업 배경](#2-작업-배경)
3. [조사 과정](#3-조사-과정)
4. [주요 변경사항](#4-주요-변경사항)
5. [Hazard별 현재 상태](#5-hazard별-현재-상태)
6. [결과 변화 요약](#6-결과-변화-요약)
7. [데이터 소스와 경고 표시](#7-데이터-소스와-경고-표시)
8. [알려진 한계와 미해결 이슈](#8-알려진-한계와-미해결-이슈)
9. [GRESB 대응 관점](#9-gresb-대응-관점)
10. [후속 작업 후보](#10-후속-작업-후보)
11. [관련 커밋](#11-관련-커밋)

---

## 1. 브랜치 목적

- 기존 물리적 리스크 모델의 hazard 해상도 검증
- 가능한 hazard(홍수·폭염·가뭄)에 대해 Open-Meteo API를 통한 ERA5 기반 자산 좌표 계산 활성화
- GRESB 대응용 자산 단위 물리적 리스크 결과의 설명 가능성(explainability) 개선

---

## 2. 작업 배경

다음 문제 인식에서 출발했다.

**주요 발단**: 서울 자산(Concordian Seoul)과 시흥 자산(Logisco Siheung)의 홍수·폭염·가뭄 위험값이 동일하게 나오는 현상 발견.

조사 결과 확인된 원인:

| 문제 | 내용 |
|------|------|
| **권역 기반 hazard 계산** | 한국을 6개 권역으로 분류하고 권역별 평균 파라미터를 모든 자산에 일괄 적용. 자산의 실제 위도·경도가 hazard 계산에 반영되지 않았음 |
| **Open-Meteo 연동 미활성화** | `use_api_data=False` 기본값으로 인해 자산 좌표 기반 ERA5 계산이 비활성화 상태였음. 코드는 있었지만 쓰이지 않고 있었음 |
| **data_source 부재** | 결과물에 어떤 데이터 소스(ERA5 vs static_config)를 사용했는지 표시가 없어 사용자가 오해할 수 있었음 |
| **조용한 fallback** | API 실패 시 아무 알림 없이 static_config로 전환되어, 사용자가 ERA5 기반 결과라고 잘못 인식할 위험이 있었음 |

---

## 3. 조사 과정

아래 순서로 조사를 진행했다.

1. **CLIMADA 구조 검토**: 기존 물리적 리스크 모델(`backend/app/services/physical_risk.py`, `util/physical_risk.py`)의 hazard별 계산 경로 추적
2. **Hazard별 데이터 소스 추적**: 각 hazard가 `config.py` 권역 테이블을 직접 참조하는지, Open-Meteo를 호출하는지 확인
3. **`use_api_data=False / True` 비교**: 코드 분기 확인 후 True로 바꿨을 때 결과 차이 측정
4. **API vs static 결과 비교**: 동일 자산·시나리오에서 두 방식의 수치 차이 정량화 (→ [6절](#6-결과-변화-요약))
5. **`data_source`와 `api_warnings` 필요성 확인**: GRESB 감사 대응 및 내부 품질 관리를 위해 소스 추적이 필수임을 확인
6. **Streamlit 표시 방식 검토**: `streamlit_app/pages/3_물리적_리스크.py`에서 기존 테이블 구조 분석 후 data_source 컬럼과 경고 배너 추가 방식 결정
7. **429 rate limit 문제 확인**: Open-Meteo 무료 플랜에서 과도한 호출 시 429 응답이 발생하며, 기존 코드는 이에 대한 처리가 없었음

---

## 4. 주요 변경사항

| 변경사항 | 내용 |
|---------|------|
| `use_api_data=True` 기본값 변경 | `assess_physical_risk()` 함수의 기본값을 False → True로 변경 |
| flood / heatwave / drought → ERA5 | 세 hazard를 Open-Meteo Archive API(ERA5, 1994–2023, 30년)를 통한 자산 좌표 기반 계산으로 전환 |
| typhoon / sea_level_rise → static_config 유지 | Open-Meteo에 경로·해수면 데이터 없음. 권역 기반 계산 유지 |
| per-hazard `data_source` 추가 | 결과 딕셔너리에 hazard별 `"open_meteo_era5"` 또는 `"static_config"` 표시 |
| `api_warnings` 추가 | API 실패, fallback 발생, 정적 hazard 사용 시 경고 메시지 목록 반환 |
| Open-Meteo 캐시 키 개선 | `{lat},{lon}` → `{lat},{lon}|{start_date}|{end_date}|{variables}` (날짜·변수 변경 시 자동 무효화) |
| cache hit / miss 추적 추가 | `get_cache_stats()` 함수로 세션 내 캐시 성능 확인 가능 |
| Open-Meteo 429 rate limit 대응 | 429 응답 감지 로직 추가 |
| 300초 cooldown 추가 | 영구 차단 플래그 대신 5분 cooldown 윈도우 방식으로 자동 복구 가능 |
| API 실패 시 fallback 명시 | static_config로 fallback 시 `api_warnings`에 기록하고 Streamlit에 표시 |
| Excel export 스크립트 추가 | `sandbox/export_physical_risk_feature.py` — Client RE Fund 자산 결과 Excel 출력 |
| Streamlit data_source / warning 표시 | `pages/3_물리적_리스크.py`에 데이터 소스 컬럼 및 API 경고 배너 추가 |

---

## 5. Hazard별 현재 상태

| Hazard | 현재 데이터 소스 | 좌표 기반 여부 | static_config 사용 여부 | API fallback 가능성 | 현재 한계 |
|--------|-----------------|--------------|------------------------|---------------------|----------|
| **flood** | Open-Meteo ERA5 (30년 강수, Gumbel 피팅) | ✅ 자산 좌표 직접 사용 | fallback 시에만 | 429/연결 오류 시 권역 테이블로 fallback | 강수량만 사용. 지형·배수·하천 거리 미반영 |
| **heatwave** | Open-Meteo ERA5 (30년 일최고기온 33°C 초과일) | ✅ 자산 좌표 직접 사용 | fallback 시에만 | 429/연결 오류 시 권역 테이블로 fallback | 도시 열섬 효과 미반영 |
| **drought** | Open-Meteo ERA5 (30년 연속 무강수일) | ✅ 자산 좌표 직접 사용 | fallback 시에만 | 429/연결 오류 시 권역 테이블로 fallback | SPI/SPEI 지수 미적용. 단순 무강수일 기준 |
| **typhoon** | static_config (6개 권역 빈도 테이블) | ❌ 권역 평균 적용 | 항상 사용 | 없음 (Open-Meteo에 경로 데이터 없음) | IBTrACS 연동 미적용. 권역 내 위치 무관 동일값 |
| **sea_level_rise** | static_config (해안/내륙 이진 분류 + IPCC AR6) | ❌ 이진 판단 (경도 임계값) | 항상 사용 | 없음 | SRTM 고도·해안선 거리 미적용. 침수 확률 단순화 |

---

## 6. 결과 변화 요약

아래 수치는 동일 자산·동일 시나리오(`current_policies`, 2030 기준)에서 static_config 대비 ERA5 기반 결과의 변화를 측정한 것이다.

| Hazard | 변화 방향 | 대략적 변화 폭 | 해석 |
|--------|----------|--------------|------|
| **홍수 손실** | ▼ 감소 | 약 40~50% 감소 | 기존 Gumbel 파라미터(권역 평균)가 ERA5 실측 대비 과대 추정되어 있었음 |
| **폭염 손실** | ▼ 감소 | 약 75~85% 감소 | 기존 폭염일수 기준값이 ERA5 30년 실측 대비 크게 과대 추정. 실측 기준 폭염일수가 훨씬 적음 |
| **가뭄 손실** | ▲ 소폭 증가 | 일부 자산 +10~36% 증가 | 기존 무강수일 기준값이 일부 지역에서 ERA5 실측보다 낮게 설정되어 있었음 |

**주의사항**:
- 정확한 수치는 자산 위치, 분석 기간, API 성공 여부에 따라 달라질 수 있음.
- API 실패로 fallback이 발생하면 해당 자산은 static_config 결과가 적용되며, 이 경우 `api_warnings`에 기록됨.
- 결과 변화의 원인은 static_config 권역 평균값과 ERA5 좌표 기반 실측값의 차이이며, 모델 구조 변경은 아님.

---

## 7. 데이터 소스와 경고 표시

### `data_source`가 필요한 이유

GRESB 감사 대응 및 내부 품질 관리를 위해, 각 hazard 결과가 어떤 데이터에서 나왔는지 추적 가능해야 한다. 결과만 있고 소스가 없으면 감사 시 설명이 불가능하다.

### `open_meteo_era5` vs `static_config`

| 값 | 의미 |
|----|------|
| `"open_meteo_era5"` | Open-Meteo Archive API를 통해 ECMWF ERA5 재분석 데이터를 자산 좌표로 직접 조회한 결과 |
| `"static_config"` | `config.py`의 한국 6개 권역 파라미터 테이블에서 가져온 정적 값. 자산 좌표를 직접 사용하지 않음 |

### `api_warnings`가 발생하는 경우

1. **정적 hazard 사용 시**: typhoon, sea_level_rise는 항상 static_config를 사용하며, 이를 사용자에게 알리기 위해 경고 메시지 자동 생성
2. **API 실패 시**: 연결 오류, 타임아웃, 429 등으로 Open-Meteo 호출이 실패하면 해당 자산·hazard 조합에 대해 fallback 경고 기록
3. **429 rate limit 시**: "일시적으로 정적 권역 기반 값 사용 (API rate limit 초과, 5분 후 자동 재시도)" 메시지로 표시

### 429 상태에서 "일시적으로 정적 권역 기반 값 사용"으로 표시하는 이유

영구 비활성화(permanent flag)가 아닌 5분 cooldown 방식을 채택했기 때문에, 429 상태가 일시적임을 사용자에게 명확히 알려야 한다. 재시작 없이 cooldown 후 자동으로 ERA5 계산이 재개된다.

### 캐시된 자산은 429 상태에서도 ERA5 결과 유지

세션 내에 이미 API를 호출해 캐시된 자산은 429 상태가 되어도 캐시 결과를 그대로 반환한다. 따라서 일부 자산은 `"open_meteo_era5"`, 일부는 `"static_config"`가 섞이는 상황이 발생할 수 있으며, 이는 `api_warnings`에 기록된다.

---

## 8. 알려진 한계와 미해결 이슈

| 이슈 | 상태 |
|------|------|
| **typhoon 권역 기반 유지** | IBTrACS(NOAA) 연동 미적용. 동일 권역 내 자산은 위치 무관 동일 빈도 적용 |
| **sea_level_rise 단순화** | NASA SRTM 고도 데이터·해안선 거리 기반 침수 확률 미적용. 해안/내륙 이진 판단만 존재 |
| **flood `business_interruption_cost` 표시 버그** | Streamlit 테이블에서 flood의 BI 비용이 올바르게 표시되지 않는 경우 존재. 확인 필요 |
| **`potential_loss` 정의 불일치** | hazard별 `potential_loss` 계산 방식이 일관되지 않음. flood는 연간 기대손실 기반, heatwave/drought는 단순 비율 적용 방식으로 다름 |
| **BI / revenue-based loss 포함 여부 미확정** | 물리적 리스크 손실 계산에 사업중단손실(BI)을 포함할지 여부는 정책적 재검토 필요 |
| **API 실패 시 자산별 혼재** | 세션 중 429 발생 시점에 따라 일부 자산은 ERA5, 일부는 static_config 결과가 섞일 수 있음. `data_source` 컬럼으로 구분 가능하나 자산 간 비교 시 주의 필요 |
| **캐시 비영속성** | 세션 내 인메모리 캐시만 존재. 앱 재시작 시 캐시 초기화 → 다시 API 호출 필요 |
| **config.py 권역 파라미터 출처 주석 미비** | static_config fallback 용도로 남아있는 권역 파라미터에 출처 인용 주석이 부족함 |

---

## 9. GRESB 대응 관점

### 현재 버전에서 설명 가능한 점

- 홍수·폭염·가뭄 3개 hazard는 자산의 실제 위도·경도를 기반으로 ERA5 기후 데이터를 직접 조회한다.
- 결과에 `data_source` 필드가 포함되어 어떤 데이터를 사용했는지 추적 가능하다.
- API 실패 시 어떤 자산이 정적 값으로 처리되었는지 `api_warnings`를 통해 확인 가능하다.

### 고객사에 말할 때 조심해야 하는 점

- typhoon과 sea_level_rise는 아직 권역 기반 정적 값이며, 자산 좌표를 직접 반영하지 않는다.
- flood 모델은 강수량 데이터만 사용하며 지형·배수체계·하천 거리는 반영되지 않는다.
- API 장애 상황에서는 일부 자산이 자동으로 정적 값으로 처리될 수 있다.

### 표현 가이드

**가능한 표현**:
> "홍수·폭염·가뭄은 ERA5 기반 자산 좌표 분석을 적용했습니다."

> "결과에 데이터 소스를 명시하여 감사 추적이 가능합니다."

**주의할 표현** (사용 금지):
> ~~"모든 hazard가 완전한 좌표 기반 모델입니다."~~ (typhoon·SLR 제외)

> ~~"CLIMADA를 완전히 구현했습니다."~~ (CLIMADA는 참조 프레임워크이며 부분 적용)

> ~~"자산 좌표 기반 분석으로 정확도가 크게 향상되었습니다."~~ (검증은 제한적 범위에서만 수행)

---

## 10. 후속 작업 후보

우선순위 기준으로 정리. 각 항목은 별도 브랜치에서 진행 권장.

| 우선순위 | 작업 | 비고 |
|---------|------|------|
| 1 | **`potential_loss` / BI 정의 통일** | hazard별 계산 방식 일관화. 정책 결정 필요 |
| 2 | **flood BI 표시 버그 수정** | Streamlit 테이블 표시 오류 수정 |
| 3 | **typhoon IBTrACS 기반 좌표 모델 개발** | NOAA IBTrACS 데이터 연동, 자산 반경 내 경로 빈도 계산 |
| 4 | **sea_level_rise SRTM 고도 + 해안거리 기반 개선** | NASA SRTM 30m DEM 기반 침수 취약도 계산 |
| 5 | **API cache persistence 검토** | 디스크 캐시(pickle/parquet) 또는 Redis 연동으로 재시작 시 캐시 유지 |
| 6 | **결과 export 문서화 및 고객사용 설명자료 정리** | Excel export 스크립트 사용법, 결과 해석 가이드 작성 |

---

## 11. 관련 커밋

이 브랜치(main 이후)의 커밋 목록 (최신순):

| 해시 | 날짜 | 커밋 메시지 |
|------|------|------------|
| `9a59b4b` | 2026-06-05 | fix: set Client RE Fund annual_revenue and ebitda to 0; clean up Excel export columns |
| `ef1d45a` | 2026-06-05 | chore: add sandbox debug and validation scripts |
| `f990ae6` | 2026-06-05 | fix: replace permanent rate-limit flag with 5-minute cooldown window |
| `2bd6d61` | 2026-06-04 | feat: add 429 rate-limit handling for Open-Meteo API |
| `6167ffe` | 2026-06-04 | Revert "fix: migrate scatter_mapbox to scatter_map (Plotly 6.x deprecation)" |
| `d798fc5` | 2026-06-04 | fix: migrate scatter_mapbox to scatter_map (Plotly 6.x deprecation) |
| `ab52066` | 2026-06-04 | fix: strip internal hazard keys before DataFrame build in physical risk page |
| `4599b1e` | 2026-06-04 | feat: add Client RE Fund physical risk Excel export script |
| `b33c0c1` | 2026-06-04 | docs: add physical risk asset-level update summary |
| `9ec97b0` | 2026-06-04 | docs: add methodology info box to physical risk page |
| `e77e9df` | 2026-06-04 | docs: add CLAUDE.md with main merge restriction rule |
| `9cdc62d` | 2026-06-04 | feat: restore Client RE Fund facilities and add validation script |
| `bd36bdd` | 2026-06-04 | feat: set use_api_data=True as default in assess_physical_risk() |
| `8438246` | 2026-06-04 | feat: show data_source and api_warnings in physical risk Streamlit page |
| `498483c` | 2026-06-04 | feat: improve cache key and add hit/miss tracking in open_meteo.py |
| `6514b73` | 2026-06-04 | feat: add per-hazard data_source tracking and API fallback warnings |
| `6b86203` | 2026-06-04 | chore: add .gitignore to exclude pycache, outputs, .env, .claude |
