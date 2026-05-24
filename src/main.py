from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

from fetchers.market_data import fetch_quote
from processors.calendar_utils import get_previous_business_day
from renderers.html_renderer import render_report, save_report
from validators.data_validator import validate_against_naver


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="주식 시장 HTML 리포트 생성기")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="국내 지수(KS11/KQ11) 종가를 NAVER 소스와 비교 검증",
    )
    parser.add_argument(
        "--date",
        dest="report_date",
        default=None,
        help="리포트 기준일 (YYYY-MM-DD). 미지정 시 직전 영업일 사용",
    )
    return parser.parse_args()


def resolve_base_day(report_date: str | None, tz_name: str):
    if report_date:
        try:
            return datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValueError("--date 형식은 YYYY-MM-DD 이어야 합니다.") from exc
    return get_previous_business_day(tz_name).date()


def cleanup_old_reports(output_dir: str, max_dated_files: int) -> int:
    if max_dated_files < 1:
        return 0

    out_dir = Path(output_dir)
    if not out_dir.exists():
        return 0

    dated_files = []
    for path in out_dir.glob("*.html"):
        if path.name == "latest.html":
            continue
        try:
            datetime.strptime(path.stem, "%Y-%m-%d")
            dated_files.append(path)
        except ValueError:
            continue

    dated_files.sort(key=lambda p: p.name, reverse=True)
    files_to_delete = dated_files[max_dated_files:]

    for old_file in files_to_delete:
        old_file.unlink(missing_ok=True)

    return len(files_to_delete)


def fmt(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "데이터 없음"
    return f"{value:,.{digits}f}"


def quote_to_dict(q, digits: int = 2, name_ko: str | None = None):
    return {
        "name": q.name,
        "name_ko": name_ko or q.name,
        "symbol": q.symbol,
        "close": fmt(q.close, digits),
        "change_pct": None if q.change_pct is None else round(q.change_pct, digits),
        "volume": fmt(q.volume, digits) if q.volume is not None else "데이터 없음",
    }


def fetch_items(items: list[dict], base_day, decimals: int) -> list[dict]:
    return [
        quote_to_dict(
            fetch_quote(i.get("name", i["symbol"]), i["symbol"], base_day),
            decimals,
            i.get("display_name"),
        )
        for i in items
    ]




def run_validation(config: dict, base_day, tolerance_pct: float):
    results = []
    for item in config["markets"].get("korea_indices", []):
        r = validate_against_naver(item.get("display_name", item["symbol"]), item["symbol"], base_day, tolerance_pct=tolerance_pct)
        results.append(r)

    print("\n[검증] NAVER 대비 종가 검증 결과")
    for r in results:
        if r.diff_pct is None:
            print(f"- {r.name}({r.symbol}): 검증 불가 (데이터 없음)")
        else:
            status = "PASS" if r.passed else "FAIL"
            print(f"- {r.name}({r.symbol}): {status} | FDR={r.fdr_close:,.2f}, NAVER={r.naver_close:,.2f}, diff={r.diff_pct:.4f}%")

def main() -> None:
    args = parse_args()

    config_path = Path("config/markets.yml")
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    decimals = config["report"].get("decimals", 2)
    tz_name = config["report"].get("timezone", "Asia/Seoul")
    output_dir = config["report"].get("output_dir", "output")
    max_dated_files = config["report"].get("max_dated_files", 90)
    validation_tolerance_pct = config["report"].get("validation_tolerance_pct", 0.3)

    base_day = resolve_base_day(args.report_date, tz_name)

    if args.validate:
        run_validation(config, base_day, validation_tolerance_pct)

    context = {
        "report_date": base_day.strftime("%Y-%m-%d"),
        "generated_at": datetime.now(ZoneInfo(tz_name)).strftime("%Y-%m-%d %H:%M:%S"),
        "validation_tolerance_pct": validation_tolerance_pct,
        "kr_indices": fetch_items(config["markets"]["korea_indices"], base_day, decimals),
        "us_indices": fetch_items(config["markets"]["us_indices"], base_day, decimals),
        "asia_indices": fetch_items(config["markets"].get("asia_indices", []), base_day, decimals),
        "fx": fetch_items(config["assets"]["fx"], base_day, decimals),
        "commodities": fetch_items(config["assets"]["commodities"], base_day, decimals),
    }

    html = render_report("templates", context)
    dated_name = f"{context['report_date']}.html"

    save_report(html, output_dir, dated_name)
    save_report(html, output_dir, "latest.html")
    removed_count = cleanup_old_reports(output_dir, max_dated_files)

    print(f"리포트 생성 완료: {output_dir}/{dated_name}")
    print(f"보관 정책: 날짜별 파일 최대 {max_dated_files}개 유지, 이번 실행 삭제 {removed_count}개")


if __name__ == "__main__":
    main()
