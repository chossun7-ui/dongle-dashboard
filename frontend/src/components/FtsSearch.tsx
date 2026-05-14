import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

interface Hit {
  id: number;
  film_name: string | null;
  equipment_name: string;
  line_name: string;
  model_name: string;
  snippet: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onPick: (recipeId: number) => void;
}

/**
 * 전체 Script 풀텍스트 검색 (SQLite FTS5).
 *
 * FTS5 쿼리 문법을 그대로 노출: "Power AND Pressure", "as42 OR as99", '"exact phrase"' 등.
 * Ctrl+K로 열고, Esc로 닫음.
 */
export function FtsSearch({ open, onClose, onPick }: Props) {
  const [q, setQ] = useState("");
  const [hits, setHits] = useState<Hit[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 30);
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    const term = q.trim();
    if (!term) {
      setHits([]);
      setError(null);
      return;
    }
    setBusy(true);
    setError(null);
    const t = setTimeout(async () => {
      try {
        const data = await api.get<Hit[]>(
          `/api/recipes/search/fts?q=${encodeURIComponent(term)}`
        );
        setHits(data);
      } catch (e) {
        setError((e as Error).message);
        setHits([]);
      } finally {
        setBusy(false);
      }
    }, 200);
    return () => clearTimeout(t);
  }, [q, open]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-start pt-20 bg-black/70"
      role="dialog"
      aria-modal="true"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-[640px] max-w-[90vw] rounded-xl border border-slate-800 bg-slate-950 shadow-2xl">
        <input
          ref={inputRef}
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="검색 (FTS5 문법 지원: Power AND Pressure, &quot;exact&quot;, *prefix)"
          className="w-full px-4 py-3 bg-transparent border-b border-slate-800 outline-none text-sm"
        />
        <div className="max-h-[60vh] overflow-auto">
          {error && (
            <p className="px-4 py-3 text-rose-300 text-sm">{error}</p>
          )}
          {!error && !busy && hits.length === 0 && q.trim() && (
            <p className="px-4 py-6 text-slate-500 text-sm text-center">결과 없음</p>
          )}
          {!error && !q.trim() && (
            <p className="px-4 py-6 text-slate-500 text-xs text-center">
              <kbd className="px-1 bg-slate-800 rounded">Esc</kbd> 닫기 ·{" "}
              <kbd className="px-1 bg-slate-800 rounded">Enter</kbd> 결과 선택
            </p>
          )}
          <ul className="divide-y divide-slate-900">
            {hits.map((h) => (
              <li
                key={h.id}
                onClick={() => onPick(h.id)}
                className="px-4 py-2 cursor-pointer hover:bg-slate-800/50"
              >
                <div className="text-sm text-sky-300">
                  {h.film_name ?? "(이름 없음)"}{" "}
                  <span className="text-slate-500">
                    · {h.line_name}/{h.model_name}/{h.equipment_name}
                  </span>
                </div>
                <div
                  className="text-xs text-slate-300 mt-0.5 font-mono"
                  dangerouslySetInnerHTML={{ __html: h.snippet }}
                />
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
