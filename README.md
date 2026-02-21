# finance_briefing

FinanceDataReader를 사용해 전일 시장 요약 HTML을 생성하고, GitHub Actions 스케줄로 매일 오전 8시(KST)에 자동 실행합니다.

## 구성
- `scripts/daily_market_summary.py`: 시장 데이터 수집 + HTML 생성
- `.github/workflows/daily-market-summary.yml`: 매일 08:00 KST 자동 실행, 결과 커밋/푸시
- `reports/`: 생성된 HTML 저장 경로

## 로컬 실행
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/daily_market_summary.py
```

실행 후 `reports/market_summary_YYYYMMDD.html` 파일이 생성됩니다.

## 스케줄
GitHub Actions cron은 UTC 기준이므로, 08:00 KST 실행을 위해 `0 23 * * *`를 사용했습니다.
