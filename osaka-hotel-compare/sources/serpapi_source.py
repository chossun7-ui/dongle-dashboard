"""SerpAPI Google Hotels 연동 (3순위, 교차 검증용, 유료).

공식 문서: https://serpapi.com/google-hotels-api
확인된 파라미터(WebSearch 검색결과 기준): q(검색어/호텔명), check_in_date,
check_out_date(YYYY-MM-DD), adults, currency, api_key, engine=google_hotels.
"""
from __future__ import annotations

import os
from typing import Any

import requests

ENDPOINT = "https://serpapi.com/search"


def is_configured() -> bool:
    return bool(os.environ.get("SERPAPI_KEY"))


def search_hotel(query: str, checkin: str, checkout: str, adults: int,
                  currency: str = "JPY", timeout: int = 20) -> dict[str, Any] | None:
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        return None

    resp = requests.get(
        ENDPOINT,
        params={
            "engine": "google_hotels",
            "q": query,
            "check_in_date": checkin,
            "check_out_date": checkout,
            "adults": adults,
            "currency": currency,
            "gl": "jp",
            "hl": "ko",
            "api_key": api_key,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()
