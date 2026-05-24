# StockReportGenerator

FinanceDataReader를 사용해 **직전 영업일 기준** 국내/미국 시장 데이터를 수집하고, 한국어 HTML 리포트를 생성하는 자동화 프로젝트입니다.

## 기능
- 국내/미국 지수 종가 및 등락률
- 거래량 표시
- 환율, 금리, 원자재(금/유가)
- 국내/미국 주요 종목 Top 상승/하락
- 한국어 숫자 포맷(소수점 2자리)
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
```

실행 완료 시 아래 파일이 생성됩니다.
- `output/YYYY-MM-DD.html`
- `output/latest.html`

## 설정
`config/markets.yml`에서 수집 대상을 조정할 수 있습니다.
- 지수/환율/금리/원자재 심볼
- 주요 종목 유니버스
- Top N 개수

## 자동화
`.github/workflows/daily-report.yml`이 평일 09:00 KST(=UTC 00:00)에 실행됩니다.

## 주의사항
- 공휴일 판정은 기본적으로 주말만 제외하도록 구현되어 있습니다.
- 일부 심볼은 데이터 공급 상황에 따라 값이 없을 수 있습니다.
