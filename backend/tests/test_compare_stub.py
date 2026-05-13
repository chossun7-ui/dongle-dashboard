"""compare 인터페이스 + stub의 계약 테스트.

사내 AI가 algorithm.py를 추가하기 전까지 stub이 인터페이스를 충족함을 보장.
algorithm.py가 추가되면 동일 테스트를 통과해야 한다 (계약 테스트).
"""

from __future__ import annotations

from app.compare import (
    CompareOptions,
    CompareRequest,
    RecipeInput,
    SCHEMA_VERSION,
    compare_recipes,
)


def _r(rid: int, text: str, name: str = "FilmX") -> RecipeInput:
    return RecipeInput(
        recipe_id=rid,
        equipment_name=f"EQ{rid}",
        line_name="P1",
        model_name="IRIS",
        path=f"/path/as{rid}",
        film_name=name,
        analysis2_text=text,
        strategy_ini_text=f"[Strategy]\nStrategyName={name}\n",
    )


def test_identical_recipes_marked_same():
    body = "A=1\nB=2\n"
    req = CompareRequest(recipes=[_r(1, body), _r(2, body)], options=CompareOptions())
    res = compare_recipes(req)
    assert res.schema_version == SCHEMA_VERSION
    assert len(res.pairs) == 1
    assert res.pairs[0].same is True
    assert res.summary.pairs_identical == 1


def test_differing_recipes_produce_diffs():
    req = CompareRequest(
        recipes=[_r(1, "A=1\n"), _r(2, "A=2\n")],
        options=CompareOptions(),
    )
    res = compare_recipes(req)
    assert res.pairs[0].same is False
    assert res.summary.pairs_with_diffs == 1
    assert res.summary.total_diffs >= 1


def test_baseline_mode_yields_n_minus_one_pairs():
    req = CompareRequest(
        recipes=[_r(1, "A"), _r(2, "B"), _r(3, "C")],
        options=CompareOptions(mode="baseline"),
    )
    res = compare_recipes(req)
    assert len(res.pairs) == 2
    assert all(p.left_recipe_id == 1 for p in res.pairs)


def test_pairwise_mode_yields_all_combinations():
    req = CompareRequest(
        recipes=[_r(1, "A"), _r(2, "B"), _r(3, "C")],
        options=CompareOptions(mode="pairwise"),
    )
    res = compare_recipes(req)
    assert len(res.pairs) == 3  # C(3,2)
