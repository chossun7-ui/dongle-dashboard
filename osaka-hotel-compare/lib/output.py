"""results.md / results.csv / checklist.md 생성."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from config import HOLIDAY_PREMIUM_DATES, RunConfig

CHECKLIST_TEMPLATE = [
    ("아고다", "\"세금·수수료 포함 표시\" 켜고 최종 결제 화면까지 진행",
     "https://www.agoda.com/search?q={query}"),
    ("라쿠텐 트래블", "쿠폰 탭 확인 후 적용가 확인",
     "https://search.travel.rakuten.co.jp/ds/hotellist/?f_query={query}"),
    ("호텔 공식 홈페이지", "회원가 확인 (특히 토요코인, 도미인)",
     "https://www.google.com/search?q={query}+公式サイト+予約"),
    ("결제 통화", "결제 통화가 JPY인지 확인 (원화 결제 선택 시 3~8% 손해)", None),
]


def _fmt_jpy(v: float | None) -> str:
    return f"¥{v:,.0f}" if v is not None else "N/A"


def _fmt_krw(v: float | None) -> str:
    return f"₩{v:,.0f}" if v is not None else "N/A"


def _fmt_bool(v: bool | None, yes="있음", no="없음") -> str:
    if v is None:
        return "N/A"
    return yes if v else no


def write_results_md(rows: list[dict[str, Any]], cfg: RunConfig, rate_info: dict[str, Any]) -> str:
    lines = []
    lines.append("# 오사카 숙소 비교 결과\n")
    lines.append(f"- 체크인: {cfg.checkin} / 체크아웃: {cfg.checkout} ({cfg.nights}박)")
    lines.append(f"- 인원: 성인 {cfg.adults}명 / 선호 객실: {cfg.rooms_preferred}실")
    fetched_at = rate_info.get("fetched_at", "N/A")
    live_note = "실시간 조회" if rate_info.get("live") else "**캐시 폴백값 — 실시간 조회 실패**"
    lines.append(f"- 환율 기준: 1 JPY = {rate_info['jpy_to_krw']} KRW ({live_note}, 기준 시각: {fetched_at})")
    lines.append(f"  - 출처: {rate_info.get('source', 'N/A')}")
    lines.append("- 정렬: 4박 총액(¥) 오름차순, 가격 미확인 항목은 표 하단으로 분리\n")

    header = ("| 순위 | 호텔명 | 지역 | 객실 구성 | 4박 총액(¥) | 1인당(¥) | 1인당(₩) | "
               "10/8 | 10/9 | 10/10 | 10/11 | 조식 | 주방 | 통금 | 숙박세 | 출처 |")
    sep = "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    lines.append(header)
    lines.append(sep)

    priced = [r for r in rows if r["resolved_total_jpy"] is not None]
    missing = [r for r in rows if r["resolved_total_jpy"] is None]

    for i, r in enumerate(priced, start=1):
        nr = r.get("nightly_rates_jpy", {}) or {}

        def cell(date_key: str) -> str:
            v = nr.get(date_key)
            s = _fmt_jpy(v)
            return f"**{s}**" if date_key in HOLIDAY_PREMIUM_DATES and v is not None else s

        room_cfg = r.get("room_config", "N/A") or "N/A"
        if r.get("used_split_rooms"):
            room_cfg += " (2실 분할 총액)"

        curfew = r.get("curfew") or {}
        curfew_cell = "⚠️ 있음" if curfew.get("has_curfew") else _fmt_bool(curfew.get("has_curfew"))

        lines.append(
            f"| {i} | {r.get('hotel_name', 'N/A')} | {r.get('area', 'N/A')} | {room_cfg} | "
            f"{_fmt_jpy(r['resolved_total_jpy'])} | {_fmt_jpy(r.get('per_person_total_jpy'))} | "
            f"{_fmt_krw(r.get('per_person_total_krw'))} | "
            f"{cell('10-08')} | {cell('10-09')} | {cell('10-10')} | {cell('10-11')} | "
            f"{_fmt_bool(r.get('breakfast_included'))} | {_fmt_bool(r.get('kitchen'))} | "
            f"{curfew_cell} | {r.get('tax_note', 'N/A')} | "
            f"[링크]({r.get('source_url', '').split(' ; ')[0] or '#'}) |"
        )

    if not priced:
        lines.append("| - | (가격 확인된 숙소 없음 — 아래 '가격 못 가져온 숙소' 섹션 참고) | | | | | | | | | | | | | |")

    lines.append("\n## 가격 못 가져온 숙소\n")
    if missing:
        lines.append("| 호텔명 | 지역 | 실패 사유 | 참고 출처 |")
        lines.append("|---|---|---|---|")
        for r in missing:
            lines.append(
                f"| {r.get('hotel_name', 'N/A')} | {r.get('area', 'N/A')} | "
                f"{r.get('failure_reason', 'N/A')} | {r.get('source_url', 'N/A')} |"
            )
    else:
        lines.append("(없음 — 모든 대상 숙소의 가격을 확인함)")

    lines.append("\n## 참고 메모\n")
    for r in rows:
        note = r.get("notes")
        if note:
            lines.append(f"- **{r.get('hotel_name')}**: {note}")

    return "\n".join(lines) + "\n"


def write_results_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "순위", "호텔명", "지역", "객실구성", "4박총액_JPY", "1인당_JPY", "1인당_KRW",
        "10-08_JPY", "10-09_JPY", "10-10_JPY", "10-11_JPY",
        "조식포함", "주방", "통금", "숙박세메모", "예약가능여부", "출처URL", "가격확인여부", "실패사유",
    ]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, r in enumerate(rows, start=1):
            nr = r.get("nightly_rates_jpy", {}) or {}
            curfew = r.get("curfew") or {}
            writer.writerow({
                "순위": i if r["resolved_total_jpy"] is not None else "",
                "호텔명": r.get("hotel_name", ""),
                "지역": r.get("area", ""),
                "객실구성": r.get("room_config", ""),
                "4박총액_JPY": r.get("resolved_total_jpy", ""),
                "1인당_JPY": r.get("per_person_total_jpy", ""),
                "1인당_KRW": r.get("per_person_total_krw", ""),
                "10-08_JPY": nr.get("10-08", ""),
                "10-09_JPY": nr.get("10-09", ""),
                "10-10_JPY": nr.get("10-10", ""),
                "10-11_JPY": nr.get("10-11", ""),
                "조식포함": r.get("breakfast_included", ""),
                "주방": r.get("kitchen", ""),
                "통금": curfew.get("has_curfew", ""),
                "숙박세메모": r.get("tax_note", ""),
                "예약가능여부": r.get("availability", ""),
                "출처URL": r.get("source_url", ""),
                "가격확인여부": r.get("price_found", False),
                "실패사유": r.get("failure_reason", ""),
            })


def write_checklist_md(rows: list[dict[str, Any]], path: Path, top_n: int = 4) -> None:
    priced = [r for r in rows if r["resolved_total_jpy"] is not None]
    top = priced[:top_n] if priced else rows[:top_n]

    lines = ["# 상위 후보 예약 전 수동 확인 체크리스트\n"]
    if not priced:
        lines.append(
            "> ⚠️ 이번 조사에서 가격이 확정된 숙소가 없어(WebFetch 도구 장애로 실시간 조회 실패), "
            "아래는 순위가 아니라 **시드 후보 우선순위** 기준으로 나열한 것입니다. "
            "실제 순위는 아래 항목을 직접 조회한 뒤 정하세요.\n"
        )

    for r in top:
        name = r.get("hotel_name", "N/A")
        query = name.replace(" ", "+")
        lines.append(f"## {name} ({r.get('area', 'N/A')})\n")
        for site, action, url_tpl in CHECKLIST_TEMPLATE:
            url = url_tpl.format(query=query) if url_tpl else None
            check = f"[ ] {site} — {action}"
            if url:
                check += f" → {url}"
            lines.append(check)
        lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
