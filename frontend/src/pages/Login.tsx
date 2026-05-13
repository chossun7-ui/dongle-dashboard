import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";

export default function Login() {
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await api.post("/api/auth/login", { password });
      nav("/admin", { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid place-items-center">
      <form
        onSubmit={submit}
        className="w-80 space-y-3 p-6 rounded-lg border border-slate-800 bg-slate-900/60"
      >
        <h1 className="text-lg font-semibold">관리자 로그인</h1>
        <p className="text-xs text-slate-400">
          관리자 페이지 접근에만 로그인이 필요합니다.
        </p>
        <input
          type="password"
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="비밀번호"
          className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-800 focus:border-sky-500 outline-none"
        />
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button
          disabled={busy || !password}
          className="w-full py-2 rounded bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700"
        >
          {busy ? "확인 중..." : "로그인"}
        </button>
      </form>
    </div>
  );
}
