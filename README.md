# StockReportGenerator

FinanceDataReader를 사용해 **직전 영업일 기준** 국내/해외 시장 데이터를 수집하고, 한국어 HTML 리포트를 자동 생성하는 프로젝트입니다.

---

## 1) 프로젝트 개요

이 프로젝트는 아래 흐름으로 동작합니다.

1. 기준일 계산(기본: 직전 영업일, 옵션: 특정 날짜 지정)
2. 지수/환율/상품 데이터 조회
3. HTML 템플릿 렌더링
4. `output/`에 날짜 파일 + `latest.html` 저장
5. 오래된 리포트 자동 정리(보관 개수 초과분 삭제)

---

## 2) 디렉토리 구조와 파일 역할

```text
StockReportGenerator/
├─ .github/                # CI/CD 및 자동화 설정
│  └─ workflows/
│     └─ daily-report.yml  # 일일 리포트 GitHub Actions 워크플로우
├─ config/                 # 데이터 대상/출력 정책 설정
│  └─ markets.yml          # 시장 심볼, 표시명, 타임존, 보관 개수 설정
├─ src/                    # 애플리케이션 소스 코드
│  ├─ main.py              # 실행 진입점(오케스트레이션)
│  ├─ fetchers/            # 외부 데이터 조회 계층
│  │  └─ market_data.py
│  ├─ processors/          # 날짜/가공 로직 계층
│  │  └─ calendar_utils.py
│  └─ renderers/           # HTML 렌더링/저장 계층
│     └─ html_renderer.py
├─ templates/              # Jinja2 템플릿 파일
│  ├─ report.html.j2       # 리포트 전체 레이아웃
│  └─ value_cell.j2        # 값 셀(가격/등락률) 부분 템플릿
├─ output/                 # 생성된 리포트 산출물(실행 시 생성)
├─ requirements.txt        # Python 의존성 목록
├─ .gitignore              # Git 추적 제외 규칙
└─ README.md               # 프로젝트 문서
```

### `.github/workflows/daily-report.yml`
- GitHub Actions 자동화 워크플로우입니다.
- `test-report`와 `prod-report`를 분리해 테스트/운영 실행을 구분합니다.
- 실패 시 로그 아티팩트를 업로드합니다.

### `config/markets.yml`
- 리포트 설정의 중심 파일입니다.
- 타임존, 소수점, 출력 폴더, 보관 개수(`max_dated_files`)를 관리합니다.
- 대상 지수/환율/상품 심볼과 화면 표시명(`display_name`)을 정의합니다.

### `src/main.py`
- 프로그램 진입점(오케스트레이터)입니다.
- 주요 역할:
  - `--date` 인자 파싱
  - YAML 로드
  - 기준일 계산
  - 데이터 수집 함수 호출
  - 템플릿 렌더링 및 파일 저장
  - 오래된 output 파일 정리

### `src/fetchers/market_data.py`
- 시장 데이터를 조회/가공하는 계층입니다.
- 주요 역할:
  - 심볼의 최근 2개 거래일 종가 조회
  - 등락률 계산
  - `Quote` 데이터 구조로 정리
  - `CNY/KRW` 조회 실패 시 `USD/KRW`와 `USD/CNY`를 이용한 fallback 계산 시도

### `src/processors/calendar_utils.py`
- 날짜 계산 유틸리티입니다.
- 현재는 주말을 제외해 직전 영업일을 계산합니다.

### `src/renderers/html_renderer.py`
- Jinja2 템플릿 렌더링 담당입니다.
- HTML 문자열 생성과 파일 저장을 분리해 제공합니다.

### `templates/report.html.j2`
- 전체 리포트 레이아웃 템플릿입니다.
- 섹션(국내/미국/해외(아시아)/환율/상품)과 스타일이 정의되어 있습니다.

### `templates/value_cell.j2`
- 값 셀(가격/등락률/화살표/색상) 부분 템플릿입니다.
- 각 섹션의 수치 셀을 동일한 표현으로 렌더링합니다.

### `requirements.txt`
- 런타임 의존성 목록입니다.
  - `finance-datareader`
  - `Jinja2`
  - `pandas`
  - `PyYAML`

### `.gitignore`
- 파이썬 캐시 파일을 제외합니다.

---

## 3) 설정 파일(`config/markets.yml`) 상세

`report` 섹션:
- `timezone`: 기준 타임존 (기본 `Asia/Seoul`)
- `decimals`: 숫자 소수점 자리수
- `output_dir`: 리포트 저장 경로
- `max_dated_files`: 날짜형 리포트 최대 보관 개수 (`latest.html` 제외)

`markets` / `assets` 섹션:
- 실제 조회 심볼(`symbol`)과 UI 표시명(`display_name`)을 분리해 관리합니다.

---

## 4) 로컬 실행 방법

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행
```bash
# 직전 영업일 기준 생성
python src/main.py

# 특정 날짜 기준 생성
python src/main.py --date 2026-05-20
```

실행 결과:
- `output/YYYY-MM-DD.html`
- `output/latest.html`

보관 정책:
- 날짜형 파일이 `report.max_dated_files`를 초과하면 오래된 파일 자동 삭제
- `latest.html`은 삭제 대상 제외

---

## 5) GitHub Actions 동작

`daily-report.yml`은 아래 트리거를 사용합니다.

- `pull_request`, `push`: 테스트 실행
- `schedule`(평일 09:00 KST = UTC 00:00): 운영 실행
- `workflow_dispatch`: 수동 실행

### test-report
- 목적: 검증 전용
- 권한: `contents: read`
- 작업: 의존성 설치 → 리포트 생성 → `output/latest.html` 확인
- 실패 시: 로그 아티팩트 업로드

### prod-report
- 목적: 운영 반영
- 권한: `contents: write`
- 작업: 리포트 생성 후 `output/` 변경 사항 자동 커밋/푸시
- 수동 실행 시 `environment=prod`와 `report_date` 입력 지원

### 실패 로그 전달
- 실패 시 `failure-logs-<job>-<run_id>` 아티팩트가 생성됩니다.
- 포함 파일: `install.log`, `report.log`, `verify.log`/`commit.log`, `failure-report.md`

---

## 6) 자주 발생하는 이슈

### Q1. `output/` 폴더가 안 보입니다.
- 실행 전에는 없을 수 있습니다.
- `python src/main.py` 실행 시 자동 생성됩니다.

### Q2. 환율이 `데이터 없음`으로 나옵니다.
- 데이터 소스 응답 실패/지연 시 발생할 수 있습니다.
- `CNY/KRW`는 fallback 계산을 시도하지만, 기초 시리즈도 실패하면 빈값이 됩니다.

### Q3. GitHub Actions에서 push가 403 납니다.
- 저장소 설정에서 `Settings > Actions > General > Workflow permissions`를
  **Read and write permissions**로 설정해야 합니다.

---

## 7) 향후 개선 아이디어

- 공휴일 캘린더 반영(현재는 주말만 제외)
- 데이터 소스 다중화(백업 소스)
- 섹션별 단위/통화 표기 강화
- 간단한 단위 테스트 추가
