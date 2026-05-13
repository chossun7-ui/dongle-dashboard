"""StrategyID.ini 파서.

목표는 단 하나: `StrategyName=...` 값을 안전하게 추출하는 것.
표준 INI 가정 (섹션 헤더 `[Section]`, 키-값 `Key=Value`)이지만, 다음 변종에 관용적:
- 섹션 없는 최상단 키
- 공백·탭 패딩
- 주석 `;` 또는 `#`
- 같은 키가 여러 번 나오면 마지막 값을 채택

본 파서는 비교 알고리즘 본체(`app/compare/algorithm.py`)와는 분리되어 있다.
저장 시점에 한 번 추출해서 `recipes.film_name`에 저장하기 위함.
"""

from __future__ import annotations

import re

_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KV_RE = re.compile(r"^\s*([^=;#\s][^=]*?)\s*=\s*(.*?)\s*$")


def extract_strategy_name(ini_text: str) -> str | None:
    """StrategyName 추출. 없으면 None.

    대소문자 무시. 첫 번째가 아닌 **마지막** 매치를 채택 (덮어쓰기 관행 반영).
    """
    found: str | None = None
    for line in ini_text.splitlines():
        line = line.strip()
        if not line or line.startswith((";", "#")):
            continue
        if _SECTION_RE.match(line):
            continue
        m = _KV_RE.match(line)
        if not m:
            continue
        key, value = m.group(1), m.group(2)
        if key.lower() == "strategyname":
            # 따옴표 둘러싸인 값 처리
            v = value.strip()
            if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                v = v[1:-1]
            found = v
    return found or None
