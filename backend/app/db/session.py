"""SQLite 세션 관리 및 부트스트랩.

초기 부팅 시:
1. DB 파일 디렉토리 생성
2. schema.sql 적용 (멱등)
3. admin 비번 부트스트랩 (테이블 비어 있을 때만 ADMIN_PASSWORD로 해시 저장)
4. ftp_config 싱글톤 부트스트랩 (없으면 빈 자리 잡아두기 — 관리자 첫 설정 전까지 None)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.security import encrypt_ftp_password, hash_password

_log = logging.getLogger(__name__)

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _ensure_sqlite_pragmas(dbapi_conn, _) -> None:
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.execute("PRAGMA journal_mode = WAL")
    cursor.execute("PRAGMA synchronous = NORMAL")
    cursor.close()


def init_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is not None:
        return _engine
    settings = get_settings()
    db_path = Path(settings.sqlite_path).absolute()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(
        settings.sqlite_url,
        future=True,
        connect_args={"check_same_thread": False},
    )
    event.listen(_engine, "connect", _ensure_sqlite_pragmas)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False, future=True)
    _apply_schema(_engine)
    _bootstrap(_engine)
    return _engine


def _apply_schema(engine: Engine) -> None:
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")
    with engine.begin() as conn:
        for stmt in _split_statements(sql):
            if stmt.strip():
                conn.exec_driver_sql(stmt)


def _split_statements(sql: str) -> list[str]:
    """SQLite는 한 번에 여러 statement 실행을 지원하지 않으므로 분할.

    트리거의 BEGIN ... END 블록을 보존하기 위해 단순 ';' 분할이 아닌
    트리거 감지가 필요. 간단한 상태 머신으로 처리.
    """
    out: list[str] = []
    buf: list[str] = []
    in_trigger = False
    for raw_line in sql.splitlines():
        line = raw_line
        stripped = line.strip().upper()
        if stripped.startswith("CREATE TRIGGER") or stripped.startswith(
            "CREATE TEMP TRIGGER"
        ):
            in_trigger = True
        buf.append(line)
        if in_trigger:
            if stripped == "END;" or stripped.endswith(" END;"):
                out.append("\n".join(buf))
                buf = []
                in_trigger = False
        else:
            if line.rstrip().endswith(";"):
                out.append("\n".join(buf))
                buf = []
    if buf:
        out.append("\n".join(buf))
    return out


def _bootstrap(engine: Engine) -> None:
    settings = get_settings()
    with engine.begin() as conn:
        # 관리자 부트스트랩
        row = conn.execute(text("SELECT 1 FROM admin WHERE id = 1")).first()
        if not row:
            conn.execute(
                text(
                    "INSERT INTO admin (id, password_hash) VALUES (1, :h)"
                ),
                {"h": hash_password(settings.admin_password)},
            )
            _log.info("관리자 계정 부트스트랩 완료 (ADMIN_PASSWORD).")

        # ftp_config 자리는 첫 관리자 설정 전까지 비워둔다 (필수 컬럼이라 더미 행을 만들지는 않는다).
        # 관리자 UI에서 처음 저장할 때 INSERT한다.


def get_db() -> Iterator[Session]:
    assert _SessionLocal is not None, "init_engine()을 먼저 호출해야 합니다."
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_demo_ftp_config_if_empty(username: str, password_plain: str) -> None:
    """개발 편의용: ftp_config가 비어 있으면 더미 자격증명을 채워 넣는다.

    운영에서는 호출하지 않는다. 테스트·로컬 개발에서만 사용.
    """
    assert _SessionLocal is not None
    with _SessionLocal() as db:
        exists = db.execute(text("SELECT 1 FROM ftp_config WHERE id = 1")).first()
        if exists:
            return
        db.execute(
            text(
                "INSERT INTO ftp_config (id, username, password_enc) "
                "VALUES (1, :u, :p)"
            ),
            {"u": username, "p": encrypt_ftp_password(password_plain)},
        )
        db.commit()
