from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import FinanceDataReader as fdr
import pandas as pd


@dataclass
class ValidationResult:
    name: str
    symbol: str
    fdr_close: float | None
    naver_close: float | None
    diff: float | None
    diff_pct: float | None
    passed: bool


def _fetch_fdr_close(symbol: str, target_day: date) -> float | None:
    try:
        start = target_day - timedelta(days=7)
        df = fdr.DataReader(symbol, start.isoformat(), target_day.isoformat())
        if df is None or df.empty:
            return None
        return float(df.iloc[-1]["Close"])
    except Exception:
        return None


def _fetch_naver_close(symbol: str, target_day: date) -> float | None:
    try:
        start = target_day - timedelta(days=7)
        df = fdr.DataReader(symbol, start.isoformat(), target_day.isoformat(), exchange="NAVER")
        if isinstance(df, pd.DataFrame) and not df.empty and "Close" in df.columns:
            return float(df.iloc[-1]["Close"])
        return None
    except Exception:
        return None


def validate_against_naver(name: str, symbol: str, target_day: date, tolerance_pct: float = 0.3) -> ValidationResult:
    fdr_close = _fetch_fdr_close(symbol, target_day)
    naver_close = _fetch_naver_close(symbol, target_day)

    if fdr_close is None or naver_close is None:
        return ValidationResult(name, symbol, fdr_close, naver_close, None, None, False)

    diff = abs(fdr_close - naver_close)
    diff_pct = (diff / naver_close * 100) if naver_close else None
    passed = (diff_pct is not None) and (diff_pct <= tolerance_pct)
    return ValidationResult(name, symbol, fdr_close, naver_close, diff, diff_pct, passed)
