from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from fetchers.market_data import fetch_quote, fetch_top_movers
from processors.calendar_utils import get_previous_business_day
from renderers.html_renderer import render_report, save_report


def fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "데이터 없음"
    return f"{value:,.{digits}f}"


def quote_to_dict(q, digits: int = 2):
    return {
        "name": q.name,
        "symbol": q.symbol,
        "close": fmt(q.close, digits),
        "change_pct": None if q.change_pct is None else round(q.change_pct, digits),
        "volume": fmt(q.volume, digits) if q.volume is not None else "데이터 없음",
    }


def main() -> None:
    config_path = Path("config/markets.yml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    decimals = config["report"].get("decimals", 2)
    tz_name = config["report"].get("timezone", "Asia/Seoul")
    output_dir = config["report"].get("output_dir", "output")

    base_day = get_previous_business_day(tz_name).date()

    kr_indices = [quote_to_dict(fetch_quote(i["name"], i["symbol"], base_day), decimals) for i in config["markets"]["korea_indices"]]
    us_indices = [quote_to_dict(fetch_quote(i["name"], i["symbol"], base_day), decimals) for i in config["markets"]["us_indices"]]

    fx = [quote_to_dict(fetch_quote(i["name"], i["symbol"], base_day), decimals) for i in config["assets"]["fx"]]
    rates = [quote_to_dict(fetch_quote(i["name"], i["symbol"], base_day), decimals) for i in config["assets"]["rates"]]
    commodities = [quote_to_dict(fetch_quote(i["name"], i["symbol"], base_day), decimals) for i in config["assets"]["commodities"]]

    top_n = config["ranking"].get("top_n", 5)
    kr_gainers, kr_losers = fetch_top_movers(config["stocks"]["korea_universe"], base_day, top_n)
    us_gainers, us_losers = fetch_top_movers(config["stocks"]["us_universe"], base_day, top_n)

    context = {
        "report_date": base_day.strftime("%Y-%m-%d"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "kr_indices": kr_indices,
        "us_indices": us_indices,
        "fx": fx,
        "rates": rates,
        "commodities": commodities,
        "kr_gainers": [quote_to_dict(q, decimals) for q in kr_gainers],
        "kr_losers": [quote_to_dict(q, decimals) for q in kr_losers],
        "us_gainers": [quote_to_dict(q, decimals) for q in us_gainers],
        "us_losers": [quote_to_dict(q, decimals) for q in us_losers],
    }

    html = render_report("templates", context)
    dated_name = f"{context['report_date']}.html"

    save_report(html, output_dir, dated_name)
    save_report(html, output_dir, "latest.html")

    print(f"리포트 생성 완료: {output_dir}/{dated_name}")


if __name__ == "__main__":
    main()
