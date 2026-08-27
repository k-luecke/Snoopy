#!/usr/bin/env python3
"""Trace the EXACT seed UTXO forward through the spend graph, hop by hop.

This deliberately does NOT crawl address history. At every hop it follows one
chosen outpoint (txid:vout) to the transaction that spends it, records the
hop, chooses the next outpoint to follow, and stops after --max-hops
(default 6), on an unspent output, or when the fan-out is too ambiguous to
pick a single analytically relevant output without human review.

Next-outpoint policy (recorded per hop as 'follow_reason'):
  1. If the spending tx has one output, follow it ("only output").
  2. If a conservative change heuristic identifies change, follow the
     NON-change output(s); if exactly one, follow it ("non-change output").
  3. Otherwise follow the largest-value output ("largest output; ambiguous —
     flagged for review") and flag the hop.

Output: appends/updates derived/seed_paths.json (per-seed hop list),
derived/nodes.csv, derived/edges.csv. Deterministic given the cache.

Usage:
    python3 trace_seed.py --seeds            # trace all seeds from evidence/seeds.json
    python3 trace_seed.py <txid> <vout> [--max-hops N] [--label NAME]
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xcoinslib as lib

MAX_HOPS_DEFAULT = 6
FANOUT_REVIEW_THRESHOLD = 20  # >N outputs: stop and flag for human review


def spend_of(txid: str, vout: int):
    outspends = lib.get_tx_outspends(txid)
    if outspends is None or vout >= len(outspends):
        return None
    sp = outspends[vout]
    return sp if sp.get("spent") else {"spent": False}


def trace(label: str, txid: str, vout: int, max_hops: int):
    hops = []
    cur_txid, cur_vout = txid, vout
    for hop_no in range(1, max_hops + 1):
        sp = spend_of(cur_txid, cur_vout)
        if sp is None:
            hops.append({"hop": hop_no, "error": f"could not fetch outspends of {cur_txid}"})
            break
        if not sp.get("spent"):
            hops.append({"hop": hop_no, "outpoint": f"{cur_txid}:{cur_vout}",
                         "status": "UNSPENT — path terminates with funds still at rest"})
            break
        spend_txid = sp["txid"]
        tx = lib.get_tx(spend_txid)
        if tx is None:
            hops.append({"hop": hop_no, "error": f"could not fetch {spend_txid}"})
            break
        s = lib.tx_summary(tx)
        change_vout, change_reason = lib.guess_change_output(tx)
        addr_reuse = sorted(
            {a for a in s["input_addresses"] if a}
            & {o["address"] for o in s["outputs"] if o["address"]})

        hop = {
            "hop": hop_no,
            "spent_outpoint": f"{cur_txid}:{cur_vout}",
            "via_input_index": sp.get("vin"),
            **s,
            "suspected_change_vout": change_vout,
            "change_heuristic_reason": change_reason,
            "address_reuse_in_out": addr_reuse,
        }

        # choose next outpoint
        outs = s["outputs"]
        if len(outs) == 1:
            nxt, why = 0, "only output"
        elif change_vout is not None and len(outs) == 2:
            nxt = 1 - change_vout
            why = "non-change output per heuristic"
        elif len(outs) > FANOUT_REVIEW_THRESHOLD:
            hop["follow_reason"] = (f"fan-out of {len(outs)} outputs exceeds review "
                                    "threshold; stopping for human triage")
            hops.append(hop)
            break
        else:
            nxt = max(range(len(outs)), key=lambda n: outs[n]["value_btc"] or 0)
            why = "largest output; ambiguous — flagged for review"
            hop["ambiguous_follow"] = True
        hop["followed_vout"] = nxt
        hop["follow_reason"] = why
        hops.append(hop)
        cur_txid, cur_vout = s["txid"], nxt
    return hops


def write_outputs(label, txid, vout, hops):
    os.makedirs(lib.DERIVED_DIR, exist_ok=True)
    paths_file = os.path.join(lib.DERIVED_DIR, "seed_paths.json")
    paths = {}
    if os.path.exists(paths_file):
        with open(paths_file) as f:
            paths = json.load(f)
    paths[label] = {"seed_outpoint": f"{txid}:{vout}", "hops": hops}
    with open(paths_file, "w") as f:
        json.dump(paths, f, indent=2)

    # nodes/edges rebuilt deterministically from ALL recorded paths
    nodes, edges = {}, []
    for lbl, p in paths.items():
        prev = p["seed_outpoint"].split(":")[0]
        nodes.setdefault(prev, {"txid": prev, "roles": set()})["roles"].add(f"seed:{lbl}")
        for h in p["hops"]:
            if "txid" not in h:
                continue
            nodes.setdefault(h["txid"], {"txid": h["txid"], "roles": set()})
            nodes[h["txid"]]["roles"].add(f"hop{h['hop']}:{lbl}")
            edges.append({"from_tx": prev, "outpoint": h.get("spent_outpoint"),
                          "to_tx": h["txid"], "seed": lbl, "hop": h["hop"]})
            prev = h["txid"]
    with open(os.path.join(lib.DERIVED_DIR, "nodes.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["txid", "roles"])
        for n in sorted(nodes):
            w.writerow([n, ";".join(sorted(nodes[n]["roles"]))])
    with open(os.path.join(lib.DERIVED_DIR, "edges.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["from_tx", "outpoint", "to_tx", "seed", "hop"])
        for e in edges:
            w.writerow([e["from_tx"], e["outpoint"], e["to_tx"], e["seed"], e["hop"]])


def main():
    argv = sys.argv[1:]
    max_hops = MAX_HOPS_DEFAULT
    if "--max-hops" in argv:
        i = argv.index("--max-hops")
        max_hops = int(argv[i + 1]); del argv[i:i + 2]

    jobs = []
    if "--seeds" in argv:
        with open(os.path.join(lib.BASE_DIR, "evidence", "seeds.json")) as f:
            for s in json.load(f)["seeds"]:
                txid = s["claimed"]["txid"]
                tx = lib.get_tx(txid)
                if tx is None:
                    print(f"[FAIL] cannot fetch seed tx {txid}")
                    continue
                target = s["claimed"]["destination_address"]
                vouts = [n for n, o in enumerate(tx["vout"])
                         if o.get("scriptpubkey_address") == target]
                if len(vouts) != 1:
                    print(f"[WARN] {s['seed_id']}: {len(vouts)} outputs pay claimed "
                          f"destination; tracing each")
                for v in vouts:
                    jobs.append((s["seed_id"] if len(vouts) == 1
                                 else f"{s['seed_id']}#v{v}", txid, v))
    else:
        label = "manual"
        if "--label" in argv:
            i = argv.index("--label")
            label = argv[i + 1]; del argv[i:i + 2]
        jobs.append((label, argv[0], int(argv[1])))

    for label, txid, vout in jobs:
        print(f"=== tracing {label}: {txid}:{vout} (max {max_hops} hops) ===")
        hops = trace(label, txid, vout, max_hops)
        write_outputs(label, txid, vout, hops)
        for h in hops:
            if "txid" in h:
                print(f"  hop {h['hop']}: {h['spent_outpoint']} -> {h['txid']} "
                      f"({h['input_count']} in / {h['output_count']} out, "
                      f"follow vout {h.get('followed_vout')}: {h.get('follow_reason')})")
            else:
                print(f"  hop {h['hop']}: {h.get('status') or h.get('error')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
