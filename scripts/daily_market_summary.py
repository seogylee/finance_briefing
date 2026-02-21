from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import FinanceDataReader as fdr
import pandas as pd

KST = ZoneInfo("Asia/Seoul")
OUTPUT_DIR = Path("reports")


@dataclass
class MarketItem:
    section: str
    label: str
    symbols: list[str]


MARKET_ITEMS: list[MarketItem] = [
    MarketItem("국내", "코스피", ["KS11"]),
    MarketItem("국내", "코스닥", ["KQ11"]),
    MarketItem("해외", "다우 산업", ["^DJI", "DJI"]),
    MarketItem("해외", "나스닥 종합", ["^IXIC", "IXIC"]),
    MarketItem("해외", "상해 종합", ["000001.SS", "SSEC"]),
    MarketItem("해외", "니케이225", ["^N225", "N225"]),
    MarketItem("환율", "원/달러", ["USD/KRW", "KRW=X"]),
    MarketItem("환율", "중국 위안/달러", ["CNY/USD", "CNY=X"]),
    MarketItem("상품", "금", ["GC=F", "XAU/USD"]),
    MarketItem("상품", "은", ["SI=F", "XAG/USD"]),
    MarketItem("상품", "WTI", ["CL=F", "WTI"]),
]


@dataclass
class MarketResult:
    section: str
    label: str
    close: float | None
    change_pct: float | None



def fetch_last_two_closes(symbol: str, days: int = 14) -> pd.Series:
    end = datetime.now(KST).date()
    start = end - timedelta(days=days)
    df = fdr.DataReader(symbol, start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
    if df.empty:
        raise ValueError("no rows returned")
    closes = df["Close"].dropna()
    if len(closes) < 2:
        raise ValueError("not enough close points")
    return closes.tail(2)



def collect() -> list[MarketResult]:
    results: list[MarketResult] = []
    for item in MARKET_ITEMS:
        close_value: float | None = None
        change_pct: float | None = None

        for symbol in item.symbols:
            try:
                closes = fetch_last_two_closes(symbol)
                prev_close, close = closes.iloc[0], closes.iloc[1]
                close_value = float(close)
                change_pct = float((close - prev_close) / prev_close * 100)
                break
            except Exception:
                continue

        results.append(
            MarketResult(
                section=item.section,
                label=item.label,
                close=close_value,
                change_pct=change_pct,
            )
        )
    return results



def format_value(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:,.2f}"



def trend_class(change_pct: float | None) -> str:
    if change_pct is None:
        return "flat"
    if change_pct > 0:
        return "up"
    if change_pct < 0:
        return "down"
    return "flat"



def trend_text(change_pct: float | None) -> str:
    if change_pct is None:
        return "-"
    if change_pct > 0:
        return f"▲ {abs(change_pct):.2f}%"
    if change_pct < 0:
        return f"▼ {abs(change_pct):.2f}%"
    return "- 0.00%"



def render_html(results: list[MarketResult], report_date: datetime) -> str:
    grouped: dict[str, list[MarketResult]] = {}
    for r in results:
        grouped.setdefault(r.section, []).append(r)

    sections = []
    for section_name in ["국내", "해외", "환율", "상품"]:
        rows = grouped.get(section_name, [])
        section_rows = "\n".join(
            f"""
            <tr>
              <td class=\"label\">{row.label}</td>
              <td class=\"value {trend_class(row.change_pct)}\">{format_value(row.close)} {trend_text(row.change_pct)}</td>
            </tr>
            """.strip()
            for row in rows
        )
        sections.append(
            f"""
            <section>
              <h2>{section_name}</h2>
              <table>
                <tbody>
                  {section_rows}
                </tbody>
              </table>
            </section>
            """.strip()
        )

    sections_html = "\n".join(sections)

    return f"""<!doctype html>
<html lang=\"ko\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>전일 시장 요약</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 20px; color: #333; max-width: 720px; }}
    h1 {{ margin-bottom: 4px; }}
    .date {{ color: #666; font-size: 14px; margin-bottom: 18px; }}
    h2 {{ margin-top: 20px; margin-bottom: 8px; border-bottom: 2px solid #d9d9d9; padding-bottom: 6px; }}
    table {{ width: 100%; border-collapse: collapse; background: #fff; }}
    td {{ border: 1px solid #e3e3e3; padding: 10px 12px; }}
    td.label {{ width: 42%; font-weight: 700; background: #f7f7f7; }}
    td.value {{ font-weight: 700; text-align: right; }}
    .up {{ color: #d5534a; }}
    .down {{ color: #4a89b6; }}
    .flat {{ color: #666; }}
  </style>
</head>
<body>
  <h1>전일 시장 요약</h1>
  <div class=\"date\">생성 시각: {report_date.strftime('%Y-%m-%d %H:%M:%S %Z')}</div>
  {sections_html}
</body>
</html>
"""



def main() -> None:
    now = datetime.now(KST)
    results = collect()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"market_summary_{now.strftime('%Y%m%d')}.html"
    out_path.write_text(render_html(results, now), encoding="utf-8")
    print(f"Saved report: {out_path}")


if __name__ == "__main__":
    main()
