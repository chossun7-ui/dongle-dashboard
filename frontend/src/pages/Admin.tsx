import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import { FtpConfigPanel } from "@/components/FtpConfigPanel";
import type { Equipment, Line, Model } from "@/types";

export default function Admin() {
  const nav = useNavigate();
  const [lines, setLines] = useState<Line[]>([]);
  const [models, setModels] = useState<Model[]>([]);
  const [equipments, setEquipments] = useState<Equipment[]>([]);

  const [newLine, setNewLine] = useState("");
  const [newModel, setNewModel] = useState("");

  const [eqName, setEqName] = useState("");
  const [eqIp, setEqIp] = useState("");
  const [eqLineId, setEqLineId] = useState<number | null>(null);
  const [eqModelId, setEqModelId] = useState<number | null>(null);

  useEffect(() => {
    refresh();
  }, []);

  const refresh = async () => {
    try {
      const [ls, ms, es] = await Promise.all([
        api.get<Line[]>("/api/lines"),
        api.get<Model[]>("/api/models"),
        api.get<Equipment[]>("/api/equipments"),
      ]);
      setLines(ls);
      setModels(ms);
      setEquipments(es);
    } catch (e) {
      if ((e as Error).message.startsWith("auth.")) {
        nav("/login", { replace: true });
      } else {
        alert((e as Error).message);
      }
    }
  };

  const addLine = async () => {
    if (!newLine.trim()) return;
    await api.post("/api/lines", { name: newLine.trim() });
    setNewLine("");
    refresh();
  };
  const addModel = async () => {
    if (!newModel.trim()) return;
    await api.post("/api/models", { name: newModel.trim() });
    setNewModel("");
    refresh();
  };
  const addEquipment = async () => {
    if (!eqName || !eqIp || !eqLineId || !eqModelId) return;
    await api.post("/api/equipments", {
      name: eqName,
      ip: eqIp,
      line_id: eqLineId,
      model_id: eqModelId,
    });
    setEqName("");
    setEqIp("");
    refresh();
  };

  const logout = async () => {
    await api.post("/api/auth/logout");
    nav("/login");
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 px-4 py-2 flex items-center justify-between">
        <h1 className="text-base font-semibold">관리자 페이지</h1>
        <nav className="flex items-center gap-3 text-sm">
          <Link to="/" className="text-slate-400 hover:text-sky-300">
            대시보드
          </Link>
          <button onClick={logout} className="text-slate-400 hover:text-rose-300">
            로그아웃
          </button>
        </nav>
      </header>

      <main className="grid grid-cols-12 gap-3 p-3">
        <Card title="라인" className="col-span-3">
          <Adder
            value={newLine}
            onChange={setNewLine}
            onAdd={addLine}
            placeholder="예: P1"
          />
          <ItemList
            items={lines.map((l) => l.name)}
            onDelete={async (i) => {
              await api.del(`/api/lines/${lines[i].id}`);
              refresh();
            }}
          />
        </Card>

        <Card title="모델" className="col-span-3">
          <Adder
            value={newModel}
            onChange={setNewModel}
            onAdd={addModel}
            placeholder="예: IRIS"
          />
          <ItemList
            items={models.map((m) => m.name)}
            onDelete={async (i) => {
              await api.del(`/api/models/${models[i].id}`);
              refresh();
            }}
          />
        </Card>

        <Card title="설비" className="col-span-6">
          <div className="grid grid-cols-4 gap-2 mb-2">
            <input
              placeholder="설비명 (MTKB561)"
              value={eqName}
              onChange={(e) => setEqName(e.target.value)}
              className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
            />
            <input
              placeholder="IP"
              value={eqIp}
              onChange={(e) => setEqIp(e.target.value)}
              className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
            />
            <select
              value={eqLineId ?? ""}
              onChange={(e) =>
                setEqLineId(e.target.value ? Number(e.target.value) : null)
              }
              className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
            >
              <option value="">라인</option>
              {lines.map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
            </select>
            <select
              value={eqModelId ?? ""}
              onChange={(e) =>
                setEqModelId(e.target.value ? Number(e.target.value) : null)
              }
              className="px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
            >
              <option value="">모델</option>
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={addEquipment}
            className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 text-sm"
          >
            추가
          </button>
          <table className="w-full mt-3 text-xs">
            <thead className="text-slate-500">
              <tr>
                <th className="text-left py-1">이름</th>
                <th className="text-left">IP</th>
                <th className="text-left">라인</th>
                <th className="text-left">모델</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {equipments.map((e) => (
                <tr key={e.id} className="border-t border-slate-800">
                  <td className="py-1">{e.name}</td>
                  <td>{e.ip}</td>
                  <td>{e.line_name}</td>
                  <td>{e.model_name}</td>
                  <td className="text-right">
                    <button
                      onClick={async () => {
                        await api.del(`/api/equipments/${e.id}`);
                        refresh();
                      }}
                      className="text-rose-400 hover:text-rose-300"
                    >
                      삭제
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <FtpConfigPanel />
      </main>
    </div>
  );
}

function Card({
  title,
  children,
  className,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-lg border border-slate-800 bg-slate-900/60 p-3 ${className ?? ""}`}
    >
      <h2 className="text-sm font-semibold text-slate-200 mb-2">{title}</h2>
      {children}
    </section>
  );
}

function Adder({
  value,
  onChange,
  onAdd,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  onAdd: () => void;
  placeholder?: string;
}) {
  return (
    <div className="flex gap-2 mb-2">
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && onAdd()}
        placeholder={placeholder}
        className="flex-1 px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
      />
      <button
        onClick={onAdd}
        className="px-2 py-1 rounded bg-sky-600 hover:bg-sky-500 text-sm"
      >
        추가
      </button>
    </div>
  );
}

function ItemList({
  items,
  onDelete,
}: {
  items: string[];
  onDelete: (idx: number) => void;
}) {
  return (
    <ul className="space-y-1 text-sm">
      {items.map((n, i) => (
        <li
          key={n}
          className="flex items-center justify-between px-2 py-1 rounded hover:bg-slate-800/40"
        >
          <span>{n}</span>
          <button
            onClick={() => onDelete(i)}
            className="text-xs text-rose-400 hover:text-rose-300"
          >
            삭제
          </button>
        </li>
      ))}
    </ul>
  );
}
