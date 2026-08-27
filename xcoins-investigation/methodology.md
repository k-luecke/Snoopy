# Methodology

## Scope and stance

Public-data forensic reconstruction of the wallet infrastructure plausibly
used by xCoins.io (BTC-for-PayPal marketplace, ~2016–2022). This is an
investigation, not an attribution exercise: no address is treated as xCoins
merely because it sits downstream of a suspected deposit; no allegations are
made about individuals; observations, heuristics, and confirmed facts are
kept distinct (see the evidence model below). A negative result is a valid
result.

## Evidence model

Every derived observation in `evidence/observations.jsonl` carries:

```json
{
  "claim": "...",
  "type": "onchain_observation | heuristic | external_attribution | hypothesis",
  "confidence": "high | medium | low",
  "source": "...",
  "timestamp_observed": "...",
  "supporting_data": [],
  "contradicting_data": [],
  "notes": "..."
}
```

A heuristic is never silently upgraded to a fact. Files under `evidence/`
are append-only.

## Data sources

1. **On-chain**: Esplora-compatible REST APIs (mempool.space, then
   blockstream.info), fetched by `scripts/xcoinslib.py` with:
   - verbatim response caching under `raw/` (never overwritten),
   - a provenance sidecar per cached object (`*.provenance.jsonl`) recording
     URL, retrieval timestamp, HTTP status, SHA-256 of body,
   - ≥1.1 s spacing between requests,
   - every attempt (success or failure) appended to `reports/crawl-log.md`.
   Re-runs are fully offline once the cache exists.
2. **Attribution**: public web search, archived pages (Wayback), forums,
   review sites, public label datasets — graded A–E in `evidence/sources.md`.

No CAPTCHA/auth/anti-bot circumvention. A host that refuses automated access
is dropped in favor of another legitimate source.

## Tracing protocol

- **UTXO-exact tracing** (`scripts/trace_seed.py`): from each seed we follow
  the specific outpoint `txid:vout` matching the claimed deposit, then the
  transaction spending that exact outpoint, and so on — never bare address
  history, which can mix unrelated flows.
- **Hop budget**: 6 forward hops per seed initially; 2 backward hops only if
  needed for clustering; stop-and-summarize at 500 unique transactions.
- **Fan-out control**: a spend with more than 20 outputs stops the automatic
  trace for human triage of which outputs are analytically relevant.
- **Next-hop choice** is recorded with its reason: only-output, non-change
  output per heuristic, or largest-output (explicitly flagged ambiguous).

## Change and clustering heuristics

Conservative, and every application records `heuristic_used`, `confidence`,
and `exceptions_considered`:

- change detection: address-reuse back to an input address; script-type
  mismatch in 2-output spends. Nothing else.
- common-input-ownership: applied only where transaction shape does not
  suggest CoinJoin (many equal-value outputs), collaborative construction,
  or custodial batching; these failure cases are flagged per node.

## Convergence criteria

Two seed paths "converge" if they share a transaction, an output address, an
input address, or their followed outputs pay a common address
(deposit → sweep → common-wallet pattern). Intersections land in
`derived/intersections.json` with type/confidence/caveats
(`scripts/compare_paths.py`). Amount/timing coincidence alone is never
convergence.

## Reproducibility

Deterministic pipelines over the cache:

```
python3 scripts/fetch_tx.py --seeds        # validate seeds vs claims
python3 scripts/trace_seed.py --seeds      # UTXO-exact 6-hop traces
python3 scripts/compare_paths.py           # intersections
python3 scripts/export_graph.py            # Mermaid graph
```

## Environment limitation (2026-08-27)

The current analysis environment's network egress policy denies every public
blockchain explorer and archival host (details in `evidence/sources.md` and
`reports/crawl-log.md`). On-chain steps are therefore pending; the pipeline
runs unmodified once executed in an environment permitting mempool.space or
blockstream.info (or once `raw/` is populated by any other analyst).
