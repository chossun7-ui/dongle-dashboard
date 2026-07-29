"""JPY → KRW 환율 조회.

실시간 조회를 우선 시도하고, 실패하면 data/fx_cache.json의 캐시값(조사 시점·출처 명시)을
폴백으로 사용한다. 이 저장소를 만든 세션(2026-07-29)에서는 이 환경의 아웃바운드 네트워크가
방화벽 정책으로 대부분의 외부 도메인에 대해 CONNECT 자체가 차단되어 있어(WebFetch도 전면
403) 실시간 조회를 실행하지 못했다 — 그래서 캐시값은 WebSearch로 확인한 근사치다.
사용자가 이 스크립트를 일반 네트워크 환경에서 실행하면 실시간 조회가 정상 동작한다.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import requests

CACHE_PATH = Path(__file__).parent.parent / "data" / "fx_cache.json"

# 실시간 조회 시도 순서. 두 곳 다 무료·무인증 공개 API.
_LIVE_ENDPOINTS = [
    "https://api.frankfurter.dev/v1/latest?base=JPY&symbols=KRW",
    "https://open.er-api.com/v6/latest/JPY",
]


def _try_live_fetch(timeout: int = 8) -> dict[str, Any] | None:
    for url in _LIVE_ENDPOINTS:
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            rate = None
            if "rates" in data and "KRW" in data["rates"]:
                rate = data["rates"]["KRW"]
            if rate:
                return {"jpy_to_krw": rate, "source": url, "live": True}
        except requests.RequestException:
            continue
    return None


def get_jpy_to_krw_rate() -> dict[str, Any]:
    """{"jpy_to_krw": float, "source": str, "live": bool, "fetched_at": str} 반환."""
    live = _try_live_fetch()
    if live:
        return live

    with open(CACHE_PATH, encoding="utf-8") as f:
        cache = json.load(f)
    cache["live"] = False
    return cache


def jpy_to_krw(amount_jpy: float | None, rate_info: dict[str, Any]) -> float | None:
    if amount_jpy is None:
        return None
    return round(amount_jpy * rate_info["jpy_to_krw"])
