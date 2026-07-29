"""소스별 조회 결과를 병합하고, 1실 3인 불가 시 2실 분할 총액을 계산하고,
최종적으로 4박 총액 오름차순 정렬 리스트를 만든다.
"""
from __future__ import annotations

from typing import Any

from lib import fx, tax


def per_person_per_night(total_4nights_jpy: float | None, adults: int, nights: int) -> float | None:
    if total_4nights_jpy is None:
        return None
    return total_4nights_jpy / adults / nights


def resolve_room_total(entry: dict[str, Any], rooms_preferred: int) -> dict[str, Any]:
    """1실 3인이 확인되지 않았고 2실 분할 정보가 있으면 분할 총액을 사용.

    entry에 "split_rooms_total_jpy"가 있으면(수동 조사 단계에서 "2실 분할 시 총액"을
    별도로 조사해 넣은 경우) 그것을 대체 총액으로 채택하고 room_config에 표시한다.
    두 값 다 없으면 total은 None으로 남는다(추정 금지).
    """
    total = entry.get("total_4nights_jpy")
    used_split = False
    if total is None and entry.get("split_rooms_total_jpy") is not None:
        total = entry["split_rooms_total_jpy"]
        used_split = True
    return {**entry, "resolved_total_jpy": total, "used_split_rooms": used_split}


def build_comparison_rows(entries: list[dict[str, Any]], adults: int, nights: int,
                           rooms_preferred: int) -> list[dict[str, Any]]:
    rate_info = fx.get_jpy_to_krw_rate()
    rows = []
    for raw in entries:
        entry = resolve_room_total(raw, rooms_preferred)
        total = entry["resolved_total_jpy"]
        ppn = per_person_per_night(total, adults, nights)
        per_person_total = (total / adults) if total is not None else None

        rows.append({
            **entry,
            "per_person_total_jpy": round(per_person_total) if per_person_total is not None else None,
            "per_person_total_krw": fx.jpy_to_krw(per_person_total, rate_info),
            "tax_note": tax.tax_note(ppn, entry.get("tax_included")),
        })

    # 가격 확인된 항목을 4박 총액 오름차순으로, 미확인 항목은 뒤로.
    rows.sort(key=lambda r: (r["resolved_total_jpy"] is None, r["resolved_total_jpy"] or 0))
    return rows, rate_info
