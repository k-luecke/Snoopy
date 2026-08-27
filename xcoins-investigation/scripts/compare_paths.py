#!/usr/bin/env python3
"""Search for convergence between traced seed paths.

Reads derived/seed_paths.json and looks for, across every pair of seeds:
  - shared transactions (same txid reached by both paths)
  - shared output addresses
  - shared input addresses (common-input-ownership signal, with caveats)
  - "sweep into common wallet" patterns: different sweep txs whose followed
    outputs pay the same address

Writes derived/intersections.json. Purely offline over cached data;
deterministic.

Every intersection is recorded as an observation with heuristic caveats —
common-input ownership fails under CoinJoin, collaborative txs, and custodial
batching, and this script cannot rule those out by itself.
"""
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xcoinslib as lib


def path_features(p):
    txids, out_addrs, in_addrs, followed_addrs = set(), {}, {}, {}
    for h in p["hops"]:
        if "txid" not in h:
            continue
        txids.add(h["txid"])
        for a in h.get("input_addresses") or []:
            if a:
                in_addrs.setdefault(a, []).append(h["txid"])
        for o in h.get("outputs") or []:
            if o.get("address"):
                out_addrs.setdefault(o["address"], []).append(h["txid"])
        fv = h.get("followed_vout")
        if fv is not None:
            a = h["outputs"][fv].get("address")
            if a:
                followed_addrs.setdefault(a, []).append(h["txid"])
    return {"txids": txids, "out_addrs": out_addrs,
            "in_addrs": in_addrs, "followed_addrs": followed_addrs}


def main():
    paths_file = os.path.join(lib.DERIVED_DIR, "seed_paths.json")
    if not os.path.exists(paths_file):
        print("no derived/seed_paths.json yet — run trace_seed.py first")
        return 1
    with open(paths_file) as f:
        paths = json.load(f)

    feats = {k: path_features(v) for k, v in paths.items()}
    intersections = []
    for a, b in itertools.combinations(sorted(feats), 2):
        fa, fb = feats[a], feats[b]
        for kind, key in [("shared_transaction", "txids")]:
            for t in sorted(fa[key] & fb[key]):
                intersections.append({
                    "seeds": [a, b], "kind": kind, "value": t,
                    "type": "onchain_observation", "confidence": "high",
                    "notes": "both traced paths pass through this transaction"})
        for kind, key, conf, note in [
            ("shared_output_address", "out_addrs", "medium",
             "an address received outputs on both paths; may indicate a common "
             "destination wallet, or an unrelated shared counterparty"),
            ("shared_input_address", "in_addrs", "medium",
             "an address contributed inputs on both paths; common-input-ownership "
             "signal — INVALID under CoinJoin/collaborative/custodial batching"),
            ("sweep_to_common_wallet", "followed_addrs", "medium",
             "the analytically-followed outputs of both paths pay this address "
             "(classic deposit->sweep->common-wallet pattern if corroborated)"),
        ]:
            for addr in sorted(set(fa[key]) & set(fb[key])):
                intersections.append({
                    "seeds": [a, b], "kind": kind, "value": addr,
                    "via_txs": {a: fa[key][addr], b: fb[key][addr]},
                    "type": "heuristic", "confidence": conf, "notes": note})

    out = os.path.join(lib.DERIVED_DIR, "intersections.json")
    with open(out, "w") as f:
        json.dump({"intersections": intersections}, f, indent=2)
    print(f"{len(intersections)} intersection(s) -> {out}")
    for i in intersections:
        print(f"  [{i['kind']}] {i['seeds']} :: {i['value']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
