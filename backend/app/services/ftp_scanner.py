"""aioftp 기반 FTP 스캐너.

목표:
1. 설비(IP)에 평문 FTP 접속 (전역 자격증명).
2. 루트부터 디렉토리 트리를 워크.
3. 정규식(`^as\d+$` 기본)에 매칭되는 폴더 중 내부에 `analysis2.txt`와 `StrategyID.ini`가
   **둘 다** 있는 폴더를 Recipe로 채택.
4. 두 파일의 바이트를 읽어 인코딩 폴백 후 디코딩, 본문·해시·StrategyName 추출.
5. SQLite의 `recipes`에 upsert. 본문 해시가 바뀌었으면 `recipe_snapshots`에도 새 행.

본 모듈은 **인터페이스 + 더미 구현**으로 시작한다. 실제 FTP 세션은 사내 망에서만 검증 가능하므로,
초기 PoC에서는 호출만 되도록 두고, 실 적용 시 `_walk_remote` 구현을 채운다.

성능:
- 글로벌 세마포어로 동시 설비 수 제한.
- 설비당 세마포어로 한 설비 내 동시 다운로드 수 제한.
- 무거운 파싱은 호출자가 별도 스레드/프로세스로 위임.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

import aioftp
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decrypt_ftp_password
from app.parsers.strategy_ini import extract_strategy_name
from app.services.encoding import decode_bytes

_log = logging.getLogger(__name__)

ANALYSIS_FILE = "analysis2.txt"
STRATEGY_FILE = "StrategyID.ini"


@dataclass
class ScanProgress:
    equipment_id: int
    equipment_name: str
    started_at: str
    state: str = "pending"            # pending / running / done / error
    visited_dirs: int = 0
    recipes_found: int = 0
    recipes_upserted: int = 0
    snapshots_added: int = 0
    error: str | None = None
    finished_at: str | None = None


@dataclass
class _Creds:
    host: str
    port: int
    mode: str                          # 'PASV' or 'ACTIVE'
    username: str
    password: str
    encoding_priority: str
    as_regex: str
    force_encoding: str | None = None
    extras: dict = field(default_factory=dict)


def _load_creds_for_equipment(db: Session, equipment_id: int) -> _Creds:
    row = db.execute(
        text(
            """
            SELECT e.id, e.name, e.ip, e.ftp_port, e.ftp_mode, e.encoding,
                   f.username, f.password_enc, f.default_port, f.default_mode,
                   f.encoding_priority, f.as_regex
            FROM equipments e
            JOIN ftp_config f ON f.id = 1
            WHERE e.id = :eid
            """
        ),
        {"eid": equipment_id},
    ).first()
    if not row:
        raise LookupError(f"설비 {equipment_id} 또는 FTP 전역설정이 없습니다.")
    return _Creds(
        host=row.ip,
        port=int(row.ftp_port or row.default_port),
        mode=(row.ftp_mode or row.default_mode or "PASV").upper(),
        username=row.username,
        password=decrypt_ftp_password(row.password_enc),
        encoding_priority=row.encoding_priority,
        as_regex=row.as_regex,
        force_encoding=row.encoding,
    )


async def scan_equipment(db: Session, equipment_id: int) -> ScanProgress:
    """단일 설비를 스캔. 호출자는 동시성 제어 위해 세마포어로 감싸 호출."""
    settings = get_settings()
    creds = _load_creds_for_equipment(db, equipment_id)
    eq = db.execute(
        text("SELECT name FROM equipments WHERE id = :i"), {"i": equipment_id}
    ).first()
    progress = ScanProgress(
        equipment_id=equipment_id,
        equipment_name=eq.name if eq else f"#{equipment_id}",
        started_at=datetime.now(timezone.utc).isoformat(),
        state="running",
    )

    as_pat = re.compile(creds.as_regex)
    per_eq_sem = asyncio.Semaphore(settings.scan_workers_per_equipment)

    try:
        async with aioftp.Client.context(
            creds.host,
            creds.port,
            user=creds.username,
            password=creds.password,
        ) as client:
            async for recipe in _walk_remote(client, as_pat, progress, per_eq_sem):
                await _upsert_recipe(db, equipment_id, recipe, creds, progress)
        progress.state = "done"
    except asyncio.TimeoutError:
        progress.state = "error"
        progress.error = "FTP 타임아웃"
    except Exception as exc:  # pragma: no cover - defensive
        _log.exception("설비 %s 스캔 중 예외", progress.equipment_name)
        progress.state = "error"
        progress.error = f"{type(exc).__name__}: {exc}"
    finally:
        progress.finished_at = datetime.now(timezone.utc).isoformat()
    return progress


@dataclass
class _RemoteRecipe:
    path: str
    analysis_bytes: bytes
    strategy_bytes: bytes
    mdtm: str | None


async def _walk_remote(
    client: "aioftp.Client",
    as_pat: re.Pattern[str],
    progress: ScanProgress,
    per_eq_sem: asyncio.Semaphore,
):
    """원격 디렉토리 트리를 BFS로 워크. `as<숫자>` 폴더만 인식하여 두 파일이 모두 존재하면 yield.

    PoC 단계의 단순 구현. 실 운영 환경에서 디렉토리 구조에 맞춰 가지치기 보강 필요.
    """
    queue: list[str] = ["/"]
    visited: set[str] = set()
    while queue:
        cur = queue.pop(0)
        if cur in visited:
            continue
        visited.add(cur)
        progress.visited_dirs += 1
        try:
            entries = await client.list(cur)
        except Exception as e:  # pragma: no cover
            _log.warning("list 실패 %s: %s", cur, e)
            continue

        name_to_kind: dict[str, str] = {}
        for path, info in entries:
            name = str(path).rsplit("/", 1)[-1]
            kind = info.get("type", "")
            name_to_kind[name] = kind

        is_recipe_dir = (
            ANALYSIS_FILE in name_to_kind
            and STRATEGY_FILE in name_to_kind
            and as_pat.match(cur.rstrip("/").rsplit("/", 1)[-1] or "")
        )
        if is_recipe_dir:
            async with per_eq_sem:
                analysis = await _download(client, f"{cur.rstrip('/')}/{ANALYSIS_FILE}")
                strategy = await _download(client, f"{cur.rstrip('/')}/{STRATEGY_FILE}")
                mdtm = await _safe_mdtm(client, f"{cur.rstrip('/')}/{ANALYSIS_FILE}")
                progress.recipes_found += 1
                yield _RemoteRecipe(
                    path=cur.rstrip("/"),
                    analysis_bytes=analysis,
                    strategy_bytes=strategy,
                    mdtm=mdtm,
                )

        for name, kind in name_to_kind.items():
            if kind == "dir":
                queue.append(f"{cur.rstrip('/')}/{name}")


async def _download(client: "aioftp.Client", remote_path: str) -> bytes:
    chunks: list[bytes] = []
    async with client.download_stream(remote_path) as stream:
        async for chunk in stream.iter_by_block(64 * 1024):
            chunks.append(chunk)
    return b"".join(chunks)


async def _safe_mdtm(client: "aioftp.Client", remote_path: str) -> str | None:
    try:
        code, info = await client.command("MDTM " + remote_path, "213")
        # info: "20240501123456" 같은 포맷
        for line in info:
            digits = "".join(c for c in line if c.isdigit())
            if len(digits) >= 14:
                return digits[:14]
    except Exception:  # pragma: no cover
        return None
    return None


async def _upsert_recipe(
    db: Session,
    equipment_id: int,
    remote: _RemoteRecipe,
    creds: _Creds,
    progress: ScanProgress,
) -> None:
    analysis = decode_bytes(remote.analysis_bytes, creds.encoding_priority, creds.force_encoding)
    strategy = decode_bytes(remote.strategy_bytes, creds.encoding_priority, creds.force_encoding)
    film_name = extract_strategy_name(strategy.text)
    body_hash = hashlib.sha256(analysis.text.encode("utf-8")).hexdigest()

    existing = db.execute(
        text(
            "SELECT id, body_hash FROM recipes WHERE equipment_id = :e AND path = :p"
        ),
        {"e": equipment_id, "p": remote.path},
    ).first()

    if not existing:
        db.execute(
            text(
                """
                INSERT INTO recipes
                    (equipment_id, path, film_name, body_hash, body_text, ini_text,
                     encoding_used, last_modified_at)
                VALUES (:e, :p, :f, :h, :b, :i, :u, :m)
                """
            ),
            {
                "e": equipment_id,
                "p": remote.path,
                "f": film_name,
                "h": body_hash,
                "b": analysis.text,
                "i": strategy.text,
                "u": analysis.encoding_used,
                "m": remote.mdtm,
            },
        )
        progress.recipes_upserted += 1
    elif existing.body_hash != body_hash:
        # 본문 변경 — 기존 행을 갱신하고 이전 본문을 스냅샷으로 보존
        db.execute(
            text(
                """
                INSERT INTO recipe_snapshots (recipe_id, body_hash, body_text, ini_text)
                SELECT id, body_hash, body_text, ini_text FROM recipes WHERE id = :rid
                """
            ),
            {"rid": existing.id},
        )
        progress.snapshots_added += 1
        db.execute(
            text(
                """
                UPDATE recipes
                SET film_name = :f, body_hash = :h, body_text = :b, ini_text = :i,
                    encoding_used = :u, last_modified_at = :m,
                    last_scanned_at = datetime('now')
                WHERE id = :rid
                """
            ),
            {
                "f": film_name,
                "h": body_hash,
                "b": analysis.text,
                "i": strategy.text,
                "u": analysis.encoding_used,
                "m": remote.mdtm,
                "rid": existing.id,
            },
        )
        progress.recipes_upserted += 1
    else:
        db.execute(
            text("UPDATE recipes SET last_scanned_at = datetime('now') WHERE id = :rid"),
            {"rid": existing.id},
        )
    db.commit()
