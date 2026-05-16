# 비교 알고리즘 인계 명세 (Compare Algorithm Spec)

본 문서는 **본 저장소 외부**에 있는 작성자(사내 AI 또는 엔지니어)가 비교 알고리즘 본체를 작성할 때 충족해야 하는 인터페이스를 정의한다. 본체는 `backend/app/compare/algorithm.py`(신규 작성)로 들어가며, 본 저장소에는 동일 시그니처의 **더미 구현(stub)** 만 들어 있다. 인터페이스를 어기지 않는 한, 알고리즘 내부 구현은 자유다.

---

## 0. 한 줄 요약

> **두 개(또는 N개)의 Recipe(`analysis2.txt` 본문 + `StrategyID.ini` 메타)를 입력받아, "어떤 항목이 어떻게 달라졌는지"를 구조화된 JSON으로 반환하라.**

---

## 1. 입력

### 1.1 단일 Recipe 표현 (`RecipeInput`)

```python
@dataclass(frozen=True)
class RecipeInput:
    recipe_id: int            # DB 행 ID. 비교 결과 추적용. 알고리즘은 이 값을 그대로 결과에 echo.
    equipment_name: str       # 예: "MTKB561"
    line_name: str            # 예: "P1"
    model_name: str           # 예: "IRIS"
    path: str                 # 설비 내 절대경로, 예: "/Film List/as42"
    film_name: str            # StrategyID.ini의 StrategyName 값
    analysis2_text: str       # analysis2.txt 본문 전체 (이미 적절한 인코딩으로 디코딩됨)
    strategy_ini_text: str    # StrategyID.ini 본문 전체
```

JSON 직렬화 시:

```json
{
  "recipe_id": 1234,
  "equipment_name": "MTKB561",
  "line_name": "P1",
  "model_name": "IRIS",
  "path": "/Film List/as42",
  "film_name": "IRIS_BlueProc_v3",
  "analysis2_text": "[General]\nPower=1500\n...",
  "strategy_ini_text": "[Strategy]\nStrategyName=IRIS_BlueProc_v3\n..."
}
```

### 1.2 비교 요청 (`CompareRequest`)

```python
@dataclass(frozen=True)
class CompareRequest:
    recipes: list[RecipeInput]   # 길이 ≥ 2. N-way 비교 가능.
    options: CompareOptions      # 아래 1.3
```

- **N=2 (가장 일반적인 케이스)**: side-by-side 두 개 비교. 결과의 `pairs` 길이 1.
- **N>2 (다중 비교)**: 모든 (i, j) 쌍에 대해 비교를 생성하거나, 첫 번째를 baseline으로 두고 baseline vs 나머지를 생성. 알고리즘 작성자가 결정하되 `options.mode`로 선택 가능하게 한다.

### 1.3 옵션 (`CompareOptions`)

```python
@dataclass(frozen=True)
class CompareOptions:
    mode: Literal["pairwise", "baseline"] = "pairwise"
    # pairwise: 모든 (i, j) 조합 — N(N-1)/2 개
    # baseline: recipes[0]을 기준으로 나머지와 비교 — N-1 개

    ignore_whitespace: bool = True
    # 키-값 비교 시 양옆 공백·줄끝 공백 무시

    ignore_comments: bool = True
    # 주석(;, #, //로 시작하는 줄) 무시

    case_sensitive_keys: bool = False
    # 키 이름 대소문자 구분 여부. False면 Power == POWER == power

    numeric_tolerance: float = 0.0
    # 수치 비교 시 절대 허용 오차. 0이면 완전 일치.
    # 예: 0.001이면 1500.0001 == 1500.0002 로 본다.

    include_unchanged: bool = False
    # True면 결과에 변경 없는 항목까지 포함 (UI에서 회색으로 표시).
    # False면 changed/added/removed만 반환 (크기 작음).

    section_order_sensitive: bool = False
    # True면 섹션 순서가 다른 것도 변경으로 본다. 일반적으로 False.
```

---

## 2. 출력

### 2.1 최상위 (`CompareResult`)

```python
@dataclass(frozen=True)
class CompareResult:
    schema_version: str               # "1.0" 등. 본 명세 버전.
    generated_at: str                 # ISO 8601 UTC, 예: "2026-05-13T12:34:56Z"
    inputs: list[RecipeInput]         # 입력 echo (recipe_id로 추적)
    pairs: list[ComparePair]          # 비교 결과 쌍의 배열
    summary: CompareSummary           # 전체 요약 통계
    warnings: list[str]               # 파싱 경고 등 (예: "as42의 IniText에 StrategyName 없음")
```

### 2.2 한 쌍의 비교 (`ComparePair`)

```python
@dataclass(frozen=True)
class ComparePair:
    left_recipe_id: int
    right_recipe_id: int
    same: bool                        # 모든 의미적 항목이 동일하면 True
    similarity: float                 # 0.0 ~ 1.0. 단순 라인 기준이 아니라 의미 기준 유사도 권장.
    diffs: list[Diff]                 # 차이 목록 (의미 단위)
    raw_diff: RawDiff | None          # difflib 기반 라인 단위 보조 diff (선택 — UI fallback용)
```

### 2.3 의미 단위 차이 (`Diff`)

```python
@dataclass(frozen=True)
class Diff:
    kind: Literal["added", "removed", "changed", "moved", "unchanged"]
    section: str | None               # 예: "General", "Step1". 섹션 밖이면 None.
    key: str | None                   # 키-값 쌍이면 키 이름. 블록·자유텍스트면 None.
    left_value: str | None            # right에만 있는 항목(added)이면 None.
    right_value: str | None           # left에만 있는 항목(removed)이면 None.
    left_line: int | None             # 1-based 줄 번호. UI에서 점프할 때 사용.
    right_line: int | None
    note: str | None                  # "numeric tolerance 내 동일" 등 사람용 메모 (선택)
    severity: Literal["info", "minor", "major", "critical"] = "info"
    # severity는 알고리즘이 판단. 예: 특정 키 화이트리스트(Power, Pressure 등)는 critical,
    # 나머지는 minor. UI에서 색상 분류에 활용.
```

### 2.4 라인 단위 보조 diff (`RawDiff`)

```python
@dataclass(frozen=True)
class RawDiff:
    unified: str                      # `difflib.unified_diff` 출력 그대로
    left_lines: list[str]             # side-by-side 렌더링용
    right_lines: list[str]
    matcher_ops: list[MatcherOp]      # difflib.SequenceMatcher.get_opcodes() 가공판
```

```python
@dataclass(frozen=True)
class MatcherOp:
    tag: Literal["equal", "replace", "delete", "insert"]
    left_start: int                   # 0-based 줄 인덱스
    left_end: int
    right_start: int
    right_end: int
```

### 2.5 요약 (`CompareSummary`)

```python
@dataclass(frozen=True)
class CompareSummary:
    total_pairs: int
    pairs_identical: int
    pairs_with_diffs: int
    total_diffs: int
    by_kind: dict[Literal["added", "removed", "changed", "moved"], int]
    by_severity: dict[Literal["info", "minor", "major", "critical"], int]
```

---

## 3. 시그니처 (Python 진입점)

```python
# backend/app/compare/algorithm.py  ← 사내 AI가 작성할 파일

from app.compare.types import CompareRequest, CompareResult

def compare_recipes(request: CompareRequest) -> CompareResult:
    """비교 본체. 동기 함수.

    Args:
        request: 비교 대상 Recipe들과 옵션.

    Returns:
        구조화된 비교 결과.

    Raises:
        ValueError: recipes 길이가 2 미만이거나 입력 텍스트가 None일 때.
        CompareError: 파싱 실패 등 알고리즘 내부 오류. types.py에 정의됨.

    동시성:
        CPU 바운드. FastAPI 측에서 run_in_executor(ProcessPoolExecutor)로 호출한다.
        함수 본체는 thread-safe / fork-safe해야 한다. 전역 상태 변경 금지.
    """
    ...
```

비동기 변형이 필요하면 별도로 `async def compare_recipes_async(...)`를 두지 말고, 본체는 동기로 두고 FastAPI 라우터에서 `loop.run_in_executor`로 감싼다.

---

## 4. 예제

### 4.1 입력 예제 (개념적)

`analysis2.txt`(좌):
```
[General]
Power=1500
Pressure=120
; 옛 설정
Gas=Ar

[Step1]
Time=30
Temperature=250
```

`analysis2.txt`(우):
```
[General]
Power=1600
Pressure=120
Gas=N2

[Step1]
Time=30
Temperature=255

[Step2]
Time=10
```

### 4.2 기대 출력 (요약본)

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-05-13T12:34:56Z",
  "inputs": [/* RecipeInput 두 개 echo */],
  "pairs": [
    {
      "left_recipe_id": 101,
      "right_recipe_id": 202,
      "same": false,
      "similarity": 0.76,
      "diffs": [
        {
          "kind": "changed",
          "section": "General",
          "key": "Power",
          "left_value": "1500",
          "right_value": "1600",
          "left_line": 2,
          "right_line": 2,
          "severity": "critical",
          "note": null
        },
        {
          "kind": "changed",
          "section": "General",
          "key": "Gas",
          "left_value": "Ar",
          "right_value": "N2",
          "left_line": 5,
          "right_line": 4,
          "severity": "major",
          "note": null
        },
        {
          "kind": "changed",
          "section": "Step1",
          "key": "Temperature",
          "left_value": "250",
          "right_value": "255",
          "left_line": 9,
          "right_line": 8,
          "severity": "minor",
          "note": "차이 5"
        },
        {
          "kind": "added",
          "section": "Step2",
          "key": null,
          "left_value": null,
          "right_value": "[Step2]\nTime=10",
          "left_line": null,
          "right_line": 10,
          "severity": "major",
          "note": "새 섹션 추가"
        }
      ],
      "raw_diff": { /* 선택 */ }
    }
  ],
  "summary": {
    "total_pairs": 1,
    "pairs_identical": 0,
    "pairs_with_diffs": 1,
    "total_diffs": 4,
    "by_kind": { "added": 1, "removed": 0, "changed": 3, "moved": 0 },
    "by_severity": { "info": 0, "minor": 1, "major": 2, "critical": 1 }
  },
  "warnings": []
}
```

---

## 5. 권장(필수가 아님) 처리 단계

알고리즘 작성자가 어떻게 구현하든 자유이나, 권장 단계는 다음과 같다:

1. **전처리**: 인코딩 정규화는 이미 호출자가 끝냄. 줄끝(`\r\n` → `\n`) 통일, BOM 제거.
2. **주석 제거**: 옵션 켜져 있으면 `;`, `#`, `//`로 시작하는 줄 제거.
3. **섹션·키-값 파싱**:
   - `[Section]` 헤더로 섹션 구분.
   - 섹션 내부에서 `Key=Value` 패턴 추출. 양쪽 공백 strip.
   - `Key=Value` 패턴이 아닌 줄(블록·표·자유텍스트)은 섹션의 `_raw_lines`로 별도 보관.
4. **의미 단위 비교**:
   - 같은 섹션 안의 같은 키끼리 매칭 → `changed`/`unchanged`.
   - 한쪽에만 있는 섹션/키 → `added`/`removed`.
   - 섹션이 양쪽 다 있지만 순서만 다르면 `section_order_sensitive=False`일 때 `moved`.
5. **보조 라인 diff**: `difflib.SequenceMatcher`로 `raw_diff` 채움. UI fallback용.
6. **severity 판정**: 키 화이트리스트 매핑 또는 휴리스틱. 기본은 `minor`, 변경 절댓값이 클수록 상향.
7. **유사도 계산**: 변경된 키 비율 또는 라인 매칭률. 0.0~1.0.
8. **결과 빌드**: `CompareResult` 직렬화.

---

## 6. 절대 어기지 말 것 (Hard Constraints)

1. **시그니처 변경 금지**: 함수 이름·파라미터·반환 타입은 본 문서 그대로. 변경이 필요하면 본 문서를 같은 PR에서 업데이트.
2. **부작용 금지**: 전역 변수 변경, 파일 쓰기, 네트워크 호출 금지. 순수 함수처럼 동작.
3. **결과는 직렬화 가능**: `dataclasses.asdict()` 또는 `pydantic`으로 즉시 JSON 변환 가능해야 한다.
4. **결정론적**: 같은 입력에 대해 항상 같은 출력. (단, `generated_at`은 예외 — 호출 시각)
5. **`recipe_id` echo**: 입력의 `recipe_id`를 결과의 `inputs`·`pairs.left_recipe_id`·`pairs.right_recipe_id`에 정확히 그대로 전달.
6. **타임아웃 인식**: 큰 파일(>1MB)에서 무한 루프에 빠지지 않게 방어. 라인 수 또는 비교 항목 수 상한을 두는 것을 권장.

---

## 7. 권장(필수가 아님) — 성능 가이드

- 파일당 50KB, 라인 1,500개 정도가 일반적이라고 가정. 그 이상이면 chunked.
- N=2 비교는 100ms 이내 목표.
- N=10 pairwise(45 쌍) 비교는 1초 이내 목표.
- 더 큰 데이터를 만나면 `compare/algorithm.py` 내에서 적응형 처리(예: 라인 1만 개 초과 시 라인 diff만 반환하고 의미 단위 분석 생략).

---

## 8. 호출 흐름 (참고)

```
[UI] /api/compare POST body: { recipe_ids: [101, 202], options: {...} }
        ↓
[FastAPI router /backend/app/api/compare.py]
        ↓ (DB에서 recipe 본문 로드 → RecipeInput 빌드)
        ↓ run_in_executor(ProcessPool)
[backend/app/compare/algorithm.py] compare_recipes(request) → CompareResult
        ↓
[FastAPI] dataclasses.asdict() → JSON 응답
        ↓
[UI] CompareDialog 렌더링 (side-by-side, 변경 점프, 검색)
```

---

## 9. (1.1) N-way 가독성용 부가 산출물 — Clusters · Pivot

본체가 채워주지 않으면 `app/compare/clustering.py`의 폴백이 자체 INI 파싱으로 채운다.
본체가 더 정밀한 의미 단위 파싱을 한다면 직접 채워 라우터의 폴백을 비활성화할 수 있다.

### 9.1 Clusters

```python
@dataclass(frozen=True)
class Cluster:
    id: str                            # "A", "B", "C", ... (26개 초과 시 "AA" 등)
    recipe_ids: list[int]
    representative_recipe_id: int
    signature: str                     # 키-값 정규화 sha256
    body_hash_match: bool              # True면 본문 바이트 동일
    is_majority: bool                  # 최대 크기이고 size ≥ 2

@dataclass(frozen=True)
class ClusterPairDiff:
    left_cluster_id: str
    right_cluster_id: str
    diffs: list[Diff]

@dataclass(frozen=True)
class ClusteringResult:
    clusters: list[Cluster]
    pair_diffs: list[ClusterPairDiff]
```

권장 규칙:
- 본문이 바이트 단위로 같으면 즉시 같은 클러스터, `body_hash_match=True`.
- 그렇지 않으면 키-값 정규화 시그니처가 같을 때 같은 클러스터.
- 정렬: 크기 큰 클러스터부터 A, B, C ... 부여. 크기 1인 클러스터는 외톨이 후보로 UI가 강조.

### 9.2 Pivot

```python
@dataclass(frozen=True)
class PivotBranch:
    value: str                         # "(없음)" 이면 해당 키가 누락된 설비들 묶음
    recipe_ids: list[int]
    is_majority: bool

@dataclass(frozen=True)
class PivotEntry:
    section: str | None
    key: str
    branches: list[PivotBranch]        # 큰 그룹이 앞
    is_outlier_present: bool           # size=1 그룹이 하나라도 있으면 True

@dataclass(frozen=True)
class PivotResult:
    entries: list[PivotEntry]
```

권장 규칙:
- 모든 입력 설비에서 동일한 값을 갖는 키는 기본 제외(`include_identical=False`).
- 정렬: 분기 수 ↓, 외톨이 보유 키 ↑, 섹션·키 알파벳 ↑.

### 9.3 CompareResult 확장

```python
@dataclass(frozen=True)
class CompareResult:
    ...
    clusters: ClusteringResult | None = None
    pivot: PivotResult | None = None
```

본체가 None을 반환해도 `interface.compare_recipes()`가 폴백으로 채운다.

## 10. 본 문서 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| 1.0 | 2026-05-13 | 최초 작성 |
| 1.1 | 2026-05-14 | Clusters · Pivot 부가 산출물 추가 (N-way 가독성용) |

문서를 수정하면 `schema_version` 상수(`backend/app/compare/types.py::SCHEMA_VERSION`)도 같은 값으로 올려야 한다.
