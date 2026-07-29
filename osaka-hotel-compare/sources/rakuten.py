"""라쿠텐 트래블 공실검색 API(VacantHotelSearch) 연동.

⚠️ 문서 확인 상태(2026-07-29 작성 시점):
이 세션의 WebFetch 도구가 전면 장애(모든 URL 403)였기 때문에 공식 문서
(https://webservice.rakuten.co.jp/documentation/vacant-hotel-search)를 직접 열람하지
못했다. 아래 엔드포인트·파라미터명은 WebSearch 스니펫과 서드파티 기술 블로그 인용을
근거로 작성한 것으로, **실제 사용 전 공식 문서로 반드시 재검증**해야 한다
(CLAUDE.md 규칙에서도 "기억이나 추측으로 작성하지 말 것"을 요구함 — 이 파일은
그 원칙을 완전히 지키지 못했으므로 이 경고를 남긴다).

확인된 것(WebSearch 검색결과 스니펫 근거):
  - 엔드포인트: https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426
  - applicationId: 필수, 발급받은 Application ID
  - format=json

미확인/추정(서드파티 블로그 인용, 공식 문서 미대조):
  - checkinDate / checkoutDate: YYYY-MM-DD
  - adultNum: 성인 인원수
  - roomNum: 객실 수(1실 검색이면 1, adultNum은 "총 인원"이 아니라 "1실당 인원"일
    가능성이 있음 — 반드시 공식 문서에서 room당 vs 총원 여부를 확인할 것)
  - largeClassCode/middleClassCode/smallClassCode/detailClassCode: 지역 코드 체계
    (일본 전국 지역 코드표 별도 조회 필요 — 오사카/니시쿠조/난바/니시나리 코드 미확정)
  - hotelNo: 특정 시설 번호로 직접 조회 시 사용
  - 응답 필드: hotels[].hotel[].hotelBasicInfo.hotelMinCharge, .hotelName /
    hotels[].hotel[].roomInfo[].dailyCharge.total 등으로 추정(공식 스키마 미대조)
"""
from __future__ import annotations

import os
from typing import Any

import requests

ENDPOINT = "https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426"


def is_configured() -> bool:
    return bool(os.environ.get("RAKUTEN_APP_ID"))


def search_hotel(hotel_no: str, checkin: str, checkout: str, adults: int,
                  rooms: int = 1, timeout: int = 15) -> dict[str, Any] | None:
    """특정 시설 번호(hotel_no)의 공실 요금을 조회한다.

    hotel_no는 라쿠텐 트래블 시설 번호로, 호텔명만으로는 조회할 수 없다.
    실사용 시 먼저 楽天トラベル施設検索API(simple-hotel-search) 또는
    キーワード検索API로 대상 호텔들의 hotel_no를 먼저 매핑해 둬야 한다
    (이 매핑 단계는 아직 구현되지 않음 — data/candidates.json에 rakuten_hotel_no
    필드를 채워 넣는 방식으로 확장할 것).
    """
    app_id = os.environ.get("RAKUTEN_APP_ID")
    if not app_id:
        return None

    params = {
        "applicationId": app_id,
        "format": "json",
        "hotelNo": hotel_no,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adultNum": adults,
        "roomNum": rooms,
    }
    resp = requests.get(ENDPOINT, params=params, timeout=timeout)
    resp.raise_for_status()
    return resp.json()


def parse_response(payload: dict[str, Any]) -> dict[str, Any] | None:
    """응답에서 최저 총액·플랜명을 추출한다. 스키마 미대조 상태이므로 방어적으로 파싱."""
    if not payload or "hotels" not in payload:
        return None
    try:
        hotel = payload["hotels"][0]["hotel"]
        basic = next(h["hotelBasicInfo"] for h in hotel if "hotelBasicInfo" in h)
        rooms = [h["roomInfo"] for h in hotel if "roomInfo" in h]
        return {
            "hotel_name": basic.get("hotelName"),
            "min_charge_jpy": basic.get("hotelMinCharge"),
            "raw_rooms": rooms,
        }
    except (KeyError, IndexError, StopIteration):
        return None
