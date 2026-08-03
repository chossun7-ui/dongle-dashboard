# Changelog

이 파일은 본 저장소의 모든 변경사항을 사람이 읽기 쉬운 형식으로 기록한다. 최상단이 최신이다.
규칙: 한 줄 요약(날짜 · 요약 · 관련 파일/디렉토리). 사소한 오타 수정도 빠뜨리지 않는다.

## 2026-08-03

- 2026-08-03 · 테스트 커버리지 분석 중 생성되는 pytest-cov 산출물(`.coverage`, `htmlcov/`)을 gitignore에 추가. 분석 결과: 전체 32% — compare/clustering/parsers는 92~100%, API 라우터 8종·ftp_scanner·core·db/session은 0%, 프론트엔드는 테스트 러너 부재. 개선 우선순위는 (1) `_upsert_recipe` 스냅샷 로직, (2) TestClient 기반 라우터 통합 테스트. · `.gitignore`

## 2026-05-15

- 2026-05-15 · N-way 비교 가독성 산출물 추가 (schema 1.0 → 1.1). 설비별로 본문이 동일하거나 키-값 시그니처가 같은 그룹을 K개 Cluster로 압축하여 K(K-1)/2 페어만 보여준다. 본체가 비워둔 경우 라우터가 폴백으로 채운다. · `backend/app/compare/types.py`, `clustering.py`, `interface.py`, `__init__.py`
- 2026-05-15 · CompareDialog에 탭 4개 통합 — [clusters][pivot][side-by-side][unified]. N≥3이면 clusters를 기본 탭으로. · `frontend/src/components/CompareDialog.tsx`
- 2026-05-15 · ClusterView 추가 — 클러스터 카드(라인·모델 그루핑 칩, 다수/외톨이 배지) + 두 클러스터 선택 시 의미 단위 diff 표. · `frontend/src/components/ClusterView.tsx`
- 2026-05-15 · PivotView 추가 — 키별 분기를 한 행으로(다수/외톨이 색상 구분, "없음" 분기 별도, 라인·모델별 칩 그루핑, 외톨이 보유 키 필터, 검색). · `frontend/src/components/PivotView.tsx`
- 2026-05-15 · 클러스터링·피벗 단위 테스트 7건 추가 (총 pytest 20 passed). · `backend/tests/test_clustering.py`
- 2026-05-15 · 비교 알고리즘 명세 문서를 1.1로 보강 — Cluster/Pivot 타입과 권장 규칙 추가. · `docs/COMPARE_ALGORITHM_SPEC.md`

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
