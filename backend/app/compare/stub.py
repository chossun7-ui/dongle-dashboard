"""비교 알고리즘 더미 구현 (stub).

본체(`algorithm.py`)가 사내 AI에 의해 추가되기 전까지의 임시 구현이다.
역할은 **인터페이스 충족만**:
- 입력 RecipeInput 들을 echo한다.
- 같은 텍스트면 same=True, 다르면 difflib 기반 라인 단위 diff만 반환한다.
- 의미 단위 파싱(섹션/키-값)은 수행하지 않는다.

본체가 추가되면 본 파일은 그대로 두어도 무방하다 (`interface.py`가 자동으로 본체를 우선).
"""

from __future__ import annotations

import difflib
from datetime import datetime, timezone

from app.compare.types import (
    CompareOptions,
    ComparePair,
    CompareRequest,
    CompareResult,
    CompareSummary,
    Diff,
    MatcherOp,
    RawDiff,
    SCHEMA_VERSION,
)


def _pair_indices(n: int, mode: str) -> list[tuple[int, int]]:
    if mode == "baseline":
        return [(0, j) for j in range(1, n)]
    return [(i, j) for i in range(n) for j in range(i + 1, n)]


def _build_raw_diff(left: str, right: str) -> RawDiff:
    left_lines = left.splitlines()
    right_lines = right.splitlines()
    unified = "\n".join(
        difflib.unified_diff(left_lines, right_lines, lineterm="", n=3)
    )
    matcher = difflib.SequenceMatcher(a=left_lines, b=right_lines, autojunk=False)
    ops = [
        MatcherOp(tag=tag, left_start=i1, left_end=i2, right_start=j1, right_end=j2)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
    ]
    return RawDiff(
        unified=unified,
        left_lines=left_lines,
        right_lines=right_lines,
        matcher_ops=ops,
    )


def _coarse_diffs(left: str, right: str) -> list[Diff]:
    """의미 단위 파싱 없이 라인 단위 변경을 Diff로 거칠게 표현."""
    diffs: list[Diff] = []
    matcher = difflib.SequenceMatcher(
        a=left.splitlines(), b=right.splitlines(), autojunk=False
    )
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        kind = {"replace": "changed", "delete": "removed", "insert": "added"}[tag]
        diffs.append(
            Diff(
                kind=kind,  # type: ignore[arg-type]
                section=None,
                key=None,
                left_value="\n".join(left.splitlines()[i1:i2]) or None,
                right_value="\n".join(right.splitlines()[j1:j2]) or None,
                left_line=i1 + 1 if i2 > i1 else None,
                right_line=j1 + 1 if j2 > j1 else None,
                note="stub: 라인 단위 diff (의미 단위 파싱 미수행)",
                severity="info",
            )
        )
    return diffs


def _similarity(left: str, right: str) -> float:
    if left == right:
        return 1.0
    return difflib.SequenceMatcher(a=left, b=right, autojunk=False).ratio()


def compare_recipes(request: CompareRequest) -> CompareResult:
    """인터페이스 명세를 충족하는 최소 구현."""
    opts: CompareOptions = request.options
    recipes = request.recipes
    warnings: list[str] = [
        "compare stub이 사용되었습니다. 사내 AI 본체(algorithm.py) 추가 후 정밀 비교 가능."
    ]

    pairs: list[ComparePair] = []
    by_kind = {"added": 0, "removed": 0, "changed": 0, "moved": 0}
    by_severity = {"info": 0, "minor": 0, "major": 0, "critical": 0}
    total_diffs = 0
    pairs_identical = 0

    for i, j in _pair_indices(len(recipes), opts.mode):
        left = recipes[i]
        right = recipes[j]
        same = left.analysis2_text == right.analysis2_text
        sim = _similarity(left.analysis2_text, right.analysis2_text)
        diffs = [] if same else _coarse_diffs(left.analysis2_text, right.analysis2_text)
        raw = None if same else _build_raw_diff(left.analysis2_text, right.analysis2_text)

        for d in diffs:
            by_kind[d.kind] = by_kind.get(d.kind, 0) + 1  # type: ignore[index]
            by_severity[d.severity] = by_severity.get(d.severity, 0) + 1
        total_diffs += len(diffs)
        if same:
            pairs_identical += 1

        pairs.append(
            ComparePair(
                left_recipe_id=left.recipe_id,
                right_recipe_id=right.recipe_id,
                same=same,
                similarity=sim,
                diffs=diffs,
                raw_diff=raw,
            )
        )

    summary = CompareSummary(
        total_pairs=len(pairs),
        pairs_identical=pairs_identical,
        pairs_with_diffs=len(pairs) - pairs_identical,
        total_diffs=total_diffs,
        by_kind=by_kind,
        by_severity=by_severity,
    )

    return CompareResult(
        schema_version=SCHEMA_VERSION,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        inputs=list(recipes),
        pairs=pairs,
        summary=summary,
        warnings=warnings,
    )
