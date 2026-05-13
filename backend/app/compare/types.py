"""비교 알고리즘의 입출력 타입.

본 파일의 시그니처는 `docs/COMPARE_ALGORITHM_SPEC.md`와 1:1로 동기화되어야 한다.
필드 추가/이름변경은 같은 커밋에서 문서·프론트엔드 타입(`frontend/src/types/compare.ts`)·SCHEMA_VERSION을 함께 올린다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SCHEMA_VERSION = "1.0"


class CompareError(Exception):
    """파싱/비교 도중 알고리즘 내부에서 발생한 회복 불가 오류."""


# ─────────────────────────────────────────────────────────────────────────────
# Input
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RecipeInput:
    recipe_id: int
    equipment_name: str
    line_name: str
    model_name: str
    path: str
    film_name: str
    analysis2_text: str
    strategy_ini_text: str


@dataclass(frozen=True)
class CompareOptions:
    mode: Literal["pairwise", "baseline"] = "pairwise"
    ignore_whitespace: bool = True
    ignore_comments: bool = True
    case_sensitive_keys: bool = False
    numeric_tolerance: float = 0.0
    include_unchanged: bool = False
    section_order_sensitive: bool = False


@dataclass(frozen=True)
class CompareRequest:
    recipes: list[RecipeInput]
    options: CompareOptions = field(default_factory=CompareOptions)


# ─────────────────────────────────────────────────────────────────────────────
# Output
# ─────────────────────────────────────────────────────────────────────────────


DiffKind = Literal["added", "removed", "changed", "moved", "unchanged"]
Severity = Literal["info", "minor", "major", "critical"]


@dataclass(frozen=True)
class Diff:
    kind: DiffKind
    section: str | None
    key: str | None
    left_value: str | None
    right_value: str | None
    left_line: int | None
    right_line: int | None
    note: str | None = None
    severity: Severity = "info"


@dataclass(frozen=True)
class MatcherOp:
    tag: Literal["equal", "replace", "delete", "insert"]
    left_start: int
    left_end: int
    right_start: int
    right_end: int


@dataclass(frozen=True)
class RawDiff:
    unified: str
    left_lines: list[str]
    right_lines: list[str]
    matcher_ops: list[MatcherOp]


@dataclass(frozen=True)
class ComparePair:
    left_recipe_id: int
    right_recipe_id: int
    same: bool
    similarity: float
    diffs: list[Diff]
    raw_diff: RawDiff | None = None


@dataclass(frozen=True)
class CompareSummary:
    total_pairs: int
    pairs_identical: int
    pairs_with_diffs: int
    total_diffs: int
    by_kind: dict[str, int]
    by_severity: dict[str, int]


@dataclass(frozen=True)
class CompareResult:
    schema_version: str
    generated_at: str
    inputs: list[RecipeInput]
    pairs: list[ComparePair]
    summary: CompareSummary
    warnings: list[str] = field(default_factory=list)
