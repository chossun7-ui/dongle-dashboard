"""Recipe Film Script 비교 모듈.

본 패키지의 역할은 두 가지다.

1. **인터페이스 정의** (`types.py`, `interface.py`)
   - 입력/출력 데이터 클래스, 시그니처, 스키마 버전.
   - 본 저장소가 책임지는 영역. 임의로 바꾸지 않는다.

2. **본체 구현** (`algorithm.py`)
   - 실제 비교 로직. 사내 AI가 별도로 작성하여 끼워 넣는다.
   - 본 저장소에는 `stub.py`로 더미 구현만 들어 있다.
   - 본체가 추가되면 `interface.compare_recipes`가 우선적으로 `algorithm.compare_recipes`를 호출한다.

작성 명세: `docs/COMPARE_ALGORITHM_SPEC.md`
"""

from app.compare.types import (
    Cluster,
    ClusterPairDiff,
    ClusteringResult,
    CompareError,
    CompareOptions,
    ComparePair,
    CompareRequest,
    CompareResult,
    CompareSummary,
    Diff,
    MatcherOp,
    PivotBranch,
    PivotEntry,
    PivotResult,
    RawDiff,
    RecipeInput,
    SCHEMA_VERSION,
)
from app.compare.interface import compare_recipes

__all__ = [
    "Cluster",
    "ClusterPairDiff",
    "ClusteringResult",
    "CompareError",
    "CompareOptions",
    "ComparePair",
    "CompareRequest",
    "CompareResult",
    "CompareSummary",
    "Diff",
    "MatcherOp",
    "PivotBranch",
    "PivotEntry",
    "PivotResult",
    "RawDiff",
    "RecipeInput",
    "SCHEMA_VERSION",
    "compare_recipes",
]
