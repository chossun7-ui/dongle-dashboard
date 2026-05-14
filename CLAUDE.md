# CLAUDE.md

이 파일은 Claude Code(또는 후속 AI 에이전트)가 본 저장소에서 작업할 때 **세션 시작 시 가장 먼저 읽어야 하는** 안내서이다. 본 저장소는 과거 `Dongle Trading Investor Dashboard`(단일 `index.html`)였으나, 2026-05-13부로 **Recipe Film Script 비교 대시보드** 프로젝트로 완전히 교체되었다. 과거 코드는 `main` 브랜치 또는 `7cde709..548d9b9` 커밋 범위에서 확인 가능하다.

---

## 프로젝트 규칙 (Project Rules — MUST READ FIRST)

다음 규칙은 사용자가 명시적으로 지정한 작업 규약이다. 모든 후속 에이전트는 매 세션 시작 시 이 섹션을 먼저 읽고 반드시 준수한다.

1. **언어**: 사용자에게 답변할 때는 **한국어**로 응답한다. 코드, 커밋 메시지, 식별자, 영문 기술 용어는 그대로 두되, 설명·요약·진행상황 보고는 한국어로 한다.
2. **변경 이력 기록**: 모든 변경사항은 두 곳에 남긴다 — (a) `git commit` (코드 차원의 진실), (b) `CHANGELOG.md`의 최상단에 사람이 읽을 한 줄 요약 (날짜·요약·관련 파일). 사소한 오타 수정도 빠뜨리지 않는다.
3. **연관 문서 동기화**: 코드/구조/데이터 스키마/규칙이 바뀌면 즉시 관련 문서(`CLAUDE.md`, `CHANGELOG.md`, `README.md`, `docs/*`)를 같은 커밋에서 함께 업데이트한다. "코드만 바꾸고 문서는 나중에"는 금지.
4. **인계 가능한 상세도**: 코드·문서 작성 시 다음 에이전트가 컨텍스트 없이 곧바로 이어서 작업할 수 있도록 충분히 상세하게 설명한다. 비자명한 결정·제약·사이드이펙트가 있는 지점에는 주석을 적극 활용한다 (단, 식별자만 봐도 자명한 곳에 잡음 주석을 달지는 않는다 — `WHY`를 적는다).
5. **대화 전체 참조**: 한 세션 안에서는 사용자가 처음부터 지금까지 말한 모든 내용을 잊지 말고 참조한다. 이전 지시·선호·제약과 충돌하는 행동을 하지 않는다. 세션을 넘어가는 영구 규칙은 이 `CLAUDE.md`에 반영하여 다음 세션에서도 이어지게 한다.
6. **작업 후 1차 검증**: 변경 작업이 끝나면 즉시 검증한다. 검증 수단은 작업 성격에 따라 선택 — `git status` / `git diff`로 의도한 변경만 반영됐는지, 백엔드면 `pytest` 또는 `uvicorn` 부팅 확인, 프론트엔드면 `npm run build` / `npm run dev` 후 브라우저(또는 헤드리스) 점검.
7. **2차 누락 검증**: 1차 검증 후, 빠뜨린 항목이 없는지 한 번 더 점검한다. 체크리스트:
   - 코드 변경에 따른 문서 업데이트가 빠지지 않았는가? (`CLAUDE.md`, `CHANGELOG.md`, `docs/*`)
   - DB 스키마 변경 시 마이그레이션·인덱스·FTS5 트리거가 일관되게 반영됐는가?
   - 라인·모델·설비 다중선택 흐름이 모든 화면에서 일관되게 동작하는가?
   - 한국어 UI 문자열이 영어로 바뀌어 있지는 않은가?
   - 다크/라이트 테마 양쪽 모두에서 정상인가? (테마 도입 시)
   - 비교 알고리즘 인터페이스 시그니처(`docs/COMPARE_ALGORITHM_SPEC.md`)와 코드(`backend/app/compare/interface.py`)가 동기화되어 있는가?
   - 커밋·푸시까지 완료됐는가? 브랜치는 `claude/init-project-9oUfV`가 맞는가?
8. **비교 알고리즘 본체는 사내 AI가 작성**: `backend/app/compare/` 의 핵심 비교 로직(`compare_recipes()` 본체)은 사용자의 사내 AI가 실제 `analysis2.txt`·`StrategyID.ini` 샘플을 받아 별도로 작성한다. 본 저장소에는 **인터페이스(타입·시그니처·예제·기대 출력)** 만 견고하게 정의해두고, 본체는 더미 구현(`stub.py`)으로 채워 두어 사내 AI가 인터페이스 충족하도록 작성하면 그대로 끼워 넣을 수 있게 한다. 인터페이스를 임의로 바꾸지 않는다. 부득이 변경 시 `docs/COMPARE_ALGORITHM_SPEC.md`를 같은 커밋에서 함께 업데이트한다.

---

## 프로젝트 한 줄 정의

반도체/디스플레이 라인의 설비별 **Film Script(공정 레시피)** 를 FTP로 원격 수집·캐싱하고, **같은 Film 이름끼리 자동 페어링하여 차이를 시각화**하는 사내 웹 대시보드.

## 핵심 도메인 개념

- **Line (라인)**: 생산라인. 예: `P1`, `P2`. 복수 선택 가능.
- **Model (모델)**: 라인에서 생산하는 제품 모델. 예: `IRIS`, `ATLAS`. 복수 선택 가능. **라인과 독립** — 같은 모델이 여러 라인에 있을 수 있음.
- **Equipment (설비)**: 실제 장비. 예: `MTKB561`, `MTKB562`. 라인+모델 조합에 속함. 한 설비는 하나의 IP를 가지고, 그 안에 다수의 Recipe가 들어 있음.
- **Recipe (레시피)**: 설비 내부 `as<숫자>` 폴더 하나. 정확히 두 개의 파일을 가짐:
  - `analysis2.txt` — Film Script 본문 (구조화된 섹션·키-값·블록 형식)
  - `StrategyID.ini` — 메타데이터. `StrategyName=` 키에 Film 이름이 들어 있음
- **Film (필름)**: `StrategyName` 값. 같은 Film 이름을 가진 Recipe가 여러 설비에 흩어져 있고, 이들을 비교하는 것이 이 도구의 본질.

## 디렉토리 구조

```
.
├── CLAUDE.md                # 이 파일
├── CHANGELOG.md             # 변경 이력 (최상단이 최신)
├── README.md                # 사용자/운영자용 안내
├── docker-compose.yml       # 운영 배포
├── .env.example             # 환경 변수 예시
├── backend/                 # FastAPI + asyncio + aioftp
│   ├── pyproject.toml
│   ├── Dockerfile
│   └── app/
│       ├── main.py
│       ├── core/            # config, security, password crypto
│       ├── db/              # SQLAlchemy models, schema, session
│       ├── api/             # FastAPI routers: auth, master, ftp_config, recipes,
│       │                    #                   scan, compare, export, favorites
│       ├── services/        # ftp_scanner, encoding
│       ├── parsers/         # analysis2.txt, StrategyID.ini 파서
│       └── compare/         # ★ 비교 알고리즘 (인터페이스 + stub — 본체는 사내 AI)
├── frontend/                # React + Vite + TS + Tailwind
│   ├── package.json
│   ├── Dockerfile
│   └── src/
│       ├── pages/           # Dashboard, Admin, Login
│       ├── components/      # MultiSelect, CompareDialog, HistoryDialog,
│       │                    #   FtsSearch, FavoritesPanel, FtpConfigPanel
│       ├── lib/             # api (envelope)
│       ├── hooks/           # useUrlState
│       └── types/
└── docs/
    ├── COMPARE_ALGORITHM_SPEC.md   # ★★ 사내 AI 인계 명세
    ├── API.md
    ├── SETUP.md
    └── DATA_MODEL.md
```

## 기술 스택 (확정)

| 영역 | 선택 | 비고 |
|---|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn, asyncio, aioftp | 평문 FTP (FTPS 아님) |
| DB | SQLite (단일 파일) + FTS5 | 풀텍스트 검색 위해 FTS5 필수 |
| ORM/마이그레이션 | SQLAlchemy 2.x + Alembic (또는 raw schema 단일파일) | 초기엔 단일 SQL 파일로 시작 |
| 인증 | 단일 관리자 비번 (bcrypt 해시) | 일반 사용자에겐 인증 없음 — 사내망 내부용 |
| FTP 비번 저장 | Fernet 대칭키 암호화 (key는 환경변수) | 평문 저장 금지 |
| Frontend | React 18, Vite 5, TypeScript, Tailwind CSS 3 | |
| UI 컴포넌트 | shadcn/ui 스타일(직접 구현, 의존성 최소) | 무거운 UI 라이브러리 회피 |
| Diff 뷰 | `diff` (npm) + 자체 렌더링 | side-by-side, unified 토글 |
| 배포 | Docker Compose (backend + frontend nginx + 볼륨) | systemd 옵션도 README에 안내 |
| OS | Linux | |
| 차트 (선택) | Chart.js or Recharts | 변경 이력 시계열용 |

## 데이터 모델 (요약 — 상세는 `docs/DATA_MODEL.md`)

```
lines        (id, name UNIQUE, created_at)
models       (id, name UNIQUE, created_at)
equipments   (id, name UNIQUE, ip, line_id FK, model_id FK, ftp_port, ftp_mode, created_at)
                                              ※ 라인·모델은 다대다가 아니라, 설비 단위로 (line, model) 한 쌍을 가짐
                                              ※ 복수 라인·모델에 같은 설비명이 있을 수 있다면 (name, line, model) UNIQUE
ftp_config   (id=1 싱글톤, username, password_enc, default_port, default_mode, encoding_priority)
recipes      (id, equipment_id FK, path, film_name, body_hash, body_text, ini_text,
              last_scanned_at, last_modified_at)   ※ path는 설비 내 절대경로 (예: /A/B/as42)
                                                    UNIQUE(equipment_id, path)
recipe_snapshots (id, recipe_id FK, taken_at, body_hash, body_text, ini_text)
                                                    ※ 변경 감지 시에만 새 행 추가 (body_hash 다를 때)
favorites    (id, kind ENUM('recipe','group','preset'), payload_json, label, created_at)
admin        (id=1, password_hash, created_at, updated_at)
audit_log    (id, actor, action, target, payload_json, at)
recipe_fts   (FTS5 virtual table on recipes.body_text, recipes.film_name)
```

## 핵심 흐름

### 사용자 흐름
1. 로그인(관리자 인증은 관리자 페이지 진입 시에만; 일반 페이지는 사내망 가정).
2. 사이드바에서 **Line 다중선택** → **Model 다중선택** → **Equipment 다중선택** (순차적으로 후보가 좁혀짐).
3. "스캔" 클릭. 캐시 우선 조회 → 캐시에 있으면 즉시 트리 표시, 없으면 백그라운드 FTP 스캔 진행 + 진행 상태 표시.
4. 스캔 결과 트리에서 비교 대상 Recipe를 좌·우(또는 N개) 선택 → "비교".
5. **Film 이름 자동 페어링** 결과를 1차로 보여주고, 사용자가 그룹 조정(추가·제거·재매칭) 후 "확정".
6. 비교 다이얼로그 열림 — side-by-side / unified 토글, 자체 스크롤, 좌우 동기, 변경 점프(`Alt+↑/↓`), 검색 하이라이트, Export.
7. 결과는 SQLite에 변경 이력 스냅샷으로 저장(body_hash 다를 때만).

### 관리자 흐름
- `/admin` 진입 시 비번 인증.
- **Line CRUD**, **Model CRUD** (둘은 독립 테이블).
- **Equipment CRUD**: 이름·IP 입력 + Line 1개·Model 1개 선택.
- **FTP 전역 설정**: 계정·비번·기본 포트·기본 모드(PASV/ACTIVE)·인코딩 우선순위.
- **as 정규식 설정**: 기본 `^as\d+$` (대소문자 구분, 엄격).
- **병렬화 파라미터**: 글로벌 worker 수, 설비당 FTP 동시 연결, asyncio 세마포어, 스캔 타임아웃.
- **캐시 TTL**: 0이면 무한(수동 재스캔 only). 양수이면 그 시간 후 자동 재스캔 트리거.
- **관리자 비번 변경**.

## 규약 (Conventions)

- 코드 식별자는 영문/스네이크/카멜 표준대로. UI 문자열만 한국어.
- 백엔드는 ASGI 단일 프로세스 + asyncio 동시성. CPU 바운드(파서·diff)는 `run_in_executor`로 ProcessPoolExecutor 위임.
- 평문 비밀번호는 **어디에도** 저장·로그·응답하지 않는다 (`pydantic.SecretStr` + Fernet).
- FastAPI 라우터는 `app/api/<도메인>.py`로 분리하고 `app/main.py`에서 include.
- DB 세션은 dependency injection (`Depends(get_db)`)으로 주입.
- 프론트엔드 API 호출은 `src/lib/api.ts`로 일원화. 직접 fetch 금지.
- 다중선택 상태는 URL query string에 동기화(`?lines=P1,P2&models=IRIS&equipments=MTKB561,MTKB562`) — 새로고침에도 유지.
- 빈 응답·에러는 일관된 envelope: `{ ok: bool, data, error?: { code, message } }`.

## as 폴더 매칭 규칙

- 정규식: `^as\d+$` (대소문자 구분, 엄격).
- `AS1`, `as001`, `as1b`, `as-1`, `as1_old` 등은 **모두 제외**.
- 디렉토리 트리 워크 시 `as42` 안에 또 `as99`가 있어도 양쪽 모두 `StrategyID.ini`가 존재하면 별개 Recipe로 카운트. 자식·부모 관계는 별도로 표시하지 않음(현재 결정).
- 사용자가 향후 정규식을 바꾸고 싶다면 관리자 탭에서 설정 가능.

## 인코딩 폴백

순서: UTF-8 → CP949 → chardet 자동 감지. 모두 실패 시 errors=`replace`로 디코딩하고 경고 플래그. 관리자가 특정 설비에 한해 강제 지정 가능.

## 캐시 전략

- 설비 선택 시 `recipes` 테이블에서 우선 조회 → 화면 즉시 표시.
- "재스캔" 버튼으로 사용자가 명시적으로 트리거.
- 자동 재스캔은 캐시 TTL 양수일 때만(기본 0 = 비활성). 재스캔 결과 본문 해시(`body_hash`)가 달라지면 `recipe_snapshots`에 새 행을 추가하여 시계열 변경 이력 형성.

## Git / Branch

- 작업 브랜치: **`claude/init-project-9oUfV`** (모든 새 작업은 여기 위에).
- `main` 브랜치: 옛 Dongle Trading 대시보드 보존. 새 프로젝트가 안정화되면 별도 결정으로 교체.
- 푸시: `git push -u origin claude/init-project-9oUfV`. 네트워크 실패 시 2s·4s·8s·16s 백오프 재시도.
- PR은 사용자가 명시적으로 요청할 때만 생성.

## 검증·테스트

- 백엔드: `pytest backend/tests`. 핵심은 파서·캐시·인코딩 폴백.
- 프론트엔드: 정적 타입 검사(`tsc --noEmit`)와 `npm run build`로 1차 검증. 통합 테스트는 후속 작업.
- 비교 알고리즘은 사내 AI가 제공한 본체로 교체 후 사용자가 실제 샘플로 검증.

## 자주 묻는 의문에 대한 답 (Anti-FAQ)

- Q. 왜 FTPS가 아니라 평문 FTP인가? — 사내 폐쇄망 + 설비 펌웨어 제약. 사용자가 평문 FTP를 명시적으로 지정.
- Q. 왜 SQLite인가? — 사내 단일 서버, 동시 사용자 소수, 운영 단순성. PostgreSQL은 과잉.
- Q. 왜 비교 알고리즘을 stub으로 두는가? — 사용자의 사내 AI가 실제 샘플 파일을 받아 직접 작성한다(규칙 8 참조). 본 저장소에서는 인터페이스를 견고히 정의하는 것이 책무.
- Q. 왜 다중선택이 다단계인가? — 라인·모델·설비는 N×M×K 카디널리티. 처음부터 설비 단일 리스트로 펼치면 너무 길어진다. 단계적 좁힘이 실제 사용 동선.
