import { useMemo, useState } from "react";

interface Option {
  id: number;
  name: string;
}

interface Props {
  label: string;
  options: Option[];
  selected: number[];
  onChange: (ids: number[]) => void;
  emptyHint?: string;
}

/**
 * 라인·모델·설비에 공통으로 쓰는 다중선택 칩 박스.
 * - 검색 박스로 좁히기
 * - 전체 선택 / 해제
 * - 선택된 항목은 상단 칩으로
 */
export function MultiSelect({ label, options, selected, onChange, emptyHint }: Props) {
  const [query, setQuery] = useState("");
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? options.filter((o) => o.name.toLowerCase().includes(q)) : options;
  }, [options, query]);
  const selectedSet = useMemo(() => new Set(selected), [selected]);

  const toggle = (id: number) => {
    const next = new Set(selectedSet);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onChange([...next]);
  };

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
      <header className="flex items-center justify-between gap-2 mb-2">
        <h3 className="text-sm font-semibold text-slate-200">
          {label}
          <span className="ml-2 text-slate-500 text-xs">
            {selected.length}/{options.length}
          </span>
        </h3>
        <div className="flex gap-1 text-xs">
          <button
            type="button"
            onClick={() => onChange(filtered.map((o) => o.id))}
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700"
          >
            전체
          </button>
          <button
            type="button"
            onClick={() => onChange([])}
            className="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700"
          >
            해제
          </button>
        </div>
      </header>
      <input
        type="search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="검색..."
        className="w-full mb-2 px-2 py-1 text-sm rounded bg-slate-950 border border-slate-800 focus:border-sky-500 outline-none"
      />
      <div className="max-h-48 overflow-auto pr-1">
        {filtered.length === 0 ? (
          <p className="text-slate-500 text-xs py-2 text-center">
            {emptyHint ?? "항목 없음"}
          </p>
        ) : (
          <ul className="space-y-0.5">
            {filtered.map((o) => {
              const on = selectedSet.has(o.id);
              return (
                <li key={o.id}>
                  <button
                    type="button"
                    onClick={() => toggle(o.id)}
                    className={`w-full text-left px-2 py-1 rounded text-sm transition ${
                      on
                        ? "bg-sky-500/20 text-sky-200"
                        : "hover:bg-slate-800 text-slate-300"
                    }`}
                  >
                    <span className="mr-2">{on ? "■" : "□"}</span>
                    {o.name}
                  </button>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </section>
  );
}
