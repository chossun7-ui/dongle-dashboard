"""오사카 숙소 비교 도구 — 고정 조건 및 CLI 인자 정의.

날짜·인원은 --checkin/--checkout/--adults/--rooms-preferred로 재정의 가능하다.
그 외(대상 지역, 시드 후보, 제외 기준, 예산 우선순위)는 명세에 고정된 값이라
CLI 인자로 노출하지 않는다 — 바꾸려면 data/candidates.json을 직접 수정한다.
"""
import argparse
from dataclasses import dataclass
from datetime import date, datetime


# 일본 스포츠의 날 연휴(10/10~10/12)·한국 한글날 연휴(10/9~10/11)와 겹치는 성수기 날짜.
# lib/output.py에서 날짜별 단가 강조 표시에 사용.
HOLIDAY_PREMIUM_DATES = {"2026-10-09", "2026-10-10"}

# USJ 방문은 체크인 후 첫 이틀(10/8 또는 10/9) 중 확정되므로, 접근성 가중치는 앞쪽 2박에만 적용.
USJ_WEIGHTED_DATES = {"2026-10-08", "2026-10-09"}

# 오사카부 숙박세 면제 기준: 1인 1박 요금(세전) 7,000엔 미만이면 면제.
OSAKA_LODGING_TAX_EXEMPT_THRESHOLD_JPY = 7000

MIN_RATING = 3.5
MIN_REVIEW_COUNT = 30

EXCLUDED_HOTELS = {"Hotel Live Max 難波", "Hotel Live Max Namba"}


@dataclass
class RunConfig:
    checkin: date
    checkout: date
    adults: int
    rooms_preferred: int
    out_dir: str

    @property
    def nights(self) -> int:
        return (self.checkout - self.checkin).days


def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


def parse_args(argv=None) -> RunConfig:
    p = argparse.ArgumentParser(description="오사카 숙소 4박 총액 자동 비교")
    p.add_argument("--checkin", default="2026-10-08", type=_parse_date,
                    help="체크인 날짜 YYYY-MM-DD (기본 2026-10-08)")
    p.add_argument("--checkout", default="2026-10-12", type=_parse_date,
                    help="체크아웃 날짜 YYYY-MM-DD (기본 2026-10-12)")
    p.add_argument("--adults", default=3, type=int, help="성인 인원 수 (기본 3)")
    p.add_argument("--rooms-preferred", default=1, type=int,
                    help="선호 객실 수 (기본 1실 — 불가 시 자동으로 분할 후보 계산)")
    p.add_argument("--out-dir", default=".", help="results.md/csv 출력 디렉토리")
    ns = p.parse_args(argv)

    if ns.checkout <= ns.checkin:
        p.error("checkout은 checkin보다 뒤여야 합니다")

    return RunConfig(
        checkin=ns.checkin,
        checkout=ns.checkout,
        adults=ns.adults,
        rooms_preferred=ns.rooms_preferred,
        out_dir=ns.out_dir,
    )
