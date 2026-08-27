#!/usr/bin/env python3
"""Fetch and cache one or more raw transactions (plus outspends) and print a
verification summary against evidence/seeds.json claims when applicable.

Usage:
    python3 fetch_tx.py <txid> [<txid> ...]
    python3 fetch_tx.py --seeds     # fetch and verify all seed txids
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xcoinslib as lib


def load_seeds():
    with open(os.path.join(lib.BASE_DIR, "evidence", "seeds.json")) as f:
        return json.load(f)["seeds"]


def verify_against_claim(tx: dict, claim: dict) -> dict:
    """Compare a raw tx against a claimed (amount, destination). Reports
    discrepancies; never mutates the claim."""
    result = {"txid": tx["txid"], "matches": [], "discrepancies": []}
    target_addr = claim["destination_address"]
    target_btc = claim["amount_btc"]
    candidates = []
    for n, o in enumerate(tx.get("vout", [])):
        if o.get("scriptpubkey_address") == target_addr:
            candidates.append((n, lib.sat_to_btc(o.get("value"))))
    if not candidates:
        result["discrepancies"].append(
            f"claimed destination {target_addr} not present in any output")
    for n, btc in candidates:
        if abs(btc - target_btc) < 1e-8:
            result["matches"].append(
                f"vout {n} pays {btc:.8f} BTC to {target_addr} (exact match)")
        else:
            result["discrepancies"].append(
                f"vout {n} pays {btc:.8f} BTC to {target_addr}, "
                f"claim says {target_btc:.8f} BTC")
    result["candidate_vouts"] = [n for n, _ in candidates]
    result["output_count"] = len(tx.get("vout", []))
    result["multiple_outputs_complicate_identification"] = (
        len(tx.get("vout", [])) > 2 and len(candidates) != 1)
    return result


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args == ["--seeds"]:
        seeds = load_seeds()
        jobs = [(s["claimed"]["txid"], s) for s in seeds]
    else:
        jobs = [(txid, None) for txid in args]

    for txid, seed in jobs:
        tx = lib.get_tx(txid)
        if tx is None:
            print(f"[FAIL] {txid}: no backend returned data (see crawl-log)")
            continue
        outspends = lib.get_tx_outspends(txid)
        summary = lib.tx_summary(tx)
        print(json.dumps(summary, indent=2))
        if seed:
            v = verify_against_claim(tx, seed["claimed"])
            print(json.dumps({"seed_verification": v}, indent=2))
        if outspends:
            for n, sp in enumerate(outspends):
                state = f"spent by {sp['txid']}:vin{sp['vin']}" if sp.get("spent") else "UNSPENT"
                print(f"  vout {n}: {state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
