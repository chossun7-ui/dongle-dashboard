"""오사카부 숙박세(宿泊税) 계산.

규칙(명세 5번): 1인 1박 요금(세금 제외 숙박요금)이 7,000엔 미만이면 면제.
7,000엔 이상 구간부터는 금액 구간별 정액제이나, 정확한 구간별 세액은 오사카부의
최신 조례를 별도로 확인해야 한다(이 도구는 "면제 여부"만 판정하고, 실제 정액
세액 산정은 하지 않는다 — 대부분의 예약 사이트 표시가에는 이미 숙박세가
포함/불포함 여부가 명시되므로, 이 모듈은 "표시가에 포함됐는지 확인이 필요한
케이스인지"를 플래그하는 용도로만 쓴다).
"""
from __future__ import annotations

from config import OSAKA_LODGING_TAX_EXEMPT_THRESHOLD_JPY


def is_tax_exempt(per_person_per_night_jpy: float | None) -> bool | None:
    """1인 1박 요금 기준 오사카부 숙박세 면제 여부. 요금 정보가 없으면 None(판정 불가)."""
    if per_person_per_night_jpy is None:
        return None
    return per_person_per_night_jpy < OSAKA_LODGING_TAX_EXEMPT_THRESHOLD_JPY


def tax_note(per_person_per_night_jpy: float | None, tax_included: bool | None) -> str:
    """results 표에 붙일 숙박세 상태 메모."""
    exempt = is_tax_exempt(per_person_per_night_jpy)
    if exempt is None:
        return "1인 1박 요금 미확인 — 면제 여부 판정 불가"
    if exempt:
        return "1인 1박 7,000엔 미만 → 숙박세 면제 대상"
    if tax_included is True:
        return "숙박세 부과 대상, 총액에 포함됨"
    if tax_included is False:
        return "숙박세 부과 대상, 총액에 미포함 — 현지 결제 시 추가"
    return "숙박세 부과 대상 (총액 포함 여부 미확인 — 예약 시 확인 필요)"
