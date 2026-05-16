import { useMemo, useState } from "react";
import type { Cluster, ClusteringResult, Diff, RecipeMeta } from "@/types";

interface Props {
  clusters: ClusteringResult;
  inputs: RecipeMeta[];
}

/**
 * 설비 클러스터 뷰.
 *
 * N≥10 설비 비교 시 N(N-1)/2 페어를 모두 펼치지 않고, 같은 본문(또는 키-값 시그니처)을
 * 공유하는 설비끼리 클러스터로 묶어 K(K-1)/2 페어로 압축한다.
 *
 * - 상단: 클러스터 카드 (라벨 A/B/C..., 크기, 라인·모델·설비 칩, 다수/외톨이 배지)
 * - 하단: 두 클러스터 선택 → 대표 본문 간 의미 단위 diff
 */
export function ClusterView({ clusters, inputs }: Props) {
  const metaById = useMemo(() => {
    const m = new Map<number, RecipeMeta>();
    inputs.forEach((r) => m.set(r.recipe_id, r));
    return m;
  }, [inputs]);

  const [leftId, setLeftId] = useState<string | null>(
    clusters.clusters[0]?.id ?? null
  );
  const [rightId, setRightId] = useState<string | null>(
    clusters.clusters[1]?.id ?? clusters.clusters[0]?.id ?? null
  );

  const pair = useMemo(() => {
    if (!leftId || !rightId || leftId === rightId) return null;
    return (
      clusters.pair_diffs.find(
        (p) =>
          (p.left_cluster_id === leftId && p.right_cluster_id === rightId) ||
          (p.left_cluster_id === rightId && p.right_cluster_id === leftId)
      ) ?? null
    );
  }, [leftId, rightId, clusters.pair_diffs]);

  // 좌우 swap이 일어났을 때 diff의 left/right를 뒤집어주기 위한 헬퍼
  const orientedDiffs = useMemo<Diff[]>(() => {
    if (!pair) return [];
    if (pair.left_cluster_id === leftId) return pair.diffs;
    return pair.diffs.map((d) => ({
      ...d,
      kind: d.kind === "added" ? "removed" : d.kind === "removed" ? "added" : d.kind,
      left_value: d.right_value,
      right_value: d.left_value,
      left_line: d.right_line,
      right_line: d.left_line,
    }));
  }, [pair, leftId]);

  if (clusters.clusters.length === 0) {
    return (
      <div className="grid place-items-center h-full text-slate-500 text-sm">
        클러스터 결과 없음
      </div>
    );
  }

  return (
    <div className="h-full min-h-0 flex flex-col gap-2 p-2">
      <header className="flex items-center gap-2 text-xs text-slate-400">
        <span>
          {inputs.length}대 설비 → {clusters.clusters.length}개 클러스터로 압축
        </span>
        <span className="text-slate-600">·</span>
        <span>K(K-1)/2 = {clusters.pair_diffs.length} 페어</span>
      </header>

      {/* 클러스터 카드 그리드 */}
      <div className="grid grid-cols-2 gap-2 overflow-auto max-h-[40%]">
        {clusters.clusters.map((c) => (
          <ClusterCard
            key={c.id}
            cluster={c}
            metaById={metaById}
            isLeft={leftId === c.id}
            isRight={rightId === c.id}
            onPickLeft={() => setLeftId(c.id)}
            onPickRight={() => setRightId(c.id)}
          />
        ))}
      </div>

      {/* 클러스터 페어 diff */}
      <div className="flex-1 min-h-0 rounded border border-slate-800 bg-slate-900/40 overflow-hidden flex flex-col">
        <div className="px-3 py-1.5 border-b border-slate-800 text-xs flex items-center gap-2">
          <span className="text-slate-400">선택된 페어:</span>
          <ClusterBadge id={leftId} />
          <span className="text-slate-500">vs</span>
          <ClusterBadge id={rightId} />
          {pair && (
            <span className="ml-auto text-slate-400">
              {pair.diffs.length}건 차이
            </span>
          )}
        </div>
        {!pair ? (
          <div className="flex-1 grid place-items-center text-slate-500 text-sm">
            카드의 [L]/[R] 버튼으로 두 클러스터를 선택하세요.
          </div>
        ) : (
          <ClusterDiffTable diffs={orientedDiffs} />
        )}
      </div>
    </div>
  );
}

function ClusterCard({
  cluster,
  metaById,
  isLeft,
  isRight,
  onPickLeft,
  onPickRight,
}: {
  cluster: Cluster;
  metaById: Map<number, RecipeMeta>;
  isLeft: boolean;
  isRight: boolean;
  onPickLeft: () => void;
  onPickRight: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  // 라인·모델별 그룹핑 — "P1/IRIS: MTKB561, 562, ..." 형태
  const grouped = useMemo(() => {
    const m = new Map<string, RecipeMeta[]>();
    cluster.recipe_ids.forEach((rid) => {
      const meta = metaById.get(rid);
      if (!meta) return;
      const k = `${meta.line_name}/${meta.model_name}`;
      (m.get(k) ?? m.set(k, []).get(k)!).push(meta);
    });
    return [...m.entries()].sort((a, b) => a[0].localeCompare(b[0]));
  }, [cluster.recipe_ids, metaById]);

  const sizeBadge = cluster.is_majority
    ? "bg-emerald-500/20 text-emerald-300"
    : cluster.recipe_ids.length === 1
    ? "bg-rose-500/20 text-rose-300"
    : "bg-amber-500/20 text-amber-300";

  return (
    <article
      className={`rounded border ${
        isLeft || isRight
          ? "border-sky-600 bg-sky-500/5"
          : "border-slate-800 bg-slate-900/60"
      } p-2 text-xs`}
    >
      <header className="flex items-center gap-2 mb-1">
        <span className="text-lg font-bold text-sky-300 leading-none">
          {cluster.id}
        </span>
        <span className={`px-1.5 py-0.5 rounded ${sizeBadge}`}>
          {cluster.recipe_ids.length}대
        </span>
        {cluster.is_majority && (
          <span className="text-emerald-400">· 기준</span>
        )}
        {cluster.recipe_ids.length === 1 && (
          <span className="text-rose-400">· 외톨이</span>
        )}
        {cluster.body_hash_match && (
          <span
            className="text-slate-500"
            title="본문 바이트가 완전히 동일"
          >
            · 본문 동일
          </span>
        )}
        <span className="ml-auto flex gap-1">
          <button
            onClick={onPickLeft}
            className={`text-[10px] px-1.5 py-0.5 rounded ${
              isLeft ? "bg-emerald-500/50" : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            L
          </button>
          <button
            onClick={onPickRight}
            className={`text-[10px] px-1.5 py-0.5 rounded ${
              isRight ? "bg-sky-500/50" : "bg-slate-800 hover:bg-slate-700"
            }`}
          >
            R
          </button>
        </span>
      </header>
      <div className="space-y-0.5 text-slate-300">
        {grouped.map(([line, list]) => {
          const visible = expanded ? list : list.slice(0, 6);
          const hidden = list.length - visible.length;
          return (
            <div key={line}>
              <span className="text-slate-500">{line}:</span>{" "}
              {visible.map((m, i) => (
                <span
                  key={m.recipe_id}
                  className="font-mono text-slate-200"
                  title={m.path}
                >
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
        })}
      </div>
      <div className="mt-1 font-mono text-[10px] text-slate-600 truncate">
        sig={cluster.signature.slice(0, 12)}
      </div>
    </article>
  );
}

function ClusterBadge({ id }: { id: string | null }) {
  if (!id) return <span className="text-slate-500">—</span>;
  return (
    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-300 font-mono">
      {id}
    </span>
  );
}

function ClusterDiffTable({ diffs }: { diffs: Diff[] }) {
  if (diffs.length === 0) {
    return (
      <div className="flex-1 grid place-items-center text-emerald-400 text-sm">
        ✓ 두 클러스터는 의미적으로 동일합니다.
      </div>
    );
  }
  return (
    <div className="flex-1 overflow-auto">
      <table className="w-full text-xs">
        <thead className="sticky top-0 bg-slate-900/90 backdrop-blur text-slate-400">
          <tr className="border-b border-slate-800">
            <th className="text-left px-2 py-1.5 w-20">kind</th>
            <th className="text-left px-2 py-1.5 w-32">section</th>
            <th className="text-left px-2 py-1.5 w-40">key</th>
            <th className="text-left px-2 py-1.5">L 값</th>
            <th className="text-left px-2 py-1.5">R 값</th>
            <th className="text-left px-2 py-1.5 w-20">severity</th>
          </tr>
        </thead>
        <tbody>
          {diffs.map((d, i) => (
            <tr
              key={i}
              className={`border-b border-slate-900 ${
                d.kind === "added"
                  ? "bg-emerald-500/5"
                  : d.kind === "removed"
                  ? "bg-rose-500/5"
                  : d.kind === "changed"
                  ? "bg-amber-500/5"
                  : ""
              }`}
            >
              <td className="px-2 py-1">
                <KindBadge kind={d.kind} />
              </td>
              <td className="px-2 py-1 text-sky-300">{d.section ?? ""}</td>
              <td className="px-2 py-1 font-mono text-slate-200">{d.key ?? ""}</td>
              <td className="px-2 py-1 font-mono text-rose-200">
                {d.left_value ?? <span className="text-slate-600">—</span>}
              </td>
              <td className="px-2 py-1 font-mono text-emerald-200">
                {d.right_value ?? <span className="text-slate-600">—</span>}
              </td>
              <td className="px-2 py-1 text-slate-400">{d.severity}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
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
