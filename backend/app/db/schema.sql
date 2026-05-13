-- Recipe Film Script 비교 대시보드 스키마.
-- SQLite 3.35+ (FTS5 포함) 필요. 단일 파일 마이그레이션으로 시작; 변경은 마이그레이션 폴더 도입 후.

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

-- ───── 마스터 데이터 ─────

CREATE TABLE IF NOT EXISTS lines (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS models (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 설비는 (라인, 모델, 이름)으로 식별. 같은 이름의 설비가 다른 라인·모델에 있을 수 있어 (line_id, model_id, name) UNIQUE.
CREATE TABLE IF NOT EXISTS equipments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,                  -- 예: MTKB561
    ip          TEXT NOT NULL,                  -- 평문 FTP 호스트
    line_id     INTEGER NOT NULL REFERENCES lines(id) ON DELETE RESTRICT,
    model_id    INTEGER NOT NULL REFERENCES models(id) ON DELETE RESTRICT,
    ftp_port    INTEGER,                        -- NULL이면 ftp_config 기본값
    ftp_mode    TEXT,                           -- 'PASV' / 'ACTIVE' / NULL=기본
    encoding    TEXT,                           -- NULL이면 ftp_config 기본 폴백 사용
    note        TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE (name, line_id, model_id)
);

CREATE INDEX IF NOT EXISTS idx_equipments_line ON equipments(line_id);
CREATE INDEX IF NOT EXISTS idx_equipments_model ON equipments(model_id);

-- ───── 전역 FTP 설정 (싱글톤) ─────

CREATE TABLE IF NOT EXISTS ftp_config (
    id                INTEGER PRIMARY KEY CHECK (id = 1),
    username          TEXT NOT NULL,
    password_enc      TEXT NOT NULL,            -- Fernet 암호문
    default_port      INTEGER NOT NULL DEFAULT 21,
    default_mode      TEXT NOT NULL DEFAULT 'PASV',
    encoding_priority TEXT NOT NULL DEFAULT 'utf-8,cp949,auto',
    as_regex          TEXT NOT NULL DEFAULT '^as\d+$',
    cache_ttl_sec     INTEGER NOT NULL DEFAULT 0,   -- 0=수동만, 양수=자동 재스캔 주기
    updated_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ───── 관리자 ─────

CREATE TABLE IF NOT EXISTS admin (
    id             INTEGER PRIMARY KEY CHECK (id = 1),
    password_hash  TEXT NOT NULL,
    created_at     TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ───── Recipe 캐시 ─────

CREATE TABLE IF NOT EXISTS recipes (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id      INTEGER NOT NULL REFERENCES equipments(id) ON DELETE CASCADE,
    path              TEXT NOT NULL,            -- 설비 내 절대경로 (as 폴더 경로)
    film_name         TEXT,                     -- StrategyName. NULL일 수 있음 (파싱 실패 시).
    body_hash         TEXT NOT NULL,            -- analysis2_text의 sha256 (16진수)
    body_text         TEXT NOT NULL,            -- analysis2.txt 본문
    ini_text          TEXT,                     -- StrategyID.ini 본문
    encoding_used     TEXT,                     -- 실제 디코딩에 사용된 인코딩 (예: 'utf-8', 'cp949')
    last_scanned_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_modified_at  TEXT,                     -- FTP MDTM 값 (있으면)
    UNIQUE (equipment_id, path)
);

CREATE INDEX IF NOT EXISTS idx_recipes_film ON recipes(film_name);
CREATE INDEX IF NOT EXISTS idx_recipes_hash ON recipes(body_hash);

-- ───── 변경 이력 (시계열) ─────

CREATE TABLE IF NOT EXISTS recipe_snapshots (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id    INTEGER NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    taken_at     TEXT NOT NULL DEFAULT (datetime('now')),
    body_hash    TEXT NOT NULL,
    body_text    TEXT NOT NULL,
    ini_text     TEXT
);

CREATE INDEX IF NOT EXISTS idx_snapshots_recipe ON recipe_snapshots(recipe_id, taken_at DESC);

-- ───── 즐겨찾기·프리셋 ─────

CREATE TABLE IF NOT EXISTS favorites (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    kind         TEXT NOT NULL CHECK (kind IN ('recipe', 'group', 'preset')),
    label        TEXT NOT NULL,
    payload_json TEXT NOT NULL,                 -- 종류에 따른 페이로드 (recipe_ids 배열, 라인/모델/설비 선택 등)
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ───── 감사 로그 ─────

CREATE TABLE IF NOT EXISTS audit_log (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    actor        TEXT NOT NULL,                 -- 'admin' / 'system' / 'anonymous'
    action       TEXT NOT NULL,                 -- 'login', 'equipment.create', 'scan', 'compare', ...
    target       TEXT,
    payload_json TEXT,
    at           TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_audit_at ON audit_log(at DESC);

-- ───── FTS5 풀텍스트 검색 ─────
-- 권장: contentless FTS5 + 동기화 트리거.

CREATE VIRTUAL TABLE IF NOT EXISTS recipe_fts USING fts5(
    film_name,
    body_text,
    content='recipes',
    content_rowid='id',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS recipes_ai AFTER INSERT ON recipes BEGIN
    INSERT INTO recipe_fts(rowid, film_name, body_text)
    VALUES (new.id, coalesce(new.film_name, ''), new.body_text);
END;

CREATE TRIGGER IF NOT EXISTS recipes_ad AFTER DELETE ON recipes BEGIN
    INSERT INTO recipe_fts(recipe_fts, rowid, film_name, body_text)
    VALUES ('delete', old.id, coalesce(old.film_name, ''), old.body_text);
END;

CREATE TRIGGER IF NOT EXISTS recipes_au AFTER UPDATE ON recipes BEGIN
    INSERT INTO recipe_fts(recipe_fts, rowid, film_name, body_text)
    VALUES ('delete', old.id, coalesce(old.film_name, ''), old.body_text);
    INSERT INTO recipe_fts(rowid, film_name, body_text)
    VALUES (new.id, coalesce(new.film_name, ''), new.body_text);
END;
