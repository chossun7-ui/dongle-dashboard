// 모든 API 호출의 단일 진입점.
// 응답은 {ok, data, error} envelope 가정.

export type ApiOk<T> = { ok: true; data: T };
export type ApiErr = { ok: false; error: { code: string; message: string } };
export type ApiResp<T> = ApiOk<T> | ApiErr;

async function call<T>(input: RequestInfo, init?: RequestInit): Promise<T> {
  const res = await fetch(input, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });
  let body: ApiResp<T> | undefined;
  try {
    body = (await res.json()) as ApiResp<T>;
  } catch {
    throw new Error(`HTTP ${res.status}: 응답 JSON 파싱 실패`);
  }
  if (!body.ok) {
    throw new Error(`${body.error.code}: ${body.error.message}`);
  }
  return body.data;
}

export const api = {
  get: <T>(url: string) => call<T>(url),
  post: <T>(url: string, body?: unknown) =>
    call<T>(url, { method: "POST", body: JSON.stringify(body ?? {}) }),
  put: <T>(url: string, body?: unknown) =>
    call<T>(url, { method: "PUT", body: JSON.stringify(body ?? {}) }),
  del: <T>(url: string) => call<T>(url, { method: "DELETE" }),
};
