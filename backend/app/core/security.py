"""인증·암호화 유틸리티.

- 관리자 비번: bcrypt 해시. 검증 함수 제공.
- FTP 비번: Fernet 대칭키 암호화. SQLite에는 암호문만 저장.

FERNET_KEY 환경변수가 비어 있으면 모듈 import 시점에 즉시 에러 — 평문 저장 사고 방지.
"""

from __future__ import annotations

import bcrypt
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import get_settings


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def _fernet() -> Fernet:
    key = get_settings().fernet_key
    if not key:
        raise RuntimeError(
            "FERNET_KEY가 설정되지 않았습니다. .env에서 FERNET_KEY를 지정하세요. "
            "생성: python -c \"from cryptography.fernet import Fernet; "
            'print(Fernet.generate_key().decode())"'
        )
    return Fernet(key.encode("utf-8") if isinstance(key, str) else key)


def encrypt_ftp_password(plain: str) -> str:
    return _fernet().encrypt(plain.encode("utf-8")).decode("utf-8")


def decrypt_ftp_password(token: str) -> str:
    try:
        return _fernet().decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise RuntimeError(
            "FTP 비번 복호화 실패. FERNET_KEY가 저장 시점과 다를 가능성."
        ) from e
