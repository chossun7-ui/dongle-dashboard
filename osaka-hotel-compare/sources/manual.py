"""수동 조사 데이터(data/manual_research.json) 로더.

API 키가 없을 때(또는 API가 실패했을 때) 폴백으로 사용한다. 조사 시점의
checkin/checkout/adults 조건이 이번 실행 조건과 정확히 일치하지 않으면
사용하지 않는다 — 다른 날짜에 대한 가격을 오늘 조건인 것처럼 잘못 보여주는
것을 막기 위함이다.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_PATH = Path(__file__).parent.parent / "data" / "manual_research.json"


def load_all() -> list[dict[str, Any]]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def matches_conditions(entry: dict[str, Any], checkin: str, checkout: str, adults: int) -> bool:
    cond = entry.get("researched_for", {})
    return (
        cond.get("checkin") == checkin
        and cond.get("checkout") == checkout
        and cond.get("adults") == adults
    )
