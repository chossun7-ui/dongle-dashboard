# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 규칙 (Project Rules — MUST READ FIRST)

다음 규칙은 사용자가 명시적으로 지정한 작업 규약이다. 모든 후속 에이전트는 매 세션 시작 시 이 섹션을 먼저 읽고 반드시 준수한다.

1. **언어**: 사용자에게 답변할 때는 **한국어**로 응답한다. 코드, 커밋 메시지, 문서의 영문 식별자/기술 용어는 그대로 두되, 설명·요약·진행상황 보고는 한국어로 한다.
2. **변경 이력 기록**: 모든 변경사항은 두 곳에 남긴다 — (a) `git commit` (코드 차원의 진실), (b) `CHANGELOG.md`의 최상단에 사람이 읽을 한 줄 요약 (날짜·요약·관련 파일). 사소한 오타 수정도 빠뜨리지 않는다.
3. **연관 문서 동기화**: 코드/구조/데이터 스키마/규칙이 바뀌면 즉시 관련 문서(`CLAUDE.md`, `CHANGELOG.md`, 향후 추가될 README 등)를 같은 커밋에서 함께 업데이트한다. "코드만 바꾸고 문서는 나중에"는 금지.
4. **인계 가능한 상세도**: 코드·문서 작성 시 다음 에이전트가 컨텍스트 없이 곧바로 이어서 작업할 수 있도록 충분히 상세하게 설명한다. 비자명한 결정·제약·사이드이펙트가 있는 지점에는 주석을 적극 활용한다 (단, 식별자만 봐도 자명한 곳에 잡음 주석을 달지는 않는다 — `WHY`를 적는다).
5. **대화 전체 참조**: 한 세션 안에서는 사용자가 처음부터 지금까지 말한 모든 내용을 잊지 말고 참조한다. 이전 지시·선호·제약과 충돌하는 행동을 하지 않는다. 세션을 넘어가는 영구 규칙은 이 `CLAUDE.md`에 반영하여 다음 세션에서도 이어지게 한다.
6. **작업 후 1차 검증**: 변경 작업이 끝나면 즉시 검증한다. 검증 수단은 작업 성격에 따라 선택 — `git status` / `git diff`로 의도한 변경만 반영됐는지, 정적 사이트라면 `index.html`을 브라우저(또는 헤드리스)로 열어 콘솔 에러·렌더링 확인, 데이터 스키마 변경 시 `transformEmbeddedData()` 경로와 라이브 API 경로 둘 다 점검.
7. **2차 누락 검증**: 1차 검증 후, 빠뜨린 항목이 없는지 한 번 더 점검한다. 체크리스트:
   - 코드 변경에 따른 문서 업데이트가 빠지지 않았는가? (`CLAUDE.md`, `CHANGELOG.md`)
   - 세 프로파일(`conservative`/`aggressive`/`ultra`) 모두에 일관되게 반영됐는가?
   - 라이브 API 응답과 임베디드 스냅샷(`window.__DONGLE_EMBEDDED_DATA__`) 두 데이터 경로 모두 깨지지 않았는가?
   - 한국어 UI 문자열이 영어로 바뀌어 있지는 않은가?
   - 다크/라이트 테마 양쪽 모두에서 정상인가?
   - 커밋·푸시까지 완료됐는가? 브랜치는 `claude/init-project-9oUfV`가 맞는가?

## Repository Shape

The entire project is a single self-contained file: `index.html` (~1.7K lines, ~200KB). There is no build system, no package manager, no test suite, and no server-side code in this repo. Everything — HTML structure, CSS theming, embedded data snapshot, and dashboard logic — lives in `index.html`.

To preview locally: open `index.html` directly in a browser, or serve the directory with any static server (e.g. `python3 -m http.server`).

## What This Dashboard Is

`index.html` renders the investor-facing dashboard for **Dongle Trading v15.0**, a crypto futures trading engine that runs three parallel risk profiles on Binance Futures Testnet:

- `conservative` — 2% risk, 5x leverage
- `aggressive`   — 3% risk, 5x leverage
- `ultra`        — 5% risk, 5x leverage

The UI is in **Korean**. Keep new copy in Korean unless told otherwise.

The page exposes four tabs (see `<nav class="tab-nav">` near line 663):

1. 실시간 모니터 — live KPIs, per-profile cards, equity curve, open positions
2. 트레이드 로그 — closed-trade table with per-profile filter
3. 백테스트 레퍼런스 — v15 backtest stats, equity curve, P&L distribution, per-symbol wins/losses
4. 엔진 로그 — engine log viewer with per-profile filter

## Data Flow (Important)

The dashboard has a **dual-source data model** — read both branches before changing data handling:

1. **Live mode**: `fetchDashboard()` (around line ~980) calls `GET /api/dashboard`; `fetchLogs()` calls `GET /api/logs`. These endpoints are served by a backend that is **not in this repo**. When reachable, the response is used directly and the status badge shows `TESTNET LIVE`.

2. **Static / snapshot mode**: when the API fetch fails, the code falls back to `window.__DONGLE_EMBEDDED_DATA__`, a large JSON blob inlined into the page (the first `<script>` tag right after `</style>`, around line ~613). The status badge then shows `SNAPSHOT`. Logs are not available in this mode.

The two shapes are **different**: the embedded snapshot has `live[]` (an array keyed by profile `name`) plus a `backtest` object, while the live API returns the shape the UI consumes directly (`profiles{}` object keyed by profile name, plus `backtest_ref`). The bridge is `transformEmbeddedData(raw)` (around line ~905) — any change to the embedded snapshot schema, the live API schema, or the field names the UI reads must keep these three in sync.

Auto-refresh runs every 30s via `setInterval`; the "Updated Xs ago" label ticks every 1s.

## Conventions to Preserve

- **Three-profile assumption is hard-coded** in many places (`['conservative', 'aggressive', 'ultra']` loops, `PROFILE_COLORS`, `PROFILE_LABELS`, KPI aggregation, tab filter buttons). Adding/removing a profile means updating all of them.
- Profile colors are fixed: conservative = teal `#4fcfb4`, aggressive = orange `#f5a623`, ultra = red `#ef5350`. The same palette is reused for equity-curve datasets, profile cards, and log tags.
- **Theme**: `data-theme="dark"` (default) and `data-theme="light"` are toggled on `<html>`; CSS variables under `:root` and the two `[data-theme=...]` blocks drive all colors. The toggle handler destroys and re-creates all Chart.js charts so they pick up new axis/grid colors — preserve this when adding new charts.
- Charts use **Chart.js 4.4.7** + `chartjs-adapter-date-fns` loaded from jsDelivr CDN. There is no bundler — keep new dependencies as CDN `<script>` tags or inline them.
- KPI/PnL color classes: `.profit` (green/teal), `.loss` (red), `.neutral` (gray). Apply them by setting `el.className = 'kpi-value ' + (val > 0 ? 'profit' : val < 0 ? 'loss' : 'neutral')`.
- The page is wrapped in an IIFE (`(function(){ 'use strict'; ... })()`) — module-level state (`dashboardData`, `logData`, chart instances, filter selections) lives there. Don't leak globals.

## Git / Branch

Development for this repo happens on branch `claude/init-project-9oUfV` (per project instructions). The `main` branch holds the deployed snapshot.
