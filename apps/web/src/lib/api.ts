// Typed client for the FactCheck FastAPI backend.

import type {
  RecentSearchesResponse,
  SourceMode,
  VerifyResponse,
} from "./types";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function handle<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      // non-JSON error body — keep statusText
    }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export async function verifyClaim(
  claim: string,
  sourceMode: SourceMode,
  signal?: AbortSignal,
): Promise<VerifyResponse> {
  const res = await fetch(`${API_URL}/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim, source_mode: sourceMode }),
    signal,
  });
  return handle<VerifyResponse>(res);
}

export async function getRecentSearches(
  limit = 20,
  offset = 0,
  signal?: AbortSignal,
): Promise<RecentSearchesResponse> {
  const params = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  });
  const res = await fetch(`${API_URL}/recent-searches?${params}`, { signal });
  return handle<RecentSearchesResponse>(res);
}
