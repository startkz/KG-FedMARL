"""Export legacy hard-coded plotting arrays to the standard CSV schema.

This is provenance preservation only. The rows are tagged ``legacy_draft`` and
are excluded from publication plots by ``plot_feeder_results.py`` unless
``--allow-nonreal`` is explicitly supplied.
"""
from __future__ import annotations

import argparse
import runpy
from pathlib import Path

from feeder_experiment_io import append_row


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--legacy-script", default="kgfedmarl_experiment_figures.py")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    ns = runpy.run_path(args.legacy_script)
    feeders = ns.get("FEEDERS", [])
    scalability = ns.get("SCALABILITY", {})
    robustness = ns.get("ROBUSTNESS", {})
    scenarios = ns.get("SCENARIOS", [])

    for method, values in scalability.items():
        for feeder, value in zip(feeders, values):
            append_row(args.output, {
                "source_kind": "legacy_draft", "seed": -1, "feeder": str(feeder),
                "n_nodes": int(feeder), "n_agents": 0, "method": method,
                "ablation": "full", "attack_type": "legacy_scalability",
                "attack_level": "unspecified", "AURC": float(value) / 100.0,
                "status": "ok",
                "notes": "exported from hard-coded legacy plotting array; not seed-level measured evidence",
            })
    for method, values in robustness.items():
        for scenario, value in zip(scenarios, values):
            append_row(args.output, {
                "source_kind": "legacy_draft", "seed": -1, "feeder": "unspecified",
                "n_nodes": 0, "n_agents": 0, "method": method, "ablation": "full",
                "attack_type": str(scenario), "attack_level": "unspecified",
                "recovered_final": float(value) / 100.0, "status": "ok",
                "notes": "exported from hard-coded legacy plotting array; not seed-level measured evidence",
            })
    print(Path(args.output))


if __name__ == "__main__":
    main()
