"""비교 알고리즘의 입출력 타입.

본 파일의 시그니처는 `docs/COMPARE_ALGORITHM_SPEC.md`와 1:1로 동기화되어야 한다.
필드 추가/이름변경은 같은 커밋에서 문서·프론트엔드 타입(`frontend/src/types/compare.ts`)·SCHEMA_VERSION을 함께 올린다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SCHEMA_VERSION = "1.1"


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


# ─────────────────────────────────────────────────────────────────────────────
# Clusters & Pivot (1.1 추가)
#
# 동기: N≥10 설비 비교 시 N(N-1)/2 페어를 모두 펼치면 가독성 붕괴.
# 같은 본문(또는 같은 키-값 시그니처)을 가진 설비끼리 묶어
# K개 클러스터로 압축하면 K(K-1)/2 ≪ N(N-1)/2 가 된다.
#
# 본 두 구조는 본체(algorithm.py)가 직접 채워주면 그대로 사용하고,
# 비어 있으면 라우터/interface가 자체 계산하여 보강한다.
# ─────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Cluster:
    id: str                            # "A", "B", "C", ...
    recipe_ids: list[int]
    representative_recipe_id: int      # 클러스터 대표 (정렬상 가장 작은 ID)
    signature: str                     # 키-값 정규화 sha256
    body_hash_match: bool              # True면 본문 바이트 동일
    is_majority: bool                  # 다수 그룹 (size가 최대이고 2 이상)


@dataclass(frozen=True)
class ClusterPairDiff:
    left_cluster_id: str
    right_cluster_id: str
    diffs: list[Diff]


@dataclass(frozen=True)
class ClusteringResult:
    clusters: list[Cluster]
    pair_diffs: list[ClusterPairDiff]


@dataclass(frozen=True)
class PivotBranch:
    value: str                         # "(없음)" 이면 해당 키가 누락된 설비들
    recipe_ids: list[int]
    is_majority: bool


@dataclass(frozen=True)
class PivotEntry:
    section: str | None
    key: str
    branches: list[PivotBranch]        # 큰 그룹이 첫 번째
    is_outlier_present: bool           # 분기 중 size=1 그룹이 하나라도 있으면 True


@dataclass(frozen=True)
class PivotResult:
    entries: list[PivotEntry]          # 분기 수·외톨이 보유 키 우선 정렬


@dataclass(frozen=True)
class CompareResult:
    schema_version: str
    generated_at: str
    inputs: list[RecipeInput]
    pairs: list[ComparePair]
    summary: CompareSummary
    warnings: list[str] = field(default_factory=list)
    # 1.1: N-way 가독성용 부가 산출물. 본체가 채워주지 않으면 라우터가 보강.
    clusters: ClusteringResult | None = None
    pivot: PivotResult | None = None
