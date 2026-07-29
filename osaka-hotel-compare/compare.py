#!/usr/bin/env python3
"""오사카 숙소 자동 비교 CLI 진입점.

사용법:
    python compare.py --checkin 2026-10-08 --checkout 2026-10-12 --adults 3

동작:
    1. data/candidates.json의 각 후보 숙소에 대해, 설정된 API 키 우선순위
       (라쿠텐 → Amadeus → SerpAPI) 순으로 실시간 조회를 시도한다.
    2. 키가 없거나 조회에 실패하면 data/manual_research.json의 수동 조사값을
       폴백으로 쓴다 (단, 조사 시점의 조건이 이번 실행 조건과 정확히 일치할 때만).
    3. 결과를 4박 총액 오름차순으로 정렬해 results.md / results.csv / checklist.md로 출력한다.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from config import parse_args
from lib import aggregate, output
from sources import amadeus, manual, rakuten, serpapi_source


def resolve_entry(candidate: dict[str, Any], manual_entries: list[dict[str, Any]],
                   checkin: str, checkout: str, adults: int) -> dict[str, Any]:
    """실시간 API를 우선 시도하고, 실패하면 조건이 일치하는 수동 조사값을 쓴다."""
    name = candidate["hotel_name"]

    # 1순위: 라쿠텐. hotel_no가 candidates.json에 채워져 있어야 실제 조회가 된다
    # (지금은 hotel_no 매핑이 비어 있어 항상 스킵됨 — README/rakuten.py 참고).
    if rakuten.is_configured() and candidate.get("rakuten_hotel_no"):
        try:
            payload = rakuten.search_hotel(candidate["rakuten_hotel_no"], checkin, checkout, adults)
            parsed = rakuten.parse_response(payload) if payload else None
            if parsed and parsed.get("min_charge_jpy"):
                nights = _nights(checkin, checkout)
                return {
                    "hotel_name": name, "area": candidate["area"], "is_seed": candidate["is_seed"],
                    "room_config": "라쿠텐 API 실시간 조회",
                    "nightly_rates_jpy": {}, "total_4nights_jpy": parsed["min_charge_jpy"] * nights,
                    "source_url": "https://travel.rakuten.co.jp/", "data_source": "라쿠텐 트래블 API (실시간)",
                    "notes": "", "price_found": True, "failure_reason": "",
                }
        except Exception as e:  # noqa: BLE001 — 원격 API 실패는 폴백으로 흡수
            print(f"[경고] 라쿠텐 API 조회 실패({name}): {e}", file=sys.stderr)

    # 수동 조사 폴백: 이번 실행 조건과 정확히 일치하는 항목만 채택.
    for entry in manual_entries:
        if entry["hotel_name"] == name and manual.matches_conditions(entry, checkin, checkout, adults):
            return entry

    return {
        "hotel_name": name, "area": candidate["area"], "is_seed": candidate["is_seed"],
        "room_config": "N/A", "nightly_rates_jpy": {}, "total_4nights_jpy": None,
        "source_url": "", "data_source": "", "notes": "",
        "price_found": False,
        "failure_reason": "API 키 미설정 + 이번 실행 조건(날짜/인원)에 맞는 수동 조사 데이터 없음",
    }


def _nights(checkin: str, checkout: str) -> int:
    from datetime import datetime
    return (datetime.strptime(checkout, "%Y-%m-%d") - datetime.strptime(checkin, "%Y-%m-%d")).days


def main() -> None:
    load_dotenv()
    cfg = parse_args()

    import json
    with open(Path(__file__).parent / "data" / "candidates.json", encoding="utf-8") as f:
        candidates = json.load(f)
    manual_entries = manual.load_all()

    checkin_s, checkout_s = str(cfg.checkin), str(cfg.checkout)

    active_sources = [
        name for name, configured in [
            ("라쿠텐 트래블", rakuten.is_configured()),
            ("Amadeus", amadeus.is_configured()),
            ("SerpAPI", serpapi_source.is_configured()),
        ] if configured
    ]
    if active_sources:
        print(f"[정보] 활성화된 실시간 API: {', '.join(active_sources)}")
    else:
        print("[정보] 설정된 API 키가 없습니다 — 수동 조사 데이터(data/manual_research.json)만 사용합니다.")

    entries = [resolve_entry(c, manual_entries, checkin_s, checkout_s, cfg.adults) for c in candidates]
    rows, rate_info = aggregate.build_comparison_rows(entries, cfg.adults, cfg.nights, cfg.rooms_preferred)

    out_dir = Path(cfg.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    md = output.write_results_md(rows, cfg, rate_info)
    (out_dir / "results.md").write_text(md, encoding="utf-8")
    output.write_results_csv(rows, out_dir / "results.csv")
    output.write_checklist_md(rows, out_dir / "checklist.md")

    priced_count = sum(1 for r in rows if r["resolved_total_jpy"] is not None)
    print(f"[완료] {len(rows)}곳 중 {priced_count}곳 가격 확인됨. "
          f"results.md / results.csv / checklist.md 생성됨 → {out_dir.resolve()}")


if __name__ == "__main__":
    main()
