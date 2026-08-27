# xCoins.io On-Chain Reconstruction

Public-data forensic reconstruction of the historical Bitcoin wallet
infrastructure plausibly used by xCoins.io (BTC-for-PayPal marketplace,
~2016–2022), seeded from three candidate deposit transactions recorded in a
user's contemporaneous wallet records.

**Stance**: investigation, not attribution. Observations, heuristics, and
confirmed facts are kept distinct; competing hypotheses are maintained; a
negative result is a valid result. See `methodology.md` and `hypotheses.md`.

## Current status (2026-08-27)

**On-chain phase blocked by environment, not by findings.** The analysis
environment's network egress policy denies every public blockchain explorer
and archival host (17 hosts attempted; see `evidence/sources.md` and
`reports/crawl-log.md`). Seed validation and UTXO tracing are therefore
**pending**, with the full pipeline implemented and ready to run.

Completed so far:
- project scaffold, evidence model, reproducible fetch/trace/compare/export
  pipeline (`scripts/`),
- attribution web research: negative results for all three addresses and all
  three txids; external documentation of xCoins' custodial lender-wallet
  model, 2017 chargeback complaints, and the 2022-04-23 shutdown
  (`evidence/attribution.jsonl`, `evidence/observations.jsonl`),
- preliminary report: `reports/preliminary-findings.md`.

## Resuming the on-chain phase

Run in any environment that can reach `mempool.space` or `blockstream.info`
(e.g. this repo on a local machine, or a Claude Code environment whose
network policy allows those domains):

```
python3 scripts/fetch_tx.py --seeds        # 1. validate seeds vs claimed outputs
python3 scripts/trace_seed.py --seeds      # 2. UTXO-exact traces, 6 hops max
python3 scripts/compare_paths.py           # 3. intersections between seed paths
python3 scripts/export_graph.py            # 4. Mermaid graph of all paths
```

All responses are cached verbatim under `raw/` with URL/timestamp/status/
SHA-256 provenance; the analysis steps are deterministic over the cache and
never touch the network when the cache is present.

## Layout

```
evidence/    seeds.json (claims vs verified), observations.jsonl (append-only),
             attribution.jsonl, sources.md (graded source log)
raw/         verbatim API responses + provenance sidecars
derived/     edges.csv, nodes.csv, seed_paths.json, intersections.json, timeline.csv
scripts/     xcoinslib.py, fetch_tx.py, fetch_address.py, trace_seed.py,
             compare_paths.py, export_graph.py
reports/     preliminary-findings.md, crawl-log.md
```
