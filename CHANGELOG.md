# Changelog

이 파일은 본 저장소의 모든 변경사항을 사람이 읽기 쉬운 형식으로 기록한다. 최상단이 최신이다.
규칙: 한 줄 요약(날짜 · 요약 · 관련 파일/디렉토리). 사소한 오타 수정도 빠뜨리지 않는다.

## 2026-05-14

- 2026-05-14 · 비교 다이얼로그 본격 구현 — side-by-side / unified 토글, 좌우 동기 스크롤, 검색 하이라이트, 변경 점프(Alt+↑/↓), 사이드바 diff 목록, kind/severity 배지. · `frontend/src/components/CompareDialog.tsx`, `pages/Dashboard.tsx`
- 2026-05-14 · Export 백엔드 추가 — HTML/CSV/PDF. Jinja 템플릿 + WeasyPrint. CSV는 Excel용 BOM 포함. · `backend/app/api/export.py`, `docs/API.md`
- 2026-05-14 · FTP 전역설정 관리자 UI 추가 — 사용자명/비번(변경 시만 입력)/포트/모드/캐시 TTL/인코딩 우선순위/as 정규식. · `frontend/src/components/FtpConfigPanel.tsx`, `pages/Admin.tsx`
- 2026-05-14 · 변경 이력 시계열 뷰 추가 — Recipe별 current+스냅샷 시점 선택 좌우 비교. 백엔드는 단일 스냅샷 조회 엔드포인트 보강. · `frontend/src/components/HistoryDialog.tsx`, `backend/app/api/recipes.py`
- 2026-05-14 · FTS5 풀텍스트 검색 UI 추가 — Ctrl+K로 열고 결과 클릭 시 비교 대상에 추가. · `frontend/src/components/FtsSearch.tsx`
- 2026-05-14 · 즐겨찾기·프리셋 패널 추가 — preset(라인/모델/설비 다중선택 조합)·group(비교 Recipe 모음) 저장/적용/삭제. · `frontend/src/components/FavoritesPanel.tsx`
- 2026-05-14 · 파서·인코딩 유닛 테스트 9건 보강 (총 pytest 13 passed). · `backend/tests/test_parsers_and_encoding.py`

## 2026-05-13

- 2026-05-13 · Recipe Film Script 비교 대시보드로 저장소 전면 재구성. 기존 Dongle Trading 대시보드(`index.html`·구 `CLAUDE.md`·구 `CHANGELOG.md`)는 main 브랜치 및 git 히스토리에 보존. · `CLAUDE.md`, `CHANGELOG.md`, `README.md`, `.gitignore`
- 2026-05-13 · 프로젝트 디렉토리 골격 생성 (backend/app/{api,core,db,services,parsers,compare}, frontend/src/{components,pages,hooks,lib,types}, docs/). · 트리 구조
- 2026-05-13 · 비교 알고리즘 인터페이스 명세 작성 — 사내 AI가 본체를 작성할 때 충족해야 하는 입력/출력 타입·예제 포함. · `docs/COMPARE_ALGORITHM_SPEC.md`, `backend/app/compare/`
- 2026-05-13 · 백엔드 골격 추가 — FastAPI 진입점, SQLite 스키마(FTS5 포함), 단일 관리자 인증, FTP 비번 Fernet 암호화, FTP 스캐너 인터페이스. · `backend/app/`
- 2026-05-13 · 프론트엔드 골격 추가 — Vite+React+TS+Tailwind 셸, 로그인, 라인/모델/설비 다중선택 흐름의 스텁 페이지. · `frontend/`
- 2026-05-13 · Docker Compose 및 개발 워크플로 구성 — backend Uvicorn, frontend nginx 정적 서빙, SQLite·로그 볼륨. · `docker-compose.yml`, 각 Dockerfile
