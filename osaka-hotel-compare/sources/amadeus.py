"""Amadeus Self-Service Hotel Search API v3 연동 (OAuth2 client-credentials).

⚠️ 이 세션에서도 developers.amadeus.com 공식 문서를 WebFetch로 직접 열람하지
못했다(전면 403 장애). 아래는 WebSearch 스니펫 기준으로 알려진 공개 정보:
  - v3 엔드포인트: GET /v3/shopping/hotel-offers (호텔의 Amadeus 고유 ID로 조회)
  - 인증: POST /v1/security/oauth2/token (client_credentials 그랜트)
  - 테스트 환경 base URL: https://test.api.amadeus.com
    운영 환경 base URL: https://api.amadeus.com
  - 파라미터: hotelIds, checkInDate, checkOutDate, adults, roomQuantity, currency

호텔명 → Amadeus hotelId 매핑은 /v1/reference-data/locations/hotels/by-city 등
별도 엔드포인트가 필요하며 아직 구현하지 않았다. 실사용 전 공식 문서로 재검증할 것.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

TEST_BASE = "https://test.api.amadeus.com"
PROD_BASE = "https://api.amadeus.com"

_token_cache: dict[str, Any] = {}


def is_configured() -> bool:
    return bool(os.environ.get("AMADEUS_CLIENT_ID") and os.environ.get("AMADEUS_CLIENT_SECRET"))


def _base_url() -> str:
    use_prod = os.environ.get("AMADEUS_USE_PRODUCTION", "false").lower() == "true"
    return PROD_BASE if use_prod else TEST_BASE


def _get_token(timeout: int = 15) -> str | None:
    now = time.time()
    if _token_cache.get("expires_at", 0) > now:
        return _token_cache["access_token"]

    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    resp = requests.post(
        f"{_base_url()}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = now + data.get("expires_in", 1800) - 30
    return _token_cache["access_token"]


def search_hotel_offers(hotel_ids: list[str], checkin: str, checkout: str,
                         adults: int, room_quantity: int = 1,
                         currency: str = "JPY", timeout: int = 15) -> dict[str, Any] | None:
    token = _get_token(timeout=timeout)
    if not token:
        return None

    resp = requests.get(
        f"{_base_url()}/v3/shopping/hotel-offers",
        headers={"Authorization": f"Bearer {token}"},
        params={
            "hotelIds": ",".join(hotel_ids),
            "checkInDate": checkin,
            "checkOutDate": checkout,
            "adults": adults,
            "roomQuantity": room_quantity,
            "currency": currency,
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()
