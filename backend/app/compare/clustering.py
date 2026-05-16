"""N-way 비교 결과의 가독성용 산출물 — 설비 클러스터링 + 키 분기 표.

본 모듈은 비교 알고리즘 본체(`algorithm.py`)의 결과 정확도에 의존하지 않는다.
입력 RecipeInput 리스트만으로 자체 INI-스타일 파싱 → 키-값 시그니처를 만든다.

사내 AI 본체가 이 두 산출물을 직접 채워주면(=CompareResult.clusters/pivot이 None이 아니면)
본 모듈은 호출되지 않고 본체 결과가 그대로 사용된다.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict

from app.compare.types import (
    Cluster,
    ClusterPairDiff,
    ClusteringResult,
    Diff,
    PivotBranch,
    PivotEntry,
    PivotResult,
    RecipeInput,
)

_SECTION_RE = re.compile(r"^\s*\[([^\]]+)\]\s*$")
_KV_RE = re.compile(r"^\s*([^=;#\s][^=]*?)\s*=\s*(.*?)\s*$")

KvMap = "OrderedDict[tuple[str | None, str], tuple[str, int]]"  # 값 + 첫 등장 줄번호


def parse_kv_with_lines(text: str) -> "OrderedDict[tuple[str | None, str], tuple[str, int]]":
    """매우 단순한 INI 파서.

    - `[Section]` 헤더로 섹션 전환.
    - `Key=Value` 라인만 채택. 주석(`;`, `#`) 무시.
    - 같은 키 중복 시 **마지막 값**을 채택 (덮어쓰기).
    - 줄번호는 1-based 첫 등장 위치.
    """
    out: OrderedDict[tuple[str | None, str], tuple[str, int]] = OrderedDict()
    section: str | None = None
    for idx, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith((";", "#")):
            continue
        m = _SECTION_RE.match(line)
        if m:
            section = m.group(1).strip()
            continue
        kv = _KV_RE.match(line)
        if not kv:
            continue
        key = kv.group(1).strip()
        val = kv.group(2).strip()
        if (val.startswith('"') and val.endswith('"')) or (
            val.startswith("'") and val.endswith("'")
        ):
            val = val[1:-1]
        out[(section, key)] = (val, idx)
    return out


def _signature(kv: "OrderedDict[tuple[str | None, str], tuple[str, int]]") -> str:
    """클러스터 동일성 판단용 정규화 시그니처. 키 정렬 + 값만 비교."""
    normalized = sorted(
        ((s or "", k, v) for (s, k), (v, _ln) in kv.items())
    )
    payload = json.dumps(normalized, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _cluster_label(idx: int) -> str:
    """0->A, 1->B, ..., 25->Z, 26->AA, ..."""
    out = ""
    n = idx
    while True:
        out = chr(ord("A") + (n % 26)) + out
        n = n // 26 - 1
        if n < 0:
            return out


def _kv_diffs(
    left_kv: "OrderedDict[tuple[str | None, str], tuple[str, int]]",
    right_kv: "OrderedDict[tuple[str | None, str], tuple[str, int]]",
) -> list[Diff]:
    """두 키-값 맵 간 의미 단위 diff. 클러스터 대표 간 비교에 사용."""
    keys = list(dict.fromkeys(list(left_kv.keys()) + list(right_kv.keys())))
    diffs: list[Diff] = []
    for (section, key) in keys:
        lv = left_kv.get((section, key))
        rv = right_kv.get((section, key))
        if lv is None and rv is not None:
            diffs.append(
                Diff(
                    kind="added",
                    section=section,
                    key=key,
                    left_value=None,
                    right_value=rv[0],
                    left_line=None,
                    right_line=rv[1],
                    note=None,
                    severity="major",
                )
            )
        elif lv is not None and rv is None:
            diffs.append(
                Diff(
                    kind="removed",
                    section=section,
                    key=key,
                    left_value=lv[0],
                    right_value=None,
                    left_line=lv[1],
                    right_line=None,
                    note=None,
                    severity="major",
                )
            )
        elif lv is not None and rv is not None and lv[0] != rv[0]:
            diffs.append(
                Diff(
                    kind="changed",
                    section=section,
                    key=key,
                    left_value=lv[0],
                    right_value=rv[0],
                    left_line=lv[1],
                    right_line=rv[1],
                    note=None,
                    severity="minor",
                )
            )
    return diffs


def compute_clusters(recipes: list[RecipeInput]) -> ClusteringResult:
    """설비 클러스터링.

    1. 본문(analysis2_text)이 바이트 단위로 동일 → 같은 클러스터, body_hash_match=True.
    2. 본문이 달라도 키-값 시그니처가 동일 → 같은 클러스터.
    3. 그 외 → 별개 클러스터.
    """
    parsed = [parse_kv_with_lines(r.analysis2_text) for r in recipes]
    sigs = [_signature(p) for p in parsed]

    # 본문 바이트 동일 그룹은 별도로 추적 (시그니처와 함께 묶기)
    body_hashes = [hashlib.sha256(r.analysis2_text.encode("utf-8")).hexdigest() for r in recipes]

    by_sig: OrderedDict[str, list[int]] = OrderedDict()
    sig_body_match: dict[str, bool] = {}
    for i, sig in enumerate(sigs):
        by_sig.setdefault(sig, []).append(i)

    # 시그니처별로 본문 해시가 모두 같으면 body_hash_match=True
    for sig, idxs in by_sig.items():
        hashes = {body_hashes[i] for i in idxs}
        sig_body_match[sig] = len(hashes) == 1

    # 크기 큰 그룹 먼저
    groups = sorted(by_sig.items(), key=lambda x: (-len(x[1]), x[1][0]))
    if not groups:
        return ClusteringResult(clusters=[], pair_diffs=[])

    max_size = len(groups[0][1])
    clusters: list[Cluster] = []
    rep_kv_by_id: dict[str, "OrderedDict[tuple[str | None, str], tuple[str, int]]"] = {}
    for cid, (sig, idxs) in enumerate(groups):
        rids = sorted(recipes[i].recipe_id for i in idxs)
        label = _cluster_label(cid)
        clusters.append(
            Cluster(
                id=label,
                recipe_ids=rids,
                representative_recipe_id=rids[0],
                signature=sig,
                body_hash_match=sig_body_match[sig],
                is_majority=(len(rids) == max_size and len(rids) > 1),
            )
        )
        rep_kv_by_id[label] = parsed[idxs[0]]

    pair_diffs: list[ClusterPairDiff] = []
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            li = clusters[i].id
            rj = clusters[j].id
            pair_diffs.append(
                ClusterPairDiff(
                    left_cluster_id=li,
                    right_cluster_id=rj,
                    diffs=_kv_diffs(rep_kv_by_id[li], rep_kv_by_id[rj]),
                )
            )
    return ClusteringResult(clusters=clusters, pair_diffs=pair_diffs)


def compute_pivot(
    recipes: list[RecipeInput],
    include_identical: bool = False,
) -> PivotResult:
    """키별 분기 표.

    - 행: (section, key)
    - 열: 동일 값을 가진 설비 묶음 (`PivotBranch`)
    - 한 설비에서 해당 키가 누락되었으면 "(없음)" 값으로 묶임 (다른 설비와 별개 분기).
    - 분기 1개뿐인(=모두 동일한) 키는 기본 제외.
    """
    parsed = [parse_kv_with_lines(r.analysis2_text) for r in recipes]

    all_keys: list[tuple[str | None, str]] = []
    seen: set[tuple[str | None, str]] = set()
    for p in parsed:
        for k in p.keys():
            if k not in seen:
                seen.add(k)
                all_keys.append(k)

    entries: list[PivotEntry] = []
    for section, key in all_keys:
        value_to_rids: OrderedDict[str, list[int]] = OrderedDict()
        for r, p in zip(recipes, parsed):
            v = p.get((section, key))
            label = v[0] if v is not None else "(없음)"
            value_to_rids.setdefault(label, []).append(r.recipe_id)

        if not include_identical and len(value_to_rids) <= 1:
            continue

        ordered = sorted(value_to_rids.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        max_size = len(ordered[0][1])
        branches = [
            PivotBranch(
                value=val,
                recipe_ids=sorted(rids),
                is_majority=(len(rids) == max_size and len(rids) > 1),
            )
            for val, rids in ordered
        ]
        outlier = any(len(b.recipe_ids) == 1 for b in branches)
        entries.append(
            PivotEntry(
                section=section,
                key=key,
                branches=branches,
                is_outlier_present=outlier,
            )
        )

    # 정렬: 분기 수 ↓, 외톨이 보유 여부 ↑, 섹션·키 알파벳
    entries.sort(
        key=lambda e: (
            -len(e.branches),
            0 if e.is_outlier_present else 1,
            (e.section or "").lower(),
            e.key.lower(),
        )
    )
    return PivotResult(entries=entries)


def attach_clusters_and_pivot(req, result):
    """본체가 채우지 않은 부가 산출물을 폴백으로 채운다.

    `dataclasses.replace`로 새 CompareResult를 만들어 반환.
    호출자는 본 함수의 반환값을 그대로 사용해야 한다.
    """
    import dataclasses

    new_clusters = result.clusters or compute_clusters(req.recipes)
    new_pivot = result.pivot or compute_pivot(req.recipes)
    return dataclasses.replace(result, clusters=new_clusters, pivot=new_pivot)
