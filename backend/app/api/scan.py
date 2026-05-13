"""스캔 트리거 라우터.

- POST /api/scan                : 설비 ID 다중 → 백그라운드 FTP 스캔 작업 등록
- GET  /api/scan/jobs           : 진행 중·완료 작업 목록
- GET  /api/scan/jobs/{job_id}  : 상세 진행 상황

스캔 작업은 메모리 딕셔너리에 보관(단일 프로세스 가정).
멀티 프로세스로 확장하면 Redis 또는 SQLite 잡 테이블로 옮긴다.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import asdict

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.auth import _is_admin
from app.api.envelope import ApiError, ok
from app.core.config import get_settings
from app.db.session import get_db
from app.services.ftp_scanner import ScanProgress, scan_equipment

_log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/scan", tags=["scan"])

# job_id -> ScanProgress 리스트(설비당 1개)
_JOBS: dict[str, list[ScanProgress]] = {}


class ScanBody(BaseModel):
    equipment_ids: list[int]


@router.post("")
def trigger_scan(
    body: ScanBody,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # 누구나 스캔 트리거 가능하지만 관리자 액션은 audit_log에 표시
    if not body.equipment_ids:
        raise ApiError("scan.no_equipments", "최소 1개 설비를 지정하세요.")
    job_id = uuid.uuid4().hex
    _JOBS[job_id] = []
    background.add_task(_run_job, job_id, body.equipment_ids, _is_admin(request))
    return ok({"job_id": job_id, "equipment_ids": body.equipment_ids})


@router.get("/jobs")
def list_jobs():
    return ok(
        [
            {
                "job_id": jid,
                "equipments": [asdict(p) for p in progs],
            }
            for jid, progs in _JOBS.items()
        ]
    )


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    progs = _JOBS.get(job_id)
    if progs is None:
        raise ApiError("scan.job_not_found", f"잡 {job_id} 없음", 404)
    return ok({"job_id": job_id, "equipments": [asdict(p) for p in progs]})


async def _run_job(job_id: str, equipment_ids: list[int], is_admin: bool) -> None:
    from app.db.session import _SessionLocal  # late import to avoid cycle

    assert _SessionLocal is not None
    settings = get_settings()
    sem = asyncio.Semaphore(settings.scan_workers_global)

    async def run_one(eid: int) -> None:
        async with sem:
            with _SessionLocal() as db:
                try:
                    prog = await asyncio.wait_for(
                        scan_equipment(db, eid), timeout=settings.scan_timeout_sec * 60
                    )
                except asyncio.TimeoutError:
                    prog = ScanProgress(
                        equipment_id=eid,
                        equipment_name=f"#{eid}",
                        started_at="",
                        state="error",
                        error="잡 타임아웃",
                    )
                _JOBS[job_id].append(prog)

    await asyncio.gather(*(run_one(eid) for eid in equipment_ids))
