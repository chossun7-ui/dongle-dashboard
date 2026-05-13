"""즐겨찾기·프리셋 라우터.

- kind='recipe' : 개별 Recipe 즐겨찾기
- kind='group'  : 비교 그룹 (recipe_ids 배열)
- kind='preset' : 라인·모델·설비 다중선택 조합 프리셋
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.envelope import ApiError, ok
from app.db.session import get_db

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


class FavoriteIn(BaseModel):
    kind: str = Field(pattern=r"^(recipe|group|preset)$")
    label: str = Field(min_length=1, max_length=128)
    payload: dict


@router.get("")
def list_favorites(kind: str | None = Query(default=None), db: Session = Depends(get_db)):
    if kind:
        rows = db.execute(
            text("SELECT id, kind, label, payload_json, created_at FROM favorites WHERE kind = :k ORDER BY created_at DESC"),
            {"k": kind},
        ).all()
    else:
        rows = db.execute(
            text("SELECT id, kind, label, payload_json, created_at FROM favorites ORDER BY created_at DESC")
        ).all()
    return ok(
        [
            {
                "id": r.id,
                "kind": r.kind,
                "label": r.label,
                "payload": json.loads(r.payload_json),
                "created_at": r.created_at,
            }
            for r in rows
        ]
    )


@router.post("")
def create_favorite(body: FavoriteIn, db: Session = Depends(get_db)):
    db.execute(
        text(
            "INSERT INTO favorites (kind, label, payload_json) VALUES (:k, :l, :p)"
        ),
        {"k": body.kind, "l": body.label, "p": json.dumps(body.payload, ensure_ascii=False)},
    )
    db.commit()
    return ok()


@router.delete("/{fav_id}")
def delete_favorite(fav_id: int, db: Session = Depends(get_db)):
    db.execute(text("DELETE FROM favorites WHERE id = :i"), {"i": fav_id})
    db.commit()
    return ok()
