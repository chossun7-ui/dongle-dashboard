import { useCallback, useEffect, useState } from "react";
import { api } from "@/lib/api";

interface Favorite {
  id: number;
  kind: "recipe" | "group" | "preset";
  label: string;
  payload: PresetPayload | GroupPayload | RecipePayload;
  created_at: string;
}

interface PresetPayload {
  lines: number[];
  models: number[];
  equipments: number[];
}
interface GroupPayload {
  recipe_ids: number[];
}
interface RecipePayload {
  recipe_id: number;
}

interface Props {
  selection: PresetPayload;
  onApplyPreset: (p: PresetPayload) => void;
  currentRecipeIds: number[];
  onApplyGroup: (recipeIds: number[]) => void;
}

/**
 * 즐겨찾기·프리셋 사이드 패널.
 * - 라인/모델/설비 다중선택 조합을 'preset'으로 저장
 * - 현재 비교 선택(recipe_ids)을 'group'으로 저장
 */
export function FavoritesPanel({
  selection,
  onApplyPreset,
  currentRecipeIds,
  onApplyGroup,
}: Props) {
  const [items, setItems] = useState<Favorite[]>([]);
  const [label, setLabel] = useState("");
  const [kind, setKind] = useState<"preset" | "group">("preset");

  const refresh = useCallback(() => {
    api.get<Favorite[]>("/api/favorites").then(setItems).catch(console.error);
  }, []);
  useEffect(refresh, [refresh]);

  const save = async () => {
    if (!label.trim()) return;
    const payload =
      kind === "preset"
        ? selection
        : { recipe_ids: currentRecipeIds };
    if (kind === "group" && currentRecipeIds.length < 2) {
      alert("Group으로 저장하려면 비교 대상 Recipe를 2개 이상 선택하세요.");
      return;
    }
    await api.post("/api/favorites", { kind, label: label.trim(), payload });
    setLabel("");
    refresh();
  };

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-3">
      <header className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-200">즐겨찾기 · 프리셋</h3>
        <span className="text-xs text-slate-500">{items.length}개</span>
      </header>
      <div className="flex gap-1 mb-2">
        <select
          value={kind}
          onChange={(e) => setKind(e.target.value as "preset" | "group")}
          className="px-1.5 py-1 text-xs bg-slate-950 border border-slate-800 rounded"
        >
          <option value="preset">preset (라인/모델/설비)</option>
          <option value="group">group (비교 Recipe)</option>
        </select>
      </div>
      <div className="flex gap-1 mb-2">
        <input
          value={label}
          onChange={(e) => setLabel(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && save()}
          placeholder="이름"
          className="flex-1 px-2 py-1 text-xs bg-slate-950 border border-slate-800 rounded"
        />
        <button
          onClick={save}
          className="px-2 py-1 text-xs rounded bg-sky-600 hover:bg-sky-500"
        >
          저장
        </button>
      </div>
      <ul className="space-y-1 max-h-48 overflow-auto pr-1">
        {items.map((f) => (
          <li
            key={f.id}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded hover:bg-slate-800/40"
          >
            <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-400">
              {f.kind}
            </span>
            <button
              className="flex-1 text-left text-slate-200 truncate"
              onClick={() => {
                if (f.kind === "preset") {
                  onApplyPreset(f.payload as PresetPayload);
                } else if (f.kind === "group") {
                  onApplyGroup((f.payload as GroupPayload).recipe_ids);
                }
              }}
            >
              {f.label}
            </button>
            <button
              onClick={async () => {
                await api.del(`/api/favorites/${f.id}`);
                refresh();
              }}
              className="text-rose-400 hover:text-rose-300"
              title="삭제"
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
