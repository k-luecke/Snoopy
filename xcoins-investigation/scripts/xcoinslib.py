"""Shared library for the xCoins on-chain reconstruction.

Design goals:
- Every network response is cached verbatim on disk under raw/, keyed by
  endpoint, together with a provenance sidecar recording URL, retrieval
  timestamp, HTTP status, and SHA-256 of the body.
- Re-runs never touch the network if a cached response exists (unless
  refresh=True), so the whole analysis is reproducible offline from raw/.
- Multiple Esplora-compatible backends; the backend actually used is
  recorded in provenance.
- Conservative rate limiting.
"""

import hashlib
import json
import os
import time
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_TX_DIR = os.path.join(BASE_DIR, "raw", "transactions")
RAW_ADDR_DIR = os.path.join(BASE_DIR, "raw", "addresses")
DERIVED_DIR = os.path.join(BASE_DIR, "derived")
CRAWL_LOG = os.path.join(BASE_DIR, "reports", "crawl-log.md")

# Esplora-compatible REST backends, in preference order.
ESPLORA_BACKENDS = [
    "https://mempool.space/api",
    "https://blockstream.info/api",
]

RATE_LIMIT_SECONDS = 1.1  # be polite to public APIs
_last_fetch_at = [0.0]

USER_AGENT = "xcoins-forensic-reconstruction/0.1 (public-data research; cached; rate-limited)"


def _now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _log_crawl(line: str):
    os.makedirs(os.path.dirname(CRAWL_LOG), exist_ok=True)
    with open(CRAWL_LOG, "a") as f:
        f.write(line.rstrip() + "\n")


def _rate_limit():
    delta = time.time() - _last_fetch_at[0]
    if delta < RATE_LIMIT_SECONDS:
        time.sleep(RATE_LIMIT_SECONDS - delta)
    _last_fetch_at[0] = time.time()


def fetch_cached(endpoint_path: str, cache_dir: str, cache_key: str,
                 refresh: bool = False, expect_json: bool = True):
    """Fetch ESPLORA_BACKENDS[i] + endpoint_path with on-disk caching.

    cache_key: filename stem for the cached body + provenance sidecar.
    Returns parsed JSON (or raw text when expect_json=False), or None if
    every backend failed. Never overwrites an existing cache entry unless
    refresh=True; provenance sidecars are append-only (one JSON object per
    fetch attempt, JSONL).
    """
    os.makedirs(cache_dir, exist_ok=True)
    body_path = os.path.join(cache_dir, cache_key)
    prov_path = os.path.join(cache_dir, cache_key + ".provenance.jsonl")

    if os.path.exists(body_path) and not refresh:
        with open(body_path, "rb") as f:
            data = f.read()
        return json.loads(data) if expect_json else data.decode("utf-8", "replace")

    for backend in ESPLORA_BACKENDS:
        url = backend + endpoint_path
        _rate_limit()
        record = {"url": url, "retrieved_at": _now_iso()}
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = resp.read()
                record["http_status"] = resp.status
                record["sha256"] = _sha256(data)
        except urllib.error.HTTPError as e:
            record["http_status"] = e.code
            record["error"] = str(e)
            _append_provenance(prov_path, record)
            _log_crawl(f"- {record['retrieved_at']} FAIL {e.code} `{url}`")
            continue
        except Exception as e:  # DNS, timeout, proxy denial, ...
            record["http_status"] = None
            record["error"] = repr(e)
            _append_provenance(prov_path, record)
            _log_crawl(f"- {record['retrieved_at']} FAIL {record['error']} `{url}`")
            continue

        with open(body_path, "wb") as f:
            f.write(data)
        _append_provenance(prov_path, record)
        _log_crawl(f"- {record['retrieved_at']} OK {record['http_status']} sha256={record['sha256'][:16]}... `{url}`")
        return json.loads(data) if expect_json else data.decode("utf-8", "replace")

    return None


def _append_provenance(prov_path: str, record: dict):
    with open(prov_path, "a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")


# ---- Esplora endpoint helpers -------------------------------------------

def get_tx(txid: str, refresh: bool = False):
    """Full transaction (inputs with prevout details, outputs, status)."""
    return fetch_cached(f"/tx/{txid}", RAW_TX_DIR, f"{txid}.json", refresh)


def get_tx_outspends(txid: str, refresh: bool = False):
    """Spend status of every output of txid: [{spent, txid, vin, status}, ...]"""
    return fetch_cached(f"/tx/{txid}/outspends", RAW_TX_DIR,
                        f"{txid}.outspends.json", refresh)


def get_address(address: str, refresh: bool = False):
    """Address summary: chain_stats {funded_txo_count, funded_txo_sum, spent_txo_count, spent_txo_sum, tx_count}."""
    return fetch_cached(f"/address/{address}", RAW_ADDR_DIR,
                        f"{address}.json", refresh)


def get_address_txs(address: str, last_seen_txid: str = None, refresh: bool = False):
    """Up to 25 confirmed txs for an address, paginated by last_seen_txid."""
    if last_seen_txid:
        path = f"/address/{address}/txs/chain/{last_seen_txid}"
        key = f"{address}.txs.{last_seen_txid}.json"
    else:
        path = f"/address/{address}/txs"
        key = f"{address}.txs.json"
    return fetch_cached(path, RAW_ADDR_DIR, key, refresh)


# ---- analysis helpers ----------------------------------------------------

def sat_to_btc(sats):
    return sats / 1e8 if sats is not None else None


def tx_summary(tx: dict) -> dict:
    """Compact per-hop record from a raw Esplora tx."""
    vin_addrs = [(i.get("prevout") or {}).get("scriptpubkey_address")
                 for i in tx.get("vin", [])]
    vout = [{
        "n": n,
        "address": o.get("scriptpubkey_address"),
        "value_btc": sat_to_btc(o.get("value")),
        "type": o.get("scriptpubkey_type"),
    } for n, o in enumerate(tx.get("vout", []))]
    st = tx.get("status", {})
    return {
        "txid": tx["txid"],
        "block_height": st.get("block_height"),
        "block_time": st.get("block_time"),
        "block_time_iso": (time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st["block_time"]))
                           if st.get("block_time") else None),
        "input_count": len(tx.get("vin", [])),
        "output_count": len(tx.get("vout", [])),
        "input_addresses": vin_addrs,
        "input_total_btc": sat_to_btc(sum((i.get("prevout") or {}).get("value", 0)
                                          for i in tx.get("vin", []))),
        "outputs": vout,
        "fee_btc": sat_to_btc(tx.get("fee")),
    }


def guess_change_output(tx: dict, deposit_vout: int = None):
    """Very conservative change heuristics on an Esplora tx.

    Returns (vout_index or None, reason string). Flags, never asserts.
    Known failure cases (CoinJoin, batching, multi-party constructions)
    make any change guess unreliable; callers must retain the reason and
    treat the result as a heuristic.
    """
    vin_addrs = {(i.get("prevout") or {}).get("scriptpubkey_address")
                 for i in tx.get("vin", [])}
    vin_types = {(i.get("prevout") or {}).get("scriptpubkey_type")
                 for i in tx.get("vin", [])}
    outs = tx.get("vout", [])
    # 1) address reuse: an output paying back to an input address
    for n, o in enumerate(outs):
        if o.get("scriptpubkey_address") in vin_addrs:
            return n, "output address also appears among input addresses (address-reuse change)"
    # 2) script-type mismatch in a 2-output tx: the output matching the
    #    input script type is more likely change
    if len(outs) == 2 and len(vin_types) == 1:
        t = next(iter(vin_types))
        matching = [n for n, o in enumerate(outs) if o.get("scriptpubkey_type") == t]
        if len(matching) == 1:
            return matching[0], ("only one of two outputs matches the input script "
                                 f"type ({t}); script-type heuristic")
    return None, "no confident change heuristic applied"
