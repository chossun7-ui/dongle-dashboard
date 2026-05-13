import { useCallback } from "react";
import { useSearchParams } from "react-router-dom";

/**
 * URL query string에 다중선택 ID 목록을 동기화한다.
 * 새로고침/공유 URL에도 선택 상태가 유지되어 운영 시 편함.
 */
export function useIntListUrlState(key: string): [number[], (next: number[]) => void] {
  const [params, setParams] = useSearchParams();
  const raw = params.get(key);
  const value = raw
    ? raw
        .split(",")
        .map((s) => Number(s))
        .filter((n) => Number.isFinite(n))
    : [];
  const setValue = useCallback(
    (next: number[]) => {
      const newParams = new URLSearchParams(params);
      if (next.length === 0) newParams.delete(key);
      else newParams.set(key, next.join(","));
      setParams(newParams, { replace: true });
    },
    [key, params, setParams]
  );
  return [value, setValue];
}
