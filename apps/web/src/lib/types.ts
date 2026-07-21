// Mirrors the backend Pydantic models in apps/api/src/lib/types.py.
// Keep in sync with the API contract.

export type Verdict =
  | "supported"
  | "refuted"
  | "contested"
  | "insufficient_evidence";

export type SourceMode = "strict" | "flexible";

export type DomainType =
  | "government"
  | "academic"
  | "established_news"
  | "other";

export interface Source {
  url: string;
  title: string;
  snippet: string;
  credibility_score: number;
  domain_type: DomainType;
}

export interface VerifyResponse {
  claim: string;
  verdict: Verdict;
  confidence: number;
  reasoning: string;
  sources: Source[];
  cached: boolean;
  cached_at: string | null;
  ttl_expires_at: string | null;
  sub_claims: string[];
  source_mode: SourceMode;
  source_mode_fallback: boolean;
}

export interface RecentSearch {
  id: string;
  claim: string;
  verdict: Verdict;
  confidence: number;
  source_mode: SourceMode;
  searched_at: string;
}

export interface RecentSearchesResponse {
  searches: RecentSearch[];
  total: number;
}
