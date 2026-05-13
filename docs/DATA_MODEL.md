# 데이터 모델

본 문서는 `backend/app/db/schema.sql`과 1:1 동기화된다. 스키마 변경 시 본 문서도 같은 커밋에서 갱신.

## ER 요약

```
lines      ──┐
              ├───< equipments ───< recipes ───< recipe_snapshots
models     ──┘
ftp_config (singleton)
admin      (singleton)
favorites  (kind: recipe|group|preset)
audit_log
recipe_fts (FTS5 virtual)
```

## 핵심 결정 사항

- **라인·모델은 독립** 테이블. 다대다가 아니라 설비 단위로 (line, model) 한 쌍을 가짐.
- 설비 식별자: `(name, line_id, model_id)` UNIQUE. 같은 설비명이 다른 라인·모델에 있을 수 있음.
- Recipe 식별자: `(equipment_id, path)` UNIQUE. `path`는 설비 내 절대경로(예: `/Film List/as42`).
- 본문 변경 감지: `body_hash`(sha256). 변경 시 기존 본문을 `recipe_snapshots`로 옮긴다.
- FTS5 인덱스는 `recipe_fts`. AFTER INSERT/UPDATE/DELETE 트리거로 자동 동기화.
- `ftp_config.password_enc`은 Fernet 대칭키 암호문. 평문 저장 금지.

## 인덱스 정책

- `idx_recipes_film` — Film 이름 기준 페어링 시 lookup.
- `idx_recipes_hash` — 본문 해시 기반 중복 탐지.
- `idx_snapshots_recipe(recipe_id, taken_at DESC)` — 시계열 조회.
- `idx_audit_at(at DESC)` — 최근 활동 표시.

## 마이그레이션 정책

PoC 단계에서는 `schema.sql` 단일 파일에 `CREATE TABLE IF NOT EXISTS`로 멱등 적용. 컬럼 추가/제거가 필요해지면 `backend/app/db/migrations/<번호>_<설명>.sql` 폴더 도입 후 부팅 시 순서대로 적용한다 (alembic 도입은 그 시점에 결정).
