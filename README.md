# StockReportGenerator

FinanceDataReader를 사용해 **직전 영업일 기준** 국내/해외 시장 데이터를 수집하고, 첨부 예시 스타일의 한국어 HTML 리포트를 생성하는 자동화 프로젝트입니다.

## 기능
- 국내: 코스피, 코스닥
- 미국: 다우 산업, 나스닥 종합, S&P 500
- 해외(아시아): 상해 종합, 니케이225
- 환율: 원/달러, 위안/원
- 상품: 금, 은, WTI
- 한국어 숫자 포맷(소수점 2자리)
- 상승/하락 색상 및 ▲/▼ 표시
- `output/latest.html` 및 날짜별 HTML 파일 저장
- GitHub Actions 평일 오전 9시(KST) 자동 실행

## 설치
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행
```bash
python src/main.py
# 특정 날짜 기준 리포트 생성
python src/main.py --date 2026-05-20
```

실행 완료 시 아래 파일이 생성됩니다.
- `output/YYYY-MM-DD.html`
- `output/latest.html`

또한 오래된 날짜 파일은 `report.max_dated_files` 값을 초과하면 자동 삭제됩니다(`latest.html` 제외).

## 설정
`config/markets.yml`에서 수집 대상을 조정할 수 있습니다.
- 지수/환율/상품 심볼
- 표기명(`display_name`)
- 소수점 자리수
- output 보관 개수(`report.max_dated_files`, 기본 90개)

## 자동화
`.github/workflows/daily-report.yml`은 아래처럼 동작합니다.
- **테스트 환경(test)**: `push`, `pull_request`, 수동 실행(`workflow_dispatch` + `environment=test`) 시 리포트 생성/검증만 수행
- **운영 환경(production)**: 평일 09:00 KST 스케줄 또는 수동 실행(`workflow_dispatch` + `environment=prod`) 시 리포트 생성 후 `output/` 자동 커밋
- **날짜 지정 실행**: Run workflow에서 `report_date`(YYYY-MM-DD)를 입력하면 해당 날짜 기준으로 리포트 생성/커밋 가능
- **에러 전달**: 실패 시 `failure-logs-<job>-<run_id>` 아티팩트(install/report/verify/commit 로그 + `failure-report.md`)가 생성되며, 이 파일을 Codex에 전달해 원인 분석 가능
- **권한 설정(중요)**: 보안을 위해 `test-report`는 read-only 토큰을 사용하고, `prod-report`만 write 토큰을 사용합니다. 자동 커밋/푸시를 위해 저장소 `Settings > Actions > General > Workflow permissions`를 **Read and write permissions**로 설정해야 합니다.

## 주의사항
- 공휴일 판정은 기본적으로 주말만 제외하도록 구현되어 있습니다.
- 일부 심볼은 데이터 공급 상황에 따라 값이 없을 수 있습니다.
