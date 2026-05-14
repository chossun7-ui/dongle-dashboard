# API 가이드

응답은 모두 envelope을 따른다.

```json
{ "ok": true, "data": ... }
{ "ok": false, "error": { "code": "...", "message": "..." } }
```

## 인증 (관리자 페이지에만 필요)

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/auth/login` | `{password}` → 세션 쿠키 발급 |
| POST | `/api/auth/logout` | 세션 종료 |
| GET  | `/api/auth/me` | `{is_admin}` 조회 |

## 마스터

| Method | Path | 권한 |
|---|---|---|
| GET    | `/api/lines` | 모두 |
| POST   | `/api/lines` | 관리자 |
| DELETE | `/api/lines/{id}` | 관리자 |
| GET    | `/api/models` | 모두 |
| POST   | `/api/models` | 관리자 |
| DELETE | `/api/models/{id}` | 관리자 |
| GET    | `/api/equipments?line_ids=&model_ids=` | 모두 |
| POST   | `/api/equipments` | 관리자 |
| DELETE | `/api/equipments/{id}` | 관리자 |

## FTP 전역 설정 (관리자 전용)

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/ftp-config` | 비번 제외 조회 |
| PUT | `/api/ftp-config` | 등록/갱신. password가 빈 문자열이면 기존 유지 |

## Recipe

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/recipes?equipment_ids=1,2,3` | 캐시된 Recipe 목록 |
| GET | `/api/recipes/{id}` | 본문/메타 |
| GET | `/api/recipes/{id}/snapshots` | 변경 이력 (current 가상 항목 + 과거 스냅샷) |
| GET | `/api/recipes/{id}/snapshots/{snap_id}` | 특정 시점 본문. `snap_id='current'`면 현재 |
| GET | `/api/recipes/search/fts?q=...` | FTS5 풀텍스트 검색 |

## 스캔

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/scan` | `{equipment_ids: [...]}` → 백그라운드 잡 등록 |
| GET  | `/api/scan/jobs` | 잡 목록 |
| GET  | `/api/scan/jobs/{job_id}` | 잡 상세 진행상황 |

## 비교

| Method | Path | 설명 |
|---|---|---|
| POST | `/api/compare` | `{recipe_ids: [...], options: {...}}` → CompareResult |

비교 본체는 `docs/COMPARE_ALGORITHM_SPEC.md` 참조.

## Export

비교를 실행하여 결과를 파일로 내려준다.

| Method | Path | 응답 |
|---|---|---|
| POST | `/api/export/html` | `text/html` (단일 파일, self-contained) |
| POST | `/api/export/csv`  | `text/csv` (Excel용 BOM 포함) |
| POST | `/api/export/pdf`  | `application/pdf` (WeasyPrint) |

요청 본문은 `/api/compare`와 동일: `{recipe_ids, options}`.

## 즐겨찾기

| Method | Path | 설명 |
|---|---|---|
| GET    | `/api/favorites?kind=preset` | 종류별 목록 |
| POST   | `/api/favorites` | `{kind, label, payload}` |
| DELETE | `/api/favorites/{id}` | 삭제 |

## 헬스 체크

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/health` | `{status: "ok"}` |
