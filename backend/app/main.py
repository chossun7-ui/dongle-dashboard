"""FastAPI 진입점.

부팅 시: DB 초기화 → 세션 시그너 준비 → 라우터 등록 → CORS.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from itsdangerous import URLSafeTimedSerializer

from app.api import auth, compare, favorites, ftp_config, master, recipes, scan
from app.api.envelope import ok
from app.core.config import get_settings
from app.db.session import init_engine


def create_app() -> FastAPI:
    settings = get_settings()
    logging.basicConfig(level=settings.log_level)

    app = FastAPI(title="Recipe Film Script Compare API", version="0.0.1")

    init_engine()
    app.state.session_serializer = URLSafeTimedSerializer(
        settings.session_secret, salt="rfc-admin-v1"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(auth.router)
    app.include_router(master.router)
    app.include_router(ftp_config.router)
    app.include_router(recipes.router)
    app.include_router(scan.router)
    app.include_router(compare.router)
    app.include_router(favorites.router)

    @app.get("/api/health")
    def health():
        return ok({"status": "ok"})

    return app


app = create_app()
