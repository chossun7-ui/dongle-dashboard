"""Recipe 라우터.

- GET /api/recipes              : 설비 id 다중 필터로 캐시 조회
- GET /api/recipes/{id}         : 단일 Recipe 본문/메타
- GET /api/recipes/{id}/snapshots : 변경 이력
- GET /api/recipes/search       : FTS5 풀텍스트 검색
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.envelope import ApiError, ok
from app.db.session import get_db

router = APIRouter(prefix="/api/recipes", tags=["recipes"])


def _csv_int_list(s: str | None) -> list[int]:
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip().isdigit()]


@router.get("")
def list_recipes(
    equipment_ids: str = Query(..., description="콤마 구분 설비 ID. 최소 1개."),
    db: Session = Depends(get_db),
):
    eids = _csv_int_list(equipment_ids)
    if not eids:
        raise ApiError("recipes.no_equipments", "설비 ID가 필요합니다.")
    placeholders = ",".join(f":e{i}" for i in range(len(eids)))
    rows = db.execute(
        text(
            f"""
            SELECT r.id, r.equipment_id, r.path, r.film_name, r.body_hash,
                   r.encoding_used, r.last_scanned_at, r.last_modified_at,
                   e.name AS equipment_name, l.name AS line_name, m.name AS model_name
            FROM recipes r
            JOIN equipments e ON e.id = r.equipment_id
            JOIN lines l ON l.id = e.line_id
            JOIN models m ON m.id = e.model_id
            WHERE r.equipment_id IN ({placeholders})
            ORDER BY l.name, m.name, e.name, r.path
            """
        ),
        {f"e{i}": v for i, v in enumerate(eids)},
    ).all()
    return ok(
        [
            {
                "id": r.id,
                "equipment_id": r.equipment_id,
                "equipment_name": r.equipment_name,
                "line_name": r.line_name,
                "model_name": r.model_name,
                "path": r.path,
                "film_name": r.film_name,
                "body_hash": r.body_hash,
                "encoding_used": r.encoding_used,
                "last_scanned_at": r.last_scanned_at,
                "last_modified_at": r.last_modified_at,
            }
            for r in rows
        ]
    )


@router.get("/{recipe_id}")
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    r = db.execute(
        text(
            """
            SELECT r.id, r.equipment_id, r.path, r.film_name, r.body_hash, r.body_text,
                   r.ini_text, r.encoding_used, r.last_scanned_at, r.last_modified_at,
                   e.name AS equipment_name, l.name AS line_name, m.name AS model_name
            FROM recipes r
            JOIN equipments e ON e.id = r.equipment_id
            JOIN lines l ON l.id = e.line_id
            JOIN models m ON m.id = e.model_id
            WHERE r.id = :rid
            """
        ),
        {"rid": recipe_id},
    ).first()
    if not r:
        raise ApiError("recipes.not_found", f"Recipe {recipe_id} 없음", 404)
    return ok(
        {
            "id": r.id,
            "equipment_id": r.equipment_id,
            "equipment_name": r.equipment_name,
            "line_name": r.line_name,
            "model_name": r.model_name,
            "path": r.path,
            "film_name": r.film_name,
            "body_hash": r.body_hash,
            "body_text": r.body_text,
            "ini_text": r.ini_text,
            "encoding_used": r.encoding_used,
            "last_scanned_at": r.last_scanned_at,
            "last_modified_at": r.last_modified_at,
        }
    )


@router.get("/{recipe_id}/snapshots")
def list_snapshots(recipe_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        text(
            "SELECT id, taken_at, body_hash FROM recipe_snapshots "
            "WHERE recipe_id = :r ORDER BY taken_at DESC"
        ),
        {"r": recipe_id},
    ).all()
    return ok([{"id": r.id, "taken_at": r.taken_at, "body_hash": r.body_hash} for r in rows])


@router.get("/search/fts")
def fts_search(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    """FTS5 풀텍스트 검색. SQL 인젝션은 파라미터 바인딩으로 차단."""
    rows = db.execute(
        text(
            """
            SELECT r.id, r.film_name, e.name AS equipment_name, l.name AS line_name,
                   m.name AS model_name, snippet(recipe_fts, 1, '<mark>', '</mark>', '…', 12) AS snip
            FROM recipe_fts
            JOIN recipes r ON r.id = recipe_fts.rowid
            JOIN equipments e ON e.id = r.equipment_id
            JOIN lines l ON l.id = e.line_id
            JOIN models m ON m.id = e.model_id
            WHERE recipe_fts MATCH :q
            ORDER BY rank
            LIMIT 200
            """
        ),
        {"q": q},
    ).all()
    return ok(
        [
            {
                "id": r.id,
                "film_name": r.film_name,
                "equipment_name": r.equipment_name,
                "line_name": r.line_name,
                "model_name": r.model_name,
                "snippet": r.snip,
            }
            for r in rows
        ]
    )
