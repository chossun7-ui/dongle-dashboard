"""관리자 인증 라우터.

- POST /api/auth/login          : 비번 확인 후 세션 쿠키 발급
- POST /api/auth/logout         : 세션 종료
- GET  /api/auth/me             : 현재 세션 상태

세션은 itsdangerous 시그닝(쿠키에 isadmin=1을 서명해 저장). 단일 관리자이므로 user id 개념 불필요.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.envelope import ApiError, ok
from app.core.security import verify_password
from app.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])

SESSION_COOKIE = "rfc_admin"


class LoginBody(BaseModel):
    password: str


@router.post("/login")
def login(body: LoginBody, request: Request, response: Response, db: Session = Depends(get_db)):
    row = db.execute(text("SELECT password_hash FROM admin WHERE id = 1")).first()
    if not row or not verify_password(body.password, row.password_hash):
        raise ApiError("auth.invalid_password", "비밀번호가 올바르지 않습니다.", 401)
    serializer = request.app.state.session_serializer
    response.set_cookie(
        SESSION_COOKIE,
        serializer.dumps({"role": "admin"}),
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return ok({"role": "admin"})


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)
    return ok()


@router.get("/me")
def me(request: Request):
    return ok({"is_admin": _is_admin(request)})


def require_admin(request: Request) -> None:
    if not _is_admin(request):
        raise ApiError("auth.required", "관리자 인증이 필요합니다.", 401)


def _is_admin(request: Request) -> bool:
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie:
        return False
    try:
        data = request.app.state.session_serializer.loads(cookie, max_age=60 * 60 * 8)
    except Exception:
        return False
    return data.get("role") == "admin"
