"""클러스터링·피벗 단위 테스트.

설비가 많을수록 가독성이 떨어지는 N-way 비교의 보조 산출물.
- 같은 본문 → 같은 클러스터 (body_hash_match=True)
- 본문 다르지만 키-값 시그니처 동일 → 같은 클러스터 (body_hash_match=False)
- 본문·시그니처 모두 다름 → 별개 클러스터
"""

from app.compare import CompareOptions, CompareRequest, RecipeInput, compare_recipes
from app.compare.clustering import compute_clusters, compute_pivot


def _r(rid: int, text: str, eq: str = "EQ", line: str = "P1", model: str = "IRIS") -> RecipeInput:
    return RecipeInput(
        recipe_id=rid,
        equipment_name=f"{eq}{rid}",
        line_name=line,
        model_name=model,
        path=f"/Film/as{rid}",
        film_name="FilmX",
        analysis2_text=text,
        strategy_ini_text="[Strategy]\nStrategyName=FilmX\n",
    )


BASE = """[General]
Power=1500
Pressure=120
Gas=Ar

[Step1]
Time=30
Temperature=250
"""

P2_VARIANT = """[General]
Power=1600
Pressure=120
Gas=N2

[Step1]
Time=30
Temperature=255

[Step2]
Time=10
"""

OUTLIER = """[General]
Power=1500
Pressure=125
Gas=Ar

[Step1]
Time=30
Temperature=250
"""


def test_identical_bodies_form_single_cluster():
    recipes = [_r(i, BASE, "MTKB", "P1") for i in (561, 562, 567, 568)]
    cr = compute_clusters(recipes)
    assert len(cr.clusters) == 1
    c = cr.clusters[0]
    assert c.recipe_ids == [561, 562, 567, 568]
    assert c.body_hash_match is True
    assert c.is_majority is True


def test_three_groups_emerge_by_signature():
    recipes = (
        [_r(i, BASE, "MTKB", "P1") for i in (561, 562, 567, 568)]
        + [_r(i, P2_VARIANT, "MTKB", "P2") for i in (563, 564, 565)]
        + [_r(566, OUTLIER, "MTKB", "P1")]
    )
    cr = compute_clusters(recipes)
    sizes = sorted([len(c.recipe_ids) for c in cr.clusters], reverse=True)
    assert sizes == [4, 3, 1]
    a, b, c = cr.clusters
    assert a.id == "A" and a.is_majority is True
    assert c.id == "C" and c.is_majority is False  # 외톨이
    # K(K-1)/2 == 3 페어
    assert len(cr.pair_diffs) == 3


def test_outlier_cluster_size_one():
    recipes = [_r(i, BASE, "MTKB", "P1") for i in (1, 2, 3)] + [_r(4, OUTLIER, "MTKB", "P1")]
    cr = compute_clusters(recipes)
    sizes = sorted([len(c.recipe_ids) for c in cr.clusters], reverse=True)
    assert sizes == [3, 1]
    outlier = [c for c in cr.clusters if len(c.recipe_ids) == 1][0]
    assert outlier.is_majority is False


def test_pivot_excludes_identical_keys_by_default():
    recipes = [_r(i, BASE) for i in (1, 2, 3)]
    pv = compute_pivot(recipes, include_identical=False)
    # 모두 동일하면 분기가 없으므로 entries 비어 있어야 함
    assert pv.entries == []


def test_pivot_emerges_with_branches_and_majority_first():
    recipes = (
        [_r(i, BASE) for i in (1, 2, 3, 4)]                # 4대 동일
        + [_r(i, P2_VARIANT) for i in (5, 6)]              # 2대 변형
        + [_r(7, OUTLIER)]                                  # 1대 외톨이 Pressure
    )
    pv = compute_pivot(recipes)
    keys = [(e.section, e.key) for e in pv.entries]
    # Power, Pressure, Gas, Temperature, Step2.Time 가 분기. (대문자 키)
    assert ("General", "Power") in keys
    assert ("General", "Pressure") in keys
    assert ("General", "Gas") in keys
    assert ("Step1", "Temperature") in keys
    assert ("Step2", "Time") in keys

    pressure = next(e for e in pv.entries if (e.section, e.key) == ("General", "Pressure"))
    # 120 다수 (1,2,3,4,5,6), 125 외톨이 (7)
    assert pressure.branches[0].value == "120"
    assert pressure.branches[0].is_majority is True
    assert pressure.branches[1].value == "125"
    assert pressure.branches[1].recipe_ids == [7]
    assert pressure.is_outlier_present is True


def test_missing_key_becomes_separate_branch():
    """Step2가 일부 설비에만 있을 때 '없음' 분기로 묶인다."""
    recipes = [_r(i, BASE) for i in (1, 2, 3)] + [_r(4, P2_VARIANT)]
    pv = compute_pivot(recipes)
    step2 = next(e for e in pv.entries if (e.section, e.key) == ("Step2", "Time"))
    none_branch = next(b for b in step2.branches if b.value == "(없음)")
    has_branch = next(b for b in step2.branches if b.value == "10")
    assert none_branch.recipe_ids == [1, 2, 3]
    assert has_branch.recipe_ids == [4]


def test_compare_recipes_attaches_clusters_and_pivot():
    """compare_recipes() 진입점이 clusters/pivot을 자동 보강해야 한다."""
    recipes = [_r(i, BASE) for i in (1, 2)] + [_r(3, P2_VARIANT)]
    res = compare_recipes(CompareRequest(recipes=recipes, options=CompareOptions()))
    assert res.clusters is not None
    assert res.pivot is not None
    assert len(res.clusters.clusters) == 2
    assert res.schema_version == "1.1"
