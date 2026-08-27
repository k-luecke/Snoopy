#!/usr/bin/env python3
"""Export a Mermaid flowchart of all traced seed paths (hop 1..N) from
derived/seed_paths.json, marking suspected change outputs, unspent terminals,
and nodes reached by more than one seed.

Usage: python3 export_graph.py [output.mmd]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xcoinslib as lib


def short(txid):
    return txid[:8] + ".."


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        lib.DERIVED_DIR, "seed_graph.mmd")
    with open(os.path.join(lib.DERIVED_DIR, "seed_paths.json")) as f:
        paths = json.load(f)

    seen_by = {}
    for label, p in paths.items():
        for h in p["hops"]:
            if "txid" in h:
                seen_by.setdefault(h["txid"], set()).add(label)

    lines = ["flowchart TD"]
    for label, p in paths.items():
        seed_tx = p["seed_outpoint"].split(":")[0]
        lines.append(f'  {label}_seed["seed {label}<br/>{short(seed_tx)}"]')
        prev = f"{label}_seed"
        for h in p["hops"]:
            if "txid" not in h:
                node = f'{label}_end{h["hop"]}'
                lines.append(f'  {node}(["{h.get("status") or h.get("error")}"])')
                lines.append(f"  {prev} --> {node}")
                break
            node = "tx_" + h["txid"][:12]
            multi = len(seen_by.get(h["txid"], set())) > 1
            tag = " CONVERGENCE" if multi else ""
            lines.append(
                f'  {node}["{short(h["txid"])}<br/>{h["input_count"]}in/{h["output_count"]}out'
                f'{tag}"]')
            edge_label = h.get("spent_outpoint", "")
            lines.append(f'  {prev} -->|"{edge_label.split(":")[-1] and "vout " + edge_label.split(":")[-1]}"| {node}')
            if multi:
                lines.append(f"  style {node} fill:#f9a,stroke:#f00")
            prev = node
    with open(out_path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
