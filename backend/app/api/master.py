"""라인·모델·설비 마스터 CRUD.

라인·모델은 독립 테이블. 설비는 (라인 1개 + 모델 1개)에 종속.
사용자 화면에서 라인·모델·설비 모두 다중선택 가능하므로, list 엔드포인트는
선택된 라인·모델 필터를 query param으로 받아 좁힐 수 있다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.api.envelope import ApiError, ok
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["master"])


# ─────────── Line ───────────

class LineIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)


@router.get("/lines")
def list_lines(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name FROM lines ORDER BY name")).all()
    return ok([{"id": r.id, "name": r.name} for r in rows])


@router.post("/lines")
def create_line(body: LineIn, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    try:
        db.execute(text("INSERT INTO lines (name) VALUES (:n)"), {"n": body.name})
        db.commit()
    except Exception:
        db.rollback()
        raise ApiError("line.duplicate", f"라인 '{body.name}'이(가) 이미 존재합니다.", 409)
    row = db.execute(text("SELECT id, name FROM lines WHERE name = :n"), {"n": body.name}).first()
    return ok({"id": row.id, "name": row.name})


@router.delete("/lines/{line_id}")
def delete_line(line_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    refs = db.execute(
        text("SELECT COUNT(*) AS c FROM equipments WHERE line_id = :i"), {"i": line_id}
    ).first()
    if refs and refs.c:
        raise ApiError(
            "line.in_use",
            f"이 라인을 참조하는 설비가 {refs.c}대 있습니다. 먼저 설비를 정리하세요.",
            409,
        )
    db.execute(text("DELETE FROM lines WHERE id = :i"), {"i": line_id})
    db.commit()
    return ok()


# ─────────── Model ───────────

class ModelIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT id, name FROM models ORDER BY name")).all()
    return ok([{"id": r.id, "name": r.name} for r in rows])


@router.post("/models")
def create_model(body: ModelIn, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    try:
        db.execute(text("INSERT INTO models (name) VALUES (:n)"), {"n": body.name})
        db.commit()
    except Exception:
        db.rollback()
        raise ApiError("model.duplicate", f"모델 '{body.name}'이(가) 이미 존재합니다.", 409)
    row = db.execute(text("SELECT id, name FROM models WHERE name = :n"), {"n": body.name}).first()
    return ok({"id": row.id, "name": row.name})


@router.delete("/models/{model_id}")
def delete_model(model_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    refs = db.execute(
        text("SELECT COUNT(*) AS c FROM equipments WHERE model_id = :i"), {"i": model_id}
    ).first()
    if refs and refs.c:
        raise ApiError(
            "model.in_use",
            f"이 모델을 참조하는 설비가 {refs.c}대 있습니다.",
            409,
        )
    db.execute(text("DELETE FROM models WHERE id = :i"), {"i": model_id})
    db.commit()
    return ok()


# ─────────── Equipment ───────────

class EquipmentIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    ip: str = Field(min_length=1, max_length=64)
    line_id: int
    model_id: int
    ftp_port: int | None = None
    ftp_mode: str | None = None
    encoding: str | None = None
    note: str | None = None


def _csv_int_list(s: str | None) -> list[int]:
    if not s:
        return []
    return [int(x) for x in s.split(",") if x.strip().isdigit()]


@router.get("/equipments")
def list_equipments(
    line_ids: str | None = Query(default=None, description="콤마 구분 라인 ID. 비면 전체."),
    model_ids: str | None = Query(default=None, description="콤마 구분 모델 ID. 비면 전체."),
    db: Session = Depends(get_db),
):
    lids = _csv_int_list(line_ids)
    mids = _csv_int_list(model_ids)

    where = []
    params: dict = {}
    if lids:
        placeholders = ",".join(f":l{i}" for i in range(len(lids)))
        where.append(f"e.line_id IN ({placeholders})")
        for i, v in enumerate(lids):
            params[f"l{i}"] = v
    if mids:
        placeholders = ",".join(f":m{i}" for i in range(len(mids)))
        where.append(f"e.model_id IN ({placeholders})")
        for i, v in enumerate(mids):
            params[f"m{i}"] = v

    sql = (
        "SELECT e.id, e.name, e.ip, e.line_id, l.name AS line_name, "
        "       e.model_id, m.name AS model_name, e.ftp_port, e.ftp_mode, e.encoding, e.note "
        "FROM equipments e "
        "JOIN lines l ON l.id = e.line_id "
        "JOIN models m ON m.id = e.model_id"
    )
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY l.name, m.name, e.name"
    rows = db.execute(text(sql), params).all()
    return ok(
        [
            {
                "id": r.id,
                "name": r.name,
                "ip": r.ip,
                "line_id": r.line_id,
                "line_name": r.line_name,
                "model_id": r.model_id,
                "model_name": r.model_name,
                "ftp_port": r.ftp_port,
                "ftp_mode": r.ftp_mode,
                "encoding": r.encoding,
                "note": r.note,
            }
            for r in rows
        ]
    )


@router.post("/equipments")
def create_equipment(body: EquipmentIn, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    try:
        db.execute(
            text(
                """
                INSERT INTO equipments
                    (name, ip, line_id, model_id, ftp_port, ftp_mode, encoding, note)
                VALUES (:n, :i, :l, :m, :p, :mo, :e, :no)
                """
            ),
            {
                "n": body.name,
                "i": body.ip,
                "l": body.line_id,
                "m": body.model_id,
                "p": body.ftp_port,
                "mo": body.ftp_mode,
                "e": body.encoding,
                "no": body.note,
            },
        )
        db.commit()
    except Exception as e:
        db.rollback()
        raise ApiError("equipment.invalid", f"설비 등록 실패: {e}", 400)
    return ok()


@router.delete("/equipments/{equipment_id}")
def delete_equipment(equipment_id: int, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    db.execute(text("DELETE FROM equipments WHERE id = :i"), {"i": equipment_id})
    db.commit()
    return ok()
