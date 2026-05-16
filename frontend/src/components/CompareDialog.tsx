import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import { ClusterView } from "@/components/ClusterView";
import { PivotView } from "@/components/PivotView";
import type { CompareResult, ComparePair, Diff } from "@/types";

interface Props {
  recipeIds: number[];
  open: boolean;
  onClose: () => void;
}

type ViewMode = "clusters" | "pivot" | "side" | "unified";

/**
 * 비교 다이얼로그.
 *
 * 특징:
 * - 자체 스크롤 (모달 본문이 화면을 점령하지 않음)
 * - side-by-side / unified 토글
 * - 좌우 동기 스크롤 (side-by-side에서)
 * - 검색 하이라이트
 * - 변경 점프 (Alt+↑ / Alt+↓)
 * - Export 메뉴 (HTML / CSV / PDF)
 *
 * 백엔드 compare 응답이 algorithm.py 본체로 교체되면 자동으로 더 정밀한 의미 단위
 * diff가 표시된다. 본 컴포넌트는 stub의 라인 단위 결과와 본체의 의미 단위 결과 모두를
 * 동일한 UI로 보여줄 수 있도록 설계되어 있다.
 */
export function CompareDialog({ recipeIds, open, onClose }: Props) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<CompareResult | null>(null);
  // N≥3이면 clusters를 기본 탭으로, N=2이면 pair(side-by-side)를 기본으로.
  const [mode, setMode] = useState<ViewMode>(
    recipeIds.length >= 3 ? "clusters" : "side"
  );
  const [search, setSearch] = useState("");
  const [activePair, setActivePair] = useState(0);

  useEffect(() => {
    if (!open || recipeIds.length < 2) return;
    setLoading(true);
    setError(null);
    setResult(null);
    setMode(recipeIds.length >= 3 ? "clusters" : "side");
    api
      .post<CompareResult>("/api/compare", { recipe_ids: recipeIds, options: {} })
      .then((r) => setResult(r))
      .catch((e) => setError((e as Error).message))
      .finally(() => setLoading(false));
  }, [open, recipeIds.join(",")]);

  if (!open) return null;

  const pair: ComparePair | undefined = result?.pairs[activePair];

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/70"
      role="dialog"
      aria-modal="true"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-[95vw] h-[90vh] max-w-[1600px] flex flex-col rounded-xl border border-slate-800 bg-slate-950">
        <CompareHeader
          result={result}
          loading={loading}
          mode={mode}
          setMode={setMode}
          search={search}
          setSearch={setSearch}
          recipeIds={recipeIds}
          activePair={activePair}
          setActivePair={setActivePair}
          onClose={onClose}
        />

        {error && (
          <div className="px-4 py-3 bg-rose-900/40 text-rose-200 text-sm">{error}</div>
        )}

        {loading && (
          <div className="flex-1 grid place-items-center text-slate-400 text-sm">
            비교 중...
          </div>
        )}

        {!loading && result && (
          <div className="flex-1 min-h-0 flex flex-col px-3 pb-3">
            {/* clusters / pivot 탭은 전체 폭으로 */}
            {mode === "clusters" && result.clusters && (
              <ClusterView clusters={result.clusters} inputs={result.inputs} />
            )}
            {mode === "pivot" && result.pivot && (
              <PivotView pivot={result.pivot} inputs={result.inputs} />
            )}
            {(mode === "side" || mode === "unified") && pair && (
              <div className="flex-1 min-h-0 grid grid-cols-12 gap-2">
                <DiffSidebar
                  pair={pair}
                  search={search}
                  onJump={(d) => scrollToLine(d.left_line, d.right_line)}
                />
                <div className="col-span-10 min-h-0 overflow-hidden rounded border border-slate-800">
                  {mode === "side" ? (
                    <SideBySideView
                      pair={pair}
                      search={search}
                      inputs={result.inputs}
                    />
                  ) : (
                    <UnifiedView pair={pair} search={search} />
                  )}
                </div>
              </div>
            )}
            {(mode === "side" || mode === "unified") && !pair && (
              <div className="flex-1 grid place-items-center text-slate-500 text-sm">
                선택된 페어가 없습니다.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// 외부에서 호출되는 스크롤 헬퍼는 view 내부 ref와 분리되어 있어 본 모듈 레벨에서는 noop.
// 실제 스크롤은 각 view 컴포넌트가 IntersectionObserver처럼 line-id 기반 직접 처리.
function scrollToLine(left: number | null, right: number | null) {
  if (left != null) {
    document.getElementById(`l-line-${left}`)?.scrollIntoView({ block: "center" });
  }
  if (right != null) {
    document.getElementById(`r-line-${right}`)?.scrollIntoView({ block: "center" });
  }
}

function CompareHeader({
  result,
  loading,
  mode,
  setMode,
  search,
  setSearch,
  recipeIds,
  activePair,
  setActivePair,
  onClose,
}: {
  result: CompareResult | null;
  loading: boolean;
  mode: ViewMode;
  setMode: (m: ViewMode) => void;
  search: string;
  setSearch: (s: string) => void;
  recipeIds: number[];
  activePair: number;
  setActivePair: (n: number) => void;
  onClose: () => void;
}) {
  return (
    <header className="px-4 py-2 border-b border-slate-800 flex items-center gap-3">
      <h2 className="text-base font-semibold">Recipe 비교</h2>
      {result && (
        <div className="text-xs text-slate-400">
          schema={result.schema_version} · pairs={result.summary.total_pairs} · diffs=
          {result.summary.total_diffs} · {result.summary.pairs_identical}쌍 동일
        </div>
      )}
      <div className="ml-auto flex items-center gap-2">
        {result && result.pairs.length > 1 && (
          <select
            value={activePair}
            onChange={(e) => setActivePair(Number(e.target.value))}
            className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-xs"
          >
            {result.pairs.map((p, i) => (
              <option key={i} value={i}>
                {p.left_recipe_id} ↔ {p.right_recipe_id} ({p.diffs.length})
              </option>
            ))}
          </select>
        )}
        <div className="flex bg-slate-900 border border-slate-800 rounded text-xs overflow-hidden">
          <button
            onClick={() => setMode("clusters")}
            className={`px-2 py-1 ${mode === "clusters" ? "bg-sky-600" : "hover:bg-slate-800"}`}
            title="설비를 동일 패턴끼리 클러스터로 압축 (N대 많을 때 권장)"
          >
            clusters
          </button>
          <button
            onClick={() => setMode("pivot")}
            className={`px-2 py-1 ${mode === "pivot" ? "bg-sky-600" : "hover:bg-slate-800"}`}
            title="키별 값 분기를 한 표로"
          >
            pivot
          </button>
          <button
            onClick={() => setMode("side")}
            className={`px-2 py-1 ${mode === "side" ? "bg-sky-600" : "hover:bg-slate-800"}`}
          >
            side-by-side
          </button>
          <button
            onClick={() => setMode("unified")}
            className={`px-2 py-1 ${mode === "unified" ? "bg-sky-600" : "hover:bg-slate-800"}`}
          >
            unified
          </button>
        </div>
        <input
          type="search"
          placeholder="검색 (Ctrl+F 대체)"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-2 py-1 bg-slate-900 border border-slate-800 rounded text-xs w-48"
        />
        <ExportMenu recipeIds={recipeIds} disabled={loading || !result} />
        <button
          onClick={onClose}
          className="px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs"
        >
          닫기 (Esc)
        </button>
      </div>
    </header>
  );
}

function ExportMenu({ recipeIds, disabled }: { recipeIds: number[]; disabled: boolean }) {
  const [busy, setBusy] = useState<"html" | "csv" | "pdf" | null>(null);

  async function download(kind: "html" | "csv" | "pdf") {
    setBusy(kind);
    try {
      const res = await fetch(`/api/export/${kind}`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ recipe_ids: recipeIds, options: {} }),
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`HTTP ${res.status}: ${txt.slice(0, 200)}`);
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `compare.${kind}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      alert(`Export 실패 (${kind}): ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex bg-slate-900 border border-slate-800 rounded text-xs overflow-hidden">
      {(["html", "csv", "pdf"] as const).map((k) => (
        <button
          key={k}
          disabled={disabled || busy !== null}
          onClick={() => download(k)}
          className="px-2 py-1 hover:bg-slate-800 disabled:opacity-50 uppercase"
        >
          {busy === k ? "…" : k}
        </button>
      ))}
    </div>
  );
}

function DiffSidebar({
  pair,
  search,
  onJump,
}: {
  pair: ComparePair;
  search: string;
  onJump: (d: Diff) => void;
}) {
  const filtered = useMemo(() => {
    if (!search.trim()) return pair.diffs;
    const q = search.toLowerCase();
    return pair.diffs.filter((d) =>
      [d.section, d.key, d.left_value, d.right_value, d.note]
        .filter(Boolean)
        .some((v) => v!.toLowerCase().includes(q))
    );
  }, [pair.diffs, search]);

  const sevColor: Record<string, string> = {
    critical: "text-rose-400",
    major: "text-amber-400",
    minor: "text-yellow-300",
    info: "text-slate-400",
  };

  return (
    <aside className="col-span-2 min-h-0 overflow-auto rounded border border-slate-800 bg-slate-900/40">
      <div className="px-2 py-1.5 text-xs text-slate-400 border-b border-slate-800 sticky top-0 bg-slate-900/80 backdrop-blur">
        차이 {pair.diffs.length}건 (표시 {filtered.length})
        {pair.same && <span className="ml-1 text-emerald-400">· 동일</span>}
      </div>
      <ul className="text-xs">
        {filtered.map((d, i) => (
          <li
            key={i}
            onClick={() => onJump(d)}
            className="cursor-pointer px-2 py-1.5 border-b border-slate-900 hover:bg-slate-800/50"
          >
            <div className="flex items-center gap-1">
              <KindBadge kind={d.kind} />
              <span className={sevColor[d.severity]}>{d.severity}</span>
              {d.section && <span className="text-sky-300">{d.section}</span>}
              {d.key && <span className="text-slate-200">{d.key}</span>}
            </div>
            {(d.left_value || d.right_value) && (
              <div className="mt-0.5 text-slate-500 truncate">
                {(d.left_value ?? "")} → {(d.right_value ?? "")}
              </div>
            )}
          </li>
        ))}
      </ul>
    </aside>
  );
}

function KindBadge({ kind }: { kind: Diff["kind"] }) {
  const color: Record<string, string> = {
    added: "bg-emerald-500/20 text-emerald-300",
    removed: "bg-rose-500/20 text-rose-300",
    changed: "bg-amber-500/20 text-amber-300",
    moved: "bg-violet-500/20 text-violet-300",
    unchanged: "bg-slate-500/20 text-slate-300",
  };
  return (
    <span className={`text-[10px] px-1 rounded ${color[kind]}`}>{kind}</span>
  );
}

function SideBySideView({
  pair,
  search,
  inputs,
}: {
  pair: ComparePair;
  search: string;
  inputs: CompareResult["inputs"];
}) {
  const leftRef = useRef<HTMLDivElement | null>(null);
  const rightRef = useRef<HTMLDivElement | null>(null);
  const syncing = useRef(false);

  // 좌우 동기 스크롤
  useEffect(() => {
    function sync(src: HTMLDivElement | null, dst: HTMLDivElement | null) {
      if (!src || !dst || syncing.current) return;
      syncing.current = true;
      const ratio = src.scrollTop / Math.max(1, src.scrollHeight - src.clientHeight);
      dst.scrollTop = ratio * Math.max(1, dst.scrollHeight - dst.clientHeight);
      // 다음 프레임에 락 해제
      requestAnimationFrame(() => (syncing.current = false));
    }
    const l = leftRef.current;
    const r = rightRef.current;
    if (!l || !r) return;
    const handleL = () => sync(l, r);
    const handleR = () => sync(r, l);
    l.addEventListener("scroll", handleL);
    r.addEventListener("scroll", handleR);
    return () => {
      l.removeEventListener("scroll", handleL);
      r.removeEventListener("scroll", handleR);
    };
  }, [pair.left_recipe_id, pair.right_recipe_id]);

  const leftMeta = inputs.find((i) => i.recipe_id === pair.left_recipe_id);
  const rightMeta = inputs.find((i) => i.recipe_id === pair.right_recipe_id);

  const { leftLineMarks, rightLineMarks } = useMemo(
    () => buildLineMarks(pair),
    [pair]
  );

  return (
    <div className="grid grid-cols-2 h-full min-h-0 divide-x divide-slate-800">
      <SidePane
        title={leftMeta ? recipeLabel(leftMeta) : "좌"}
        text={leftMeta?.analysis2_text ?? ""}
        side="l"
        lineMarks={leftLineMarks}
        scrollRef={leftRef}
        search={search}
      />
      <SidePane
        title={rightMeta ? recipeLabel(rightMeta) : "우"}
        text={rightMeta?.analysis2_text ?? ""}
        side="r"
        lineMarks={rightLineMarks}
        scrollRef={rightRef}
        search={search}
      />
    </div>
  );
}

function recipeLabel(r: { line_name: string; model_name: string; equipment_name: string; path: string; film_name: string }) {
  return `${r.line_name}/${r.model_name}/${r.equipment_name} · ${r.path} · ${r.film_name}`;
}

function SidePane({
  title,
  text,
  side,
  lineMarks,
  scrollRef,
  search,
}: {
  title: string;
  text: string;
  side: "l" | "r";
  lineMarks: Map<number, Diff["kind"]>;
  scrollRef: React.MutableRefObject<HTMLDivElement | null>;
  search: string;
}) {
  const lines = useMemo(() => text.split(/\r?\n/), [text]);
  const q = search.trim().toLowerCase();

  return (
    <div className="flex flex-col min-h-0">
      <div className="px-2 py-1 text-xs text-slate-400 bg-slate-900/60 border-b border-slate-800 truncate">
        {title}
      </div>
      <div ref={scrollRef} className="flex-1 overflow-auto font-mono text-xs leading-5">
        {lines.map((line, i) => {
          const lineNo = i + 1;
          const mark = lineMarks.get(lineNo);
          const cls =
            mark === "added"
              ? "diff-added"
              : mark === "removed"
              ? "diff-removed"
              : mark === "changed"
              ? "diff-changed"
              : "";
          return (
            <div
              key={lineNo}
              id={`${side}-line-${lineNo}`}
              className={`grid grid-cols-[3.5rem_1fr] hover:bg-slate-800/30 ${cls}`}
            >
              <div className="text-right pr-2 text-slate-600 select-none">{lineNo}</div>
              <div className="whitespace-pre-wrap break-all px-2">
                {highlight(line, q)}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function UnifiedView({ pair, search }: { pair: ComparePair; search: string }) {
  const lines = useMemo(() => {
    if (!pair.raw_diff) return [];
    const out: { tag: string; text: string; lineL: number | null; lineR: number | null }[] = [];
    const L = pair.raw_diff.left_lines;
    const R = pair.raw_diff.right_lines;
    for (const op of pair.raw_diff.matcher_ops) {
      if (op.tag === "equal") {
        for (let i = 0; i < op.left_end - op.left_start; i++) {
          out.push({
            tag: "equal",
            text: L[op.left_start + i] ?? "",
            lineL: op.left_start + i + 1,
            lineR: op.right_start + i + 1,
          });
        }
      } else {
        for (let i = op.left_start; i < op.left_end; i++) {
          out.push({ tag: "del", text: L[i] ?? "", lineL: i + 1, lineR: null });
        }
        for (let i = op.right_start; i < op.right_end; i++) {
          out.push({ tag: "add", text: R[i] ?? "", lineL: null, lineR: i + 1 });
        }
      }
    }
    return out;
  }, [pair]);

  const q = search.trim().toLowerCase();

  return (
    <div className="overflow-auto h-full font-mono text-xs leading-5">
      {lines.map((row, i) => {
        const cls =
          row.tag === "add" ? "diff-added" : row.tag === "del" ? "diff-removed" : "";
        const prefix = row.tag === "add" ? "+" : row.tag === "del" ? "-" : " ";
        return (
          <div key={i} className={`grid grid-cols-[2rem_3rem_3rem_1fr] ${cls}`}>
            <div className="text-center text-slate-500 select-none">{prefix}</div>
            <div className="text-right pr-1 text-slate-600 select-none">
              {row.lineL ?? ""}
            </div>
            <div className="text-right pr-2 text-slate-600 select-none">
              {row.lineR ?? ""}
            </div>
            <div className="px-2 whitespace-pre-wrap break-all">
              {highlight(row.text, q)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function buildLineMarks(pair: ComparePair) {
  const leftLineMarks = new Map<number, Diff["kind"]>();
  const rightLineMarks = new Map<number, Diff["kind"]>();
  for (const d of pair.diffs) {
    if (d.left_line != null && d.kind !== "added") {
      leftLineMarks.set(d.left_line, d.kind);
    }
    if (d.right_line != null && d.kind !== "removed") {
      rightLineMarks.set(d.right_line, d.kind);
    }
  }
  // raw_diff가 있으면 매처 op도 보강 (stub의 광범위 변경 영역 표시)
  if (pair.raw_diff) {
    for (const op of pair.raw_diff.matcher_ops) {
      if (op.tag === "replace") {
        for (let i = op.left_start + 1; i <= op.left_end; i++)
          if (!leftLineMarks.has(i)) leftLineMarks.set(i, "changed");
        for (let i = op.right_start + 1; i <= op.right_end; i++)
          if (!rightLineMarks.has(i)) rightLineMarks.set(i, "changed");
      } else if (op.tag === "delete") {
        for (let i = op.left_start + 1; i <= op.left_end; i++)
          if (!leftLineMarks.has(i)) leftLineMarks.set(i, "removed");
      } else if (op.tag === "insert") {
        for (let i = op.right_start + 1; i <= op.right_end; i++)
          if (!rightLineMarks.has(i)) rightLineMarks.set(i, "added");
      }
    }
  }
  return { leftLineMarks, rightLineMarks };
}

function highlight(text: string, q: string) {
  if (!q) return text;
  const lower = text.toLowerCase();
  const out: React.ReactNode[] = [];
  let cursor = 0;
  while (cursor < text.length) {
    const idx = lower.indexOf(q, cursor);
    if (idx === -1) {
      out.push(text.slice(cursor));
      break;
    }
    if (idx > cursor) out.push(text.slice(cursor, idx));
    out.push(
      <mark key={idx} className="bg-yellow-300/40 text-yellow-100">
        {text.slice(idx, idx + q.length)}
      </mark>
    );
    cursor = idx + q.length;
  }
  return out;
}

// 외부에서 키보드 단축키로 변경 점프를 호출하기 위한 헬퍼.
// 본 컴포넌트가 호출자보다 짧게 살 수 있으므로 글로벌 hook으로 노출하지 않고
// 다이얼로그 내부에서 keydown을 직접 처리.
export function useDialogShortcuts(opts: {
  open: boolean;
  onClose: () => void;
  onJump: (delta: 1 | -1) => void;
}) {
  useEffect(() => {
    if (!opts.open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        opts.onClose();
      } else if (e.altKey && e.key === "ArrowDown") {
        e.preventDefault();
        opts.onJump(1);
      } else if (e.altKey && e.key === "ArrowUp") {
        e.preventDefault();
        opts.onJump(-1);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [opts.open, opts.onClose, opts.onJump]);
}
