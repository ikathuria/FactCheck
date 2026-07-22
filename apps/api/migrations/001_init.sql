-- FactCheck — Turso (libSQL / SQLite) schema
-- Run this once against your Turso database, e.g.:
--   turso db shell <your-db> < apps/api/migrations/001_init.sql
-- (or paste it into the Turso web shell). Creates the result cache and the
-- `searches` table that backs the public recent-searches feed.

-- Result cache. TTL has no native support in SQLite, so `expires_at` (unix
-- epoch seconds) is enforced in the app: reads filter on it, writes sweep it.
create table if not exists cache (
  key         text primary key,   -- SHA-256 cache key
  value       text not null,       -- VerifyResponse serialized as JSON
  expires_at  integer not null     -- unix epoch seconds
);

create index if not exists cache_expires_at_idx on cache (expires_at);

-- Recent-searches feed.
create table if not exists searches (
  id          text primary key,    -- app-generated uuid4 hex
  claim       text not null,
  claim_hash  text not null,        -- SHA-256 cache key
  verdict     text not null,        -- supported | refuted | insufficient_evidence | contested
  confidence  real not null,
  source_mode text not null,        -- strict | flexible
  searched_at text not null         -- ISO 8601 UTC timestamp
);

create index if not exists searches_searched_at_idx on searches (searched_at desc);
create index if not exists searches_claim_hash_idx on searches (claim_hash);
