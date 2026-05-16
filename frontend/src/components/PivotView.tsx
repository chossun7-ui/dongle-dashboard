import { useMemo, useState } from "react";
import type { PivotEntry, PivotResult, RecipeMeta } from "@/types";

interface Props {
  pivot: PivotResult;
  inputs: RecipeMeta[];
}

/**
 * 키 분기 표.
 *
 * 각 (section, key)별로 값에 따라 설비를 묶어 한 줄에 표시.
 * - 다수 그룹은 회색 베이스, 외톨이는 빨강, 중간은 노랑.
 * - 라인·모델별로 칩을 그루핑하여 패턴이 보이도록 한다.
 * - 검색·외톨이 필터 지원.
 */
export function PivotView({ pivot, inputs }: Props) {
  const metaById = useMemo(() => {
    const m = new Map<number, RecipeMeta>();
    inputs.forEach((r) => m.set(r.recipe_id, r));
    return m;
  }, [inputs]);

  const [search, setSearch] = useState("");
  const [outlierOnly, setOutlierOnly] = useState(false);

  const filtered = useMemo(() => {
    let list = pivot.entries;
    if (outlierOnly) list = list.filter((e) => e.is_outlier_present);
    const q = search.trim().toLowerCase();
    if (q) {
      list = list.filter((e) =>
        [e.section, e.key, ...e.branches.map((b) => b.value)]
          .filter(Boolean)
          .some((s) => s!.toLowerCase().includes(q))
      );
    }
    return list;
  }, [pivot.entries, search, outlierOnly]);

  return (
    <div className="h-full min-h-0 flex flex-col p-2 gap-2">
      <header className="flex items-center gap-2 text-xs">
        <span className="text-slate-400">
          분기 키 {pivot.entries.length}개 · {inputs.length}대 설비
        </span>
        <input
          type="search"
          placeholder="키·값 검색"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="px-2 py-1 bg-slate-900 border border-slate-800 rounded w-48"
        />
        <label className="flex items-center gap-1 text-slate-300">
          <input
            type="checkbox"
            checked={outlierOnly}
            onChange={(e) => setOutlierOnly(e.target.checked)}
          />
          외톨이(1대뿐인 분기) 보유 키만
        </label>
        <span className="ml-auto text-slate-500">{filtered.length}건 표시</span>
      </header>

      <div className="flex-1 min-h-0 overflow-auto rounded border border-slate-800 bg-slate-900/40">
        {filtered.length === 0 ? (
          <p className="p-6 text-slate-500 text-sm text-center">
            {pivot.entries.length === 0
              ? "모든 키가 동일합니다. 차이가 없습니다."
              : "필터에 일치하는 키가 없습니다."}
          </p>
        ) : (
          <ul className="divide-y divide-slate-900">
            {filtered.map((e) => (
              <PivotRow key={`${e.section ?? ""}|${e.key}`} entry={e} metaById={metaById} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function PivotRow({
  entry,
  metaById,
}: {
  entry: PivotEntry;
  metaById: Map<number, RecipeMeta>;
}) {
  return (
    <li className="px-3 py-2">
      <div className="flex items-baseline gap-2 mb-1.5">
        {entry.section && (
          <span className="text-xs text-sky-300">[{entry.section}]</span>
        )}
        <span className="text-sm font-mono text-slate-100">{entry.key}</span>
        <span className="text-xs text-slate-500">— 분기 {entry.branches.length}개</span>
        {entry.is_outlier_present && (
          <span className="text-[10px] px-1 rounded bg-rose-500/20 text-rose-300">
            외톨이 포함
          </span>
        )}
      </div>
      <ul className="space-y-1">
        {entry.branches.map((b, i) => (
          <BranchRow key={`${b.value}|${i}`} branch={b} metaById={metaById} />
        ))}
      </ul>
    </li>
  );
}

function BranchRow({
  branch,
  metaById,
}: {
  branch: { value: string; recipe_ids: number[]; is_majority: boolean };
  metaById: Map<number, RecipeMeta>;
}) {
  const isMajority = branch.is_majority;
  const isOutlier = branch.recipe_ids.length === 1;
  const isMissing = branch.value === "(없음)";

  const bullet = isMajority ? "▪" : "▫";
  const valueClass = isMissing
    ? "text-rose-300 italic"
    : isMajority
    ? "text-slate-100"
    : "text-amber-200";
  const bgClass = isMajority
    ? "bg-slate-800/40"
    : isOutlier
    ? "bg-rose-500/10"
    : "bg-amber-500/10";

  // 라인/모델별 그루핑
  const grouped = useMemo(() => {
    const m = new Map<string, RecipeMeta[]>();
    branch.recipe_ids.forEach((rid) => {
      const meta = metaById.get(rid);
      if (!meta) return;
      const k = `${meta.line_name}/${meta.model_name}`;
      (m.get(k) ?? m.set(k, []).get(k)!).push(meta);
    });
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [branch.recipe_ids, metaById]);

  return (
    <li className={`grid grid-cols-[1rem_8rem_5rem_1fr] gap-2 items-start px-2 py-1 rounded ${bgClass}`}>
      <span className="text-slate-500">{bullet}</span>
      <span className={`font-mono text-xs truncate ${valueClass}`} title={branch.value}>
        {branch.value}
      </span>
      <span className="text-[11px] text-slate-400">
        {branch.recipe_ids.length}대
        {isMajority && " · 다수"}
        {isOutlier && " · 외톨이"}
      </span>
      <div className="text-[11px] space-y-0.5">
        {grouped.map(([line, list]) => (
          <ChipLine key={line} line={line} list={list} />
        ))}
      </div>
    </li>
  );
}

function ChipLine({ line, list }: { line: string; list: RecipeMeta[] }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? list : list.slice(0, 8);
  const hidden = list.length - visible.length;
  return (
    <div>
      <span className="text-slate-500">{line}:</span>{" "}
      {visible.map((m, i) => (
        <span key={m.recipe_id} className="font-mono text-slate-200" title={m.path}>
          {m.equipment_name}
          {i < visible.length - 1 && ", "}
        </span>
      ))}
      {hidden > 0 && (
        <button
          onClick={() => setExpanded(true)}
          className="ml-1 text-sky-400 hover:underline"
        >
          +{hidden}
        </button>
      )}
    </div>
  );
}
