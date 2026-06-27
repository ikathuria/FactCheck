-- FactCheck — Supabase schema
-- Run this once in the Supabase SQL editor (Dashboard -> SQL Editor -> New query).
-- Creates the `searches` table that backs the public recent-searches feed.

create table if not exists searches (
  id uuid primary key default gen_random_uuid(),
  claim text not null,
  claim_hash text not null,         -- SHA-256 cache key
  verdict text not null,            -- supported | refuted | insufficient_evidence | contested
  confidence float not null,
  source_mode text not null,        -- strict | flexible
  searched_at timestamptz not null default now()
);

create index if not exists searches_searched_at_idx on searches (searched_at desc);
create index if not exists searches_claim_hash_idx on searches (claim_hash);

-- The backend uses the service-role key (which bypasses RLS), so explicit RLS
-- policies are not required for the API to read/write. If you later expose this
-- table to the anon key, enable RLS and add appropriate policies.
