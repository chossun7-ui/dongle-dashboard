"""FTP 전역 설정 라우터.

전역 단일 행. 관리자만 변경 가능. 비번은 응답에서 절대 노출하지 않는다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.auth import require_admin
from app.api.envelope import ok
from app.core.security import encrypt_ftp_password
from app.db.session import get_db

router = APIRouter(prefix="/api/ftp-config", tags=["ftp-config"])


class FtpConfigIn(BaseModel):
    username: str = Field(min_length=1)
    password: str | None = None              # None이면 기존 비번 유지
    default_port: int = 21
    default_mode: str = Field(default="PASV", pattern=r"^(PASV|ACTIVE)$")
    encoding_priority: str = "utf-8,cp949,auto"
    as_regex: str = r"^as\d+$"
    cache_ttl_sec: int = 0


@router.get("")
def get_config(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    row = db.execute(
        text(
            "SELECT username, default_port, default_mode, encoding_priority, as_regex, cache_ttl_sec "
            "FROM ftp_config WHERE id = 1"
        )
    ).first()
    if not row:
        return ok(None)
    return ok(
        {
            "username": row.username,
            "default_port": row.default_port,
            "default_mode": row.default_mode,
            "encoding_priority": row.encoding_priority,
            "as_regex": row.as_regex,
            "cache_ttl_sec": row.cache_ttl_sec,
            "password_set": True,
        }
    )


@router.put("")
def upsert_config(body: FtpConfigIn, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    existing = db.execute(text("SELECT 1 FROM ftp_config WHERE id = 1")).first()
    if not existing:
        if not body.password:
            return ok({"error": "최초 등록 시 비밀번호 필수"})
        db.execute(
            text(
                """
                INSERT INTO ftp_config
                    (id, username, password_enc, default_port, default_mode,
                     encoding_priority, as_regex, cache_ttl_sec)
                VALUES (1, :u, :p, :pt, :m, :ep, :ar, :tt)
                """
            ),
            {
                "u": body.username,
                "p": encrypt_ftp_password(body.password),
                "pt": body.default_port,
                "m": body.default_mode,
                "ep": body.encoding_priority,
                "ar": body.as_regex,
                "tt": body.cache_ttl_sec,
            },
        )
    else:
        # 비번이 비어 있으면 password_enc 유지
        if body.password:
            db.execute(
                text("UPDATE ftp_config SET password_enc = :p WHERE id = 1"),
                {"p": encrypt_ftp_password(body.password)},
            )
        db.execute(
            text(
                """
                UPDATE ftp_config SET
                    username = :u, default_port = :pt, default_mode = :m,
                    encoding_priority = :ep, as_regex = :ar,
                    cache_ttl_sec = :tt, updated_at = datetime('now')
                WHERE id = 1
                """
            ),
            {
                "u": body.username,
                "pt": body.default_port,
                "m": body.default_mode,
                "ep": body.encoding_priority,
                "ar": body.as_regex,
                "tt": body.cache_ttl_sec,
            },
        )
    db.commit()
    return ok()
