# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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
