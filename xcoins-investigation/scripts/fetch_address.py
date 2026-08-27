#!/usr/bin/env python3
"""Fetch and cache an address summary plus (optionally) its transaction pages.

Usage:
    python3 fetch_address.py <address> [--txs] [--max-pages N]

Note for analysis: address-level history can mix unrelated flows. UTXO-level
tracing (trace_seed.py) is authoritative for path work; address summaries are
used for reuse statistics, deposit-address one-timeness, and residual-balance
questions only.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xcoinslib as lib


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    want_txs = "--txs" in sys.argv
    max_pages = 4
    if "--max-pages" in sys.argv:
        max_pages = int(sys.argv[sys.argv.index("--max-pages") + 1])
    if not args:
        print(__doc__)
        return 1

    for address in args:
        info = lib.get_address(address)
        if info is None:
            print(f"[FAIL] {address}: no backend returned data")
            continue
        cs = info.get("chain_stats", {})
        funded = lib.sat_to_btc(cs.get("funded_txo_sum", 0))
        spent = lib.sat_to_btc(cs.get("spent_txo_sum", 0))
        print(json.dumps({
            "address": address,
            "tx_count": cs.get("tx_count"),
            "funded_txo_count": cs.get("funded_txo_count"),
            "spent_txo_count": cs.get("spent_txo_count"),
            "total_received_btc": funded,
            "total_spent_btc": spent,
            "current_balance_btc": (funded - spent) if funded is not None else None,
            "one_time_deposit_pattern": (
                cs.get("funded_txo_count") == 1 and cs.get("spent_txo_count") == 1),
        }, indent=2))

        if want_txs:
            last = None
            for page in range(max_pages):
                txs = lib.get_address_txs(address, last)
                if not txs:
                    break
                print(f"  page {page}: {len(txs)} txs "
                      f"({txs[0]['txid'][:12]}.. -> {txs[-1]['txid'][:12]}..)")
                if len(txs) < 25:
                    break
                last = txs[-1]["txid"]
    return 0


if __name__ == "__main__":
    sys.exit(main())
