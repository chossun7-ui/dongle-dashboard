"""분할된 인코딩 폴백 디코더.

우선순위 문자열(예: "utf-8,cp949,auto")을 받아 순서대로 시도.
"auto"는 chardet 자동감지. 모두 실패 시 errors='replace'로 강제 디코딩하고 경고.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import chardet

_log = logging.getLogger(__name__)


@dataclass(frozen=True)
class DecodeResult:
    text: str
    encoding_used: str
    fell_back: bool                  # True면 errors='replace' 사용 — 데이터 손실 가능


def decode_bytes(blob: bytes, priority: str, force: str | None = None) -> DecodeResult:
    """priority는 콤마 구분 인코딩 목록. force가 주어지면 그것만 시도."""
    if force:
        try:
            return DecodeResult(blob.decode(force), force, False)
        except UnicodeDecodeError:
            _log.warning("강제 인코딩 %s 디코딩 실패. 폴백 진행.", force)

    encodings = [e.strip().lower() for e in priority.split(",") if e.strip()]
    if not encodings:
        encodings = ["utf-8", "cp949", "auto"]

    for enc in encodings:
        if enc == "auto":
            detected = chardet.detect(blob).get("encoding")
            if not detected:
                continue
            try:
                return DecodeResult(blob.decode(detected), detected, False)
            except (UnicodeDecodeError, LookupError):
                continue
        else:
            try:
                return DecodeResult(blob.decode(enc), enc, False)
            except UnicodeDecodeError:
                continue

    return DecodeResult(blob.decode("utf-8", errors="replace"), "utf-8?replace", True)
