"""비교 라우터.

- POST /api/compare      : recipe_ids 배열 + options → CompareResult JSON

비교 본체는 CPU 바운드이므로 ProcessPoolExecutor에 위임.
사내 AI 본체가 추가되기 전에는 stub이 응답한다.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.envelope import ApiError, ok
from app.compare import (
    CompareOptions,
    CompareRequest,
    RecipeInput,
    compare_recipes,
)
from app.db.session import get_db

router = APIRouter(prefix="/api/compare", tags=["compare"])

# 비교 워커 풀. 프로세스 풀은 fork-safe해야 함 (compare는 순수 함수이므로 OK).
_EXEC = ProcessPoolExecutor(max_workers=2)


class CompareBody(BaseModel):
    recipe_ids: list[int]
    options: dict[str, Any] | None = None


def _build_options(raw: dict[str, Any] | None) -> CompareOptions:
    if not raw:
        return CompareOptions()
    return CompareOptions(**{k: v for k, v in raw.items() if k in CompareOptions.__dataclass_fields__})


def _load_recipe_inputs(db: Session, recipe_ids: list[int]) -> list[RecipeInput]:
    placeholders = ",".join(f":r{i}" for i in range(len(recipe_ids)))
    rows = db.execute(
        text(
            f"""
            SELECT r.id, r.path, r.film_name, r.body_text, r.ini_text,
                   e.name AS eq_name, l.name AS line_name, m.name AS model_name
            FROM recipes r
            JOIN equipments e ON e.id = r.equipment_id
            JOIN lines l ON l.id = e.line_id
            JOIN models m ON m.id = e.model_id
            WHERE r.id IN ({placeholders})
            """
        ),
        {f"r{i}": v for i, v in enumerate(recipe_ids)},
    ).all()
    by_id = {r.id: r for r in rows}
    out: list[RecipeInput] = []
    for rid in recipe_ids:
        r = by_id.get(rid)
        if not r:
            raise ApiError("compare.recipe_missing", f"Recipe {rid} 없음", 404)
        out.append(
            RecipeInput(
                recipe_id=r.id,
                equipment_name=r.eq_name,
                line_name=r.line_name,
                model_name=r.model_name,
                path=r.path,
                film_name=r.film_name or "",
                analysis2_text=r.body_text,
                strategy_ini_text=r.ini_text or "",
            )
        )
    return out


@router.post("")
async def do_compare(body: CompareBody, db: Session = Depends(get_db)):
    if len(body.recipe_ids) < 2:
        raise ApiError("compare.too_few", "최소 2개 Recipe가 필요합니다.")
    inputs = _load_recipe_inputs(db, body.recipe_ids)
    req = CompareRequest(recipes=inputs, options=_build_options(body.options))

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(_EXEC, compare_recipes, req)
    return ok(asdict(result))
