"""모든 API 응답이 따르는 단일 envelope.

`{"ok": True, "data": ...}` / `{"ok": False, "error": {"code", "message"}}`.
프론트엔드 `src/lib/api.ts`도 동일 envelope를 가정한다.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException
from fastapi.responses import JSONResponse


def ok(data: Any = None) -> dict[str, Any]:
    return {"ok": True, "data": data}


def fail(code: str, message: str, status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={"ok": False, "error": {"code": code, "message": message}},
    )


class ApiError(HTTPException):
    def __init__(self, code: str, message: str, status: int = 400):
        super().__init__(status_code=status, detail={"code": code, "message": message})
