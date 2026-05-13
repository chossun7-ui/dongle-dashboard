import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";
import { MultiSelect } from "@/components/MultiSelect";
import { useIntListUrlState } from "@/hooks/useUrlState";
import type { Equipment, Line, Model, RecipeListItem } from "@/types";

export default function Dashboard() {
  const [lines, setLines] = useState<Line[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [equipments, setEquipments] = useState<Equipment[]>([]);
  const [recipes, setRecipes] = useState<RecipeListItem[]>([]);
  const [scanning, setScanning] = useState(false);

  const [selLines, setSelLines] = useIntListUrlState("lines");
  const [selModels, setSelModels] = useIntListUrlState("models");
  const [selEquips, setSelEquips] = useIntListUrlState("equipments");
  const [selRecipes, setSelRecipes] = useIntListUrlState("recipes");

  // 마스터 데이터 로드
  useEffect(() => {
    api.get<Line[]>("/api/lines").then(setLines).catch(console.error);
    api.get<Model[]>("/api/models").then(setModels).catch(console.error);
  }, []);

  // 라인·모델 선택에 따라 설비 후보 갱신
  useEffect(() => {
    const qs = new URLSearchParams();
    if (selLines.length) qs.set("line_ids", selLines.join(","));
    if (selModels.length) qs.set("model_ids", selModels.join(","));
    api
      .get<Equipment[]>(`/api/equipments?${qs.toString()}`)
      .then(setEquipments)
      .catch(console.error);
  }, [selLines, selModels]);

  // 설비 후보 변동 시 더 이상 선택 가능하지 않은 설비는 자동 제거
  useEffect(() => {
    const valid = new Set(equipments.map((e) => e.id));
    const next = selEquips.filter((id) => valid.has(id));
    if (next.length !== selEquips.length) setSelEquips(next);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [equipments]);

  // 설비 선택 시 캐시된 Recipe 조회 (재스캔은 명시적 버튼)
  useEffect(() => {
    if (selEquips.length === 0) {
      setRecipes([]);
      return;
    }
    api
      .get<RecipeListItem[]>(`/api/recipes?equipment_ids=${selEquips.join(",")}`)
      .then(setRecipes)
      .catch(console.error);
  }, [selEquips]);

  const recipesByFilm = useMemo(() => {
    const m = new Map<string, RecipeListItem[]>();
    for (const r of recipes) {
      const key = r.film_name ?? "(이름 없음)";
      const arr = m.get(key) ?? [];
      arr.push(r);
      m.set(key, arr);
    }
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [recipes]);

  const rescan = async () => {
    if (selEquips.length === 0) return;
    setScanning(true);
    try {
      await api.post<{ job_id: string }>("/api/scan", {
        equipment_ids: selEquips,
      });
      alert("스캔 작업 요청을 보냈습니다. 잠시 후 새로고침하세요.");
    } catch (e) {
      alert(`스캔 요청 실패: ${(e as Error).message}`);
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-slate-800 px-4 py-2 flex items-center justify-between">
        <h1 className="text-base font-semibold">Recipe Film Script 비교 대시보드</h1>
        <nav className="flex items-center gap-3 text-sm">
          <Link to="/admin" className="text-slate-400 hover:text-sky-300">
            관리자
          </Link>
        </nav>
      </header>

      <main className="flex-1 grid grid-cols-12 gap-3 p-3">
        <aside className="col-span-3 space-y-3">
          <MultiSelect
            label="라인"
            options={lines}
            selected={selLines}
            onChange={setSelLines}
            emptyHint="등록된 라인이 없습니다. 관리자 페이지에서 추가하세요."
          />
          <MultiSelect
            label="모델"
            options={models}
            selected={selModels}
            onChange={setSelModels}
            emptyHint="등록된 모델이 없습니다."
          />
          <MultiSelect
            label="설비"
            options={equipments.map((e) => ({
              id: e.id,
              name: `${e.name} · ${e.line_name}/${e.model_name}`,
            }))}
            selected={selEquips}
            onChange={setSelEquips}
            emptyHint="라인/모델을 먼저 선택하세요."
          />
          <button
            onClick={rescan}
            disabled={selEquips.length === 0 || scanning}
            className="w-full py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm"
          >
            {scanning ? "요청 중..." : `선택 설비 재스캔 (${selEquips.length})`}
          </button>
        </aside>

        <section className="col-span-9 rounded-lg border border-slate-800 bg-slate-900/40 p-3">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-slate-200">
                Recipe 목록 — Film 이름별 자동 그룹
              </h2>
              <p className="text-xs text-slate-500">
                {recipes.length}개 Recipe · {selRecipes.length}개 비교 선택
              </p>
            </div>
            <button
              disabled={selRecipes.length < 2}
              onClick={() => alert("비교 다이얼로그는 다음 단계 PR에서 추가됩니다.")}
              className="px-3 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-700 disabled:text-slate-500 text-white text-sm"
            >
              선택 비교 ({selRecipes.length})
            </button>
          </div>

          {recipesByFilm.length === 0 ? (
            <p className="text-slate-500 text-sm py-8 text-center">
              설비를 선택하면 캐시된 Recipe가 표시됩니다.
            </p>
          ) : (
            <div className="space-y-3 overflow-auto" style={{ maxHeight: "70vh" }}>
              {recipesByFilm.map(([film, items]) => (
                <div key={film} className="rounded border border-slate-800">
                  <div className="px-3 py-1.5 bg-slate-800/60 text-sm font-medium text-sky-300">
                    {film} <span className="text-xs text-slate-400">({items.length})</span>
                  </div>
                  <ul className="divide-y divide-slate-800">
                    {items.map((r) => {
                      const on = selRecipes.includes(r.id);
                      return (
                        <li
                          key={r.id}
                          className={`px-3 py-1.5 text-xs flex items-center gap-2 cursor-pointer ${
                            on ? "bg-sky-500/10" : "hover:bg-slate-800/40"
                          }`}
                          onClick={() => {
                            const next = on
                              ? selRecipes.filter((x) => x !== r.id)
                              : [...selRecipes, r.id];
                            setSelRecipes(next);
                          }}
                        >
                          <span>{on ? "■" : "□"}</span>
                          <span className="text-slate-300">
                            {r.line_name}/{r.model_name}/{r.equipment_name}
                          </span>
                          <span className="text-slate-500 font-mono">{r.path}</span>
                          <span className="ml-auto text-slate-600">
                            {r.body_hash.slice(0, 8)} · {r.last_scanned_at}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
