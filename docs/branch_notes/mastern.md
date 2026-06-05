# 브랜치 노트: Mastern

## 브랜치 생성 배경

`main` 브랜치에서 직접 분기. 기존 `sample_facilities.py`에는 K-Steel Corp, K-Petrochem 등 가상의 한국 산업 시설 데이터가 다수 포함되어 있었으나, 실제 고객사(Client RE Fund)에 시현하기 위해 고객사 자산만 남기고 공통 사이드바를 적용하는 작업을 위해 생성되었다.

---

## 이 브랜치에서 해결하려던 문제

1. 기존 sample_facilities.py에 고객사와 무관한 가상 데이터가 다수 포함되어 있어 시현에 부적합
2. Streamlit 앱에서 페이지 이동 시 회사 선택이 초기화되는 문제 (사이드바가 app.py에만 있었음)
3. 고객사 자산의 위도/경도를 구글 맵 등에서 직접 확인할 수 있는 보조 스크립트 필요

---

## 주요 변경사항

### 1. Client RE Fund 자산 추가 (`5a07f23`)
- 기존 FACILITIES 리스트 전체 제거
- Client RE Fund 소속 2개 시설로 대체:
  - **Concordian** (서울 종로구, KR-RE-001)
  - **Logisco Siheung** (경기 시흥시, KR-RE-002)
- 초기 설정값: `annual_revenue=1,000,000,000`, `ebitda=200,000,000`
- 이후 `feature/asset-level-physical-risk`와 병합 시 `annual_revenue=0`, `ebitda=0`으로 변경됨 (고의적 설정 — 아래 참조)

### 2. 공통 사이드바 컴포넌트 추가 (`5a07f23`)
- `streamlit_app/components/sidebar.py` 신규 생성
- `render_global_sidebar()` 함수: 기업 선택, NGFS 시나리오, 탄소가격 체계, 평가 연도를 `st.session_state`에 전역 저장
- 모든 Streamlit 페이지(2~7번)에 `render_global_sidebar()` 호출 추가

### 3. 위도/경도 조회 스크립트 추가 (`5a07f23`)
- `sandbox/geocode.py`: 주소 → 좌표 변환 보조 스크립트

### 4. 프로젝트 정리 (`24f643b`)
- `.gitignore` 추가 (`__pycache__/`, `outputs/`, `.env`, `.claude/` 제외)
- `CLAUDE.md` 추가 (프로젝트 컨벤션)
- `sandbox/export_excel.py`, `sandbox/test_api_vs_static.py` 추가
- 기존 추적 중이던 `.pyc` 파일 전체 제거

---

## 변경된 주요 파일

| 파일 | 변경 내용 |
|---|---|
| `backend/app/data/sample_facilities.py` | 전체 재작성 — Client RE Fund 2개 자산만 보유 |
| `streamlit_app/components/sidebar.py` | 신규 생성 |
| `streamlit_app/components/__init__.py` | 신규 생성 |
| `streamlit_app/app.py` | 사이드바 로직 `render_global_sidebar()`로 위임 |
| `streamlit_app/pages/2_전환_리스크.py` ~ `7_종합_대시보드.py` | `render_global_sidebar()` 호출 추가 |
| `sandbox/geocode.py` | 신규 생성 |
| `sandbox/export_excel.py` | 신규 생성 |
| `sandbox/test_api_vs_static.py` | 신규 생성 |

---

## 모델/데이터 측면에서 달라진 점

- 분석 대상 자산이 가상 한국 산업 시설 전체 → Client RE Fund 2개 자산으로 교체됨
- 모델 계산 로직 자체는 변경 없음 (이 브랜치에서는 물리적/전환 리스크 모델 수정 없음)

---

## UI/Streamlit 측면에서 달라진 점

- 사이드바가 `app.py`에만 있던 구조 → 모든 페이지에서 `render_global_sidebar()` 호출
- 페이지 이동 시 기업/시나리오/연도 선택값이 유지됨 (`st.session_state` 공유)
- 사이드바 기업 목록이 `sample_facilities.py`의 `get_company_list()`에서 동적으로 로딩됨

---

## 고객사 또는 분석 결과에 미치는 영향

- Client RE Fund 자산만 분석 대상으로 표시됨
- `annual_revenue=0`, `ebitda=0` 설정으로 인해 영업중단(Business Interruption) 손실이 0으로 계산됨 → 자산 기반 직접 손상(direct damage)만 EAL에 반영
- 고객사에 발송하는 Excel 결과물이 이 자산 기준으로 생성됨

---

## 의도적으로 남겨둔 한계

- `annual_revenue=0`, `ebitda=0`은 고객사 재무정보 비공개를 위한 의도적 설정이지만, 이로 인해 heatwave/drought의 BI 손실이 전부 0으로 계산됨
- sector가 `real_estate`로 통일되어 있어 업종 특성 반영이 제한적

---

## 후속 작업 후보

- [ ] 실제 revenue/EBITDA 데이터를 별도 환경변수나 `.env`로 관리하는 구조 검토
- [ ] 자산별 sector 세분화 (오피스, 물류센터 등 real estate 하위 분류)
- [ ] `geocode.py`를 활용한 추가 자산 좌표 확인

---

## 관련 커밋 목록

| 커밋 해시 | 날짜 | 내용 |
|---|---|---|
| `5a07f23` | 2026-06-03 | feat: add Client RE Fund assets and global sidebar component |
| `24f643b` | 2026-06-04 | chore: add .gitignore, CLAUDE.md, sandbox scripts; remove tracked pycache |
| `6f84251` | 2026-06-05 | feat: merge feature/asset-level-physical-risk into Mastern |

> 현재 Mastern은 `feature/asset-level-physical-risk`와 병합된 통합 브랜치 상태임.
> 위 2개 커밋이 Mastern 고유 작업이며, 이후 feature 브랜치의 16개 커밋이 머지됨.
