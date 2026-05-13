# Changelog

이 파일은 본 저장소의 모든 변경사항을 사람이 읽기 쉬운 형식으로 기록한다. 최상단이 최신이다.
규칙: 한 줄 요약(날짜 · 요약 · 관련 파일/디렉토리). 사소한 오타 수정도 빠뜨리지 않는다.

## 2026-05-13

- 2026-05-13 · Recipe Film Script 비교 대시보드로 저장소 전면 재구성. 기존 Dongle Trading 대시보드(`index.html`·구 `CLAUDE.md`·구 `CHANGELOG.md`)는 main 브랜치 및 git 히스토리에 보존. · `CLAUDE.md`, `CHANGELOG.md`, `README.md`, `.gitignore`
- 2026-05-13 · 프로젝트 디렉토리 골격 생성 (backend/app/{api,core,db,services,parsers,compare}, frontend/src/{components,pages,hooks,lib,types}, docs/). · 트리 구조
- 2026-05-13 · 비교 알고리즘 인터페이스 명세 작성 — 사내 AI가 본체를 작성할 때 충족해야 하는 입력/출력 타입·예제 포함. · `docs/COMPARE_ALGORITHM_SPEC.md`, `backend/app/compare/`
- 2026-05-13 · 백엔드 골격 추가 — FastAPI 진입점, SQLite 스키마(FTS5 포함), 단일 관리자 인증, FTP 비번 Fernet 암호화, FTP 스캐너 인터페이스. · `backend/app/`
- 2026-05-13 · 프론트엔드 골격 추가 — Vite+React+TS+Tailwind 셸, 로그인, 라인/모델/설비 다중선택 흐름의 스텁 페이지. · `frontend/`
- 2026-05-13 · Docker Compose 및 개발 워크플로 구성 — backend Uvicorn, frontend nginx 정적 서빙, SQLite·로그 볼륨. · `docker-compose.yml`, 각 Dockerfile
