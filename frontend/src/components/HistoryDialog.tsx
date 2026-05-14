import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";

interface Props {
  recipeId: number | null;
  onClose: () => void;
}

interface Snapshot {
  id: number | "current";
  taken_at: string;
  body_hash: string;
  is_current: boolean;
}

interface SnapshotBody {
  body_text: string;
  ini_text: string | null;
  body_hash: string;
  taken_at: string;
}

/**
 * Recipe 변경 이력 시계열 뷰.
 * - 좌측: 시점 목록 (current + 과거 스냅샷)
 * - 우측: 두 시점 본문을 좌·우로 비교 (단순 라인 단위)
 *
 * 본격적인 의미 단위 비교가 필요하면 두 본문 중 한쪽을 임시 RecipeInput으로 만들어
 * compare API를 호출하도록 확장 가능하나, 현재는 빠른 시각 비교에 집중.
 */
export function HistoryDialog({ recipeId, onClose }: Props) {
  const open = recipeId != null;
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [leftId, setLeftId] = useState<Snapshot["id"] | null>(null);
  const [rightId, setRightId] = useState<Snapshot["id"] | null>(null);
  const [leftBody, setLeftBody] = useState<SnapshotBody | null>(null);
  const [rightBody, setRightBody] = useState<SnapshotBody | null>(null);

  useEffect(() => {
    if (!open) return;
    api
      .get<Snapshot[]>(`/api/recipes/${recipeId}/snapshots`)
      .then((data) => {
        setSnapshots(data);
        // 기본: 현재 vs 직전
        setLeftId(data[1]?.id ?? null);
        setRightId(data[0]?.id ?? null);
      })
      .catch(console.error);
  }, [recipeId, open]);

  useEffect(() => {
    if (!open || leftId == null) {
      setLeftBody(null);
      return;
    }
    api.get<SnapshotBody>(`/api/recipes/${recipeId}/snapshots/${leftId}`).then(setLeftBody);
  }, [recipeId, leftId, open]);
  useEffect(() => {
    if (!open || rightId == null) {
      setRightBody(null);
      return;
    }
    api.get<SnapshotBody>(`/api/recipes/${recipeId}/snapshots/${rightId}`).then(setRightBody);
  }, [recipeId, rightId, open]);

  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 grid place-items-center bg-black/70"
      role="dialog"
      aria-modal="true"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-[90vw] h-[80vh] max-w-[1400px] flex flex-col rounded-xl border border-slate-800 bg-slate-950">
        <header className="px-4 py-2 border-b border-slate-800 flex items-center gap-3">
          <h2 className="text-base font-semibold">Recipe 변경 이력</h2>
          <span className="text-xs text-slate-400">
            {snapshots.length}개 시점 (current 포함)
          </span>
          <button
            onClick={onClose}
            className="ml-auto px-3 py-1 rounded bg-slate-800 hover:bg-slate-700 text-xs"
          >
            닫기 (Esc)
          </button>
        </header>
        <div className="flex-1 min-h-0 grid grid-cols-12 gap-2 px-3 pb-3">
          <aside className="col-span-2 min-h-0 overflow-auto rounded border border-slate-800 bg-slate-900/40 text-xs">
            <div className="px-2 py-1.5 sticky top-0 bg-slate-900/80 backdrop-blur border-b border-slate-800 text-slate-400">
              시점 선택 — 좌/우
            </div>
            <ul>
              {snapshots.map((s) => {
                const isLeft = s.id === leftId;
                const isRight = s.id === rightId;
                return (
                  <li
                    key={String(s.id)}
                    className="px-2 py-1.5 border-b border-slate-900 hover:bg-slate-800/40"
                  >
                    <div className="flex items-center gap-1 text-slate-300">
                      <button
                        className={`text-[10px] px-1 rounded ${
                          isLeft ? "bg-emerald-500/40" : "bg-slate-800"
                        }`}
                        onClick={() => setLeftId(s.id)}
                      >
                        L
                      </button>
                      <button
                        className={`text-[10px] px-1 rounded ${
                          isRight ? "bg-sky-500/40" : "bg-slate-800"
                        }`}
                        onClick={() => setRightId(s.id)}
                      >
                        R
                      </button>
                      <span className="ml-1 truncate">
                        {s.is_current ? "current" : s.taken_at.slice(0, 16)}
                      </span>
                    </div>
                    <div className="text-slate-600 ml-7 font-mono text-[10px]">
                      {s.body_hash.slice(0, 12)}
                    </div>
                  </li>
                );
              })}
            </ul>
          </aside>
          <div className="col-span-10 min-h-0 grid grid-cols-2 gap-2">
            <BodyPane title="L" body={leftBody} />
            <BodyPane title="R" body={rightBody} />
          </div>
        </div>
      </div>
    </div>
  );
}

function BodyPane({ title, body }: { title: string; body: SnapshotBody | null }) {
  const lines = useMemo(() => (body?.body_text ?? "").split(/\r?\n/), [body]);
  return (
    <div className="min-h-0 flex flex-col rounded border border-slate-800">
      <div className="px-2 py-1 text-xs text-slate-400 bg-slate-900/60 border-b border-slate-800">
        {title} · {body?.taken_at ?? ""}
      </div>
      <div className="flex-1 overflow-auto font-mono text-xs leading-5">
        {!body ? (
          <p className="text-slate-500 text-center py-4">선택된 시점이 없습니다.</p>
        ) : (
          lines.map((l, i) => (
            <div
              key={i}
              className="grid grid-cols-[3rem_1fr] hover:bg-slate-800/30"
            >
              <div className="text-right pr-2 text-slate-600 select-none">{i + 1}</div>
              <div className="whitespace-pre-wrap break-all px-2">{l}</div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
