from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import FinanceDataReader as fdr
import pandas as pd


@dataclass
class Quote:
    name: str
    symbol: str
    close: float | None
    change_pct: float | None
    volume: float | None = None


def _fetch_two_days(symbol: str, target_day: date) -> pd.DataFrame:
    start = target_day - timedelta(days=7)
    df = fdr.DataReader(symbol, start.isoformat(), target_day.isoformat())
    if df is None or df.empty:
        return pd.DataFrame()
    return df.tail(2)


def fetch_quote(name: str, symbol: str, target_day: date) -> Quote:
    try:
        df = _fetch_two_days(symbol, target_day)
        if len(df) < 2:
            return Quote(name, symbol, None, None, None)

        prev_close = float(df.iloc[-2]["Close"])
        latest_close = float(df.iloc[-1]["Close"])
        volume = float(df.iloc[-1].get("Volume", 0.0))
        change_pct = ((latest_close - prev_close) / prev_close) * 100 if prev_close else 0.0
        return Quote(name, symbol, latest_close, change_pct, volume)
    except Exception:
        return Quote(name, symbol, None, None, None)


def fetch_top_movers(symbols: list[str], target_day: date, top_n: int = 5) -> tuple[list[Quote], list[Quote]]:
    rows: list[Quote] = []
    for sym in symbols:
        q = fetch_quote(sym, sym, target_day)
        if q.change_pct is not None:
            rows.append(q)

    gainers = sorted(rows, key=lambda x: x.change_pct if x.change_pct is not None else -999, reverse=True)[:top_n]
    losers = sorted(rows, key=lambda x: x.change_pct if x.change_pct is not None else 999)[:top_n]
    return gainers, losers
