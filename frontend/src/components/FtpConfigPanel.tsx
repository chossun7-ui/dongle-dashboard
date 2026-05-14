import { useEffect, useState } from "react";
import { api } from "@/lib/api";

interface FtpConfig {
  username: string;
  default_port: number;
  default_mode: "PASV" | "ACTIVE";
  encoding_priority: string;
  as_regex: string;
  cache_ttl_sec: number;
  password_set: boolean;
}

/**
 * FTP 전역 설정 + as 정규식 + 인코딩 우선순위 + 캐시 TTL 패널.
 * 비번은 입력하지 않으면 기존 값을 유지한다.
 */
export function FtpConfigPanel() {
  const [cfg, setCfg] = useState<FtpConfig | null>(null);
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  useEffect(() => {
    refresh();
  }, []);

  const refresh = async () => {
    try {
      const c = await api.get<FtpConfig | null>("/api/ftp-config");
      setCfg(
        c ?? {
          username: "",
          default_port: 21,
          default_mode: "PASV",
          encoding_priority: "utf-8,cp949,auto",
          as_regex: "^as\\d+$",
          cache_ttl_sec: 0,
          password_set: false,
        }
      );
    } catch (e) {
      setMsg((e as Error).message);
    }
  };

  const save = async () => {
    if (!cfg) return;
    setBusy(true);
    setMsg(null);
    try {
      await api.put("/api/ftp-config", {
        username: cfg.username,
        password: password || null,
        default_port: Number(cfg.default_port),
        default_mode: cfg.default_mode,
        encoding_priority: cfg.encoding_priority,
        as_regex: cfg.as_regex,
        cache_ttl_sec: Number(cfg.cache_ttl_sec),
      });
      setMsg("저장 완료");
      setPassword("");
      refresh();
    } catch (e) {
      setMsg((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  if (!cfg) return null;

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-3 col-span-12">
      <h2 className="text-sm font-semibold text-slate-200 mb-3">
        FTP 전역 설정 · 스캔 규칙
      </h2>
      <div className="grid grid-cols-12 gap-3">
        <Field label="FTP 사용자명" className="col-span-3">
          <input
            value={cfg.username}
            onChange={(e) => setCfg({ ...cfg, username: e.target.value })}
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
          />
        </Field>
        <Field
          label={
            cfg.password_set
              ? "FTP 비번 (변경 시 입력. 비우면 유지)"
              : "FTP 비번 (최초 등록 — 필수)"
          }
          className="col-span-3"
        >
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
            placeholder={cfg.password_set ? "••••••••" : "필수"}
          />
        </Field>
        <Field label="기본 포트" className="col-span-2">
          <input
            type="number"
            value={cfg.default_port}
            onChange={(e) =>
              setCfg({ ...cfg, default_port: Number(e.target.value) })
            }
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
          />
        </Field>
        <Field label="기본 모드" className="col-span-2">
          <select
            value={cfg.default_mode}
            onChange={(e) =>
              setCfg({
                ...cfg,
                default_mode: e.target.value as "PASV" | "ACTIVE",
              })
            }
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
          >
            <option value="PASV">PASV (권장)</option>
            <option value="ACTIVE">ACTIVE</option>
          </select>
        </Field>
        <Field label="캐시 TTL (초) — 0=수동만" className="col-span-2">
          <input
            type="number"
            value={cfg.cache_ttl_sec}
            onChange={(e) =>
              setCfg({ ...cfg, cache_ttl_sec: Number(e.target.value) })
            }
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm"
          />
        </Field>
        <Field
          label="인코딩 우선순위 (콤마, 'auto'는 chardet 자동 감지)"
          className="col-span-6"
        >
          <input
            value={cfg.encoding_priority}
            onChange={(e) =>
              setCfg({ ...cfg, encoding_priority: e.target.value })
            }
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm font-mono"
          />
        </Field>
        <Field label="as 폴더 정규식" className="col-span-6">
          <input
            value={cfg.as_regex}
            onChange={(e) => setCfg({ ...cfg, as_regex: e.target.value })}
            className="w-full px-2 py-1 bg-slate-950 border border-slate-800 rounded text-sm font-mono"
          />
        </Field>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <button
          onClick={save}
          disabled={busy}
          className="px-3 py-1.5 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 text-sm"
        >
          {busy ? "저장 중..." : "저장"}
        </button>
        {msg && <span className="text-xs text-slate-400">{msg}</span>}
      </div>
    </section>
  );
}

function Field({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className}>
      <div className="text-xs text-slate-400 mb-1">{label}</div>
      {children}
    </div>
  );
}
