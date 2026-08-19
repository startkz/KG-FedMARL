"""Run an external feeder simulator once per seed and append standard CSV rows.

Simulator contract
------------------
The runner sets ``KG_RESULT_JSON`` to a temporary path and passes experiment
metadata through ``KG_*`` environment variables. The simulator MUST write one
JSON object to ``KG_RESULT_JSON`` containing the metrics AURC, T_crit, D_B,
P_FA, T_corr, D_pi, fallback_rate, and gate_latency_ms. Optional fields such as
recovered_final/verifier_calls/safety_violations are also accepted.

The command is executed without a shell. Example:
    python feeder_seed_runner.py ... -- python actual_simulator.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from feeder_experiment_io import FINAL_REQUIRED_METRICS, append_row, parse_seed_spec, sha256_file


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True, help="Aggregate per-seed CSV")
    p.add_argument("--seeds", default="1-5")
    p.add_argument("--feeder", required=True)
    p.add_argument("--n-nodes", type=int, required=True)
    p.add_argument("--n-agents", type=int, required=True)
    p.add_argument("--method", required=True)
    p.add_argument("--ablation", default="full")
    p.add_argument("--attack-type", default="none")
    p.add_argument("--attack-level", default="none")
    p.add_argument("--f-p", type=int, default=0)
    p.add_argument("--B-z", type=int, default=0)
    p.add_argument("--H-A", type=int, default=0)
    p.add_argument("--epsilon-s", type=float, default=0.0)
    p.add_argument("--evidence-sources", type=int, default=0)
    p.add_argument("--provenance-groups", type=int, default=0)
    p.add_argument("--prereq-per-action", type=int, default=0)
    p.add_argument("--source-kind", choices=["simulator", "measured"], default="simulator")
    p.add_argument("--source-commit", default=os.environ.get("KG_SOURCE_COMMIT", ""))
    p.add_argument("--log-dir", default=None)
    p.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")
    args = p.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        p.error("missing simulator command; append: -- python simulator.py")
    return args


def main():
    args = parse_args()
    out_csv = Path(args.output)
    log_dir = Path(args.log_dir or out_csv.parent / "run_logs")
    log_dir.mkdir(parents=True, exist_ok=True)

    failures = 0
    for seed in parse_seed_spec(args.seeds):
        with tempfile.TemporaryDirectory(prefix="kgfedmarl_result_") as td:
            result_path = Path(td) / "result.json"
            env = os.environ.copy()
            env.update({
                "KG_RESULT_JSON": str(result_path),
                "KG_SEED": str(seed),
                "KG_FEEDER": args.feeder,
                "KG_N_NODES": str(args.n_nodes),
                "KG_N_AGENTS": str(args.n_agents),
                "KG_METHOD": args.method,
                "KG_ABLATION": args.ablation,
                "KG_ATTACK_TYPE": args.attack_type,
                "KG_ATTACK_LEVEL": args.attack_level,
                "KG_F_P": str(args.f_p),
                "KG_B_Z": str(args.B_z),
                "KG_H_A": str(args.H_A),
                "KG_EPSILON_S": str(args.epsilon_s),
            })
            proc = subprocess.run(args.command, env=env, capture_output=True, text=True)
            stem = f"{args.feeder}_{args.method}_{args.attack_type}_{args.attack_level}_seed{seed}"
            raw_log = log_dir / f"{stem}.log"
            raw_log.write_text(
                "COMMAND: " + " ".join(args.command) + "\n"
                + f"RETURN_CODE: {proc.returncode}\n\nSTDOUT\n{proc.stdout}\n\nSTDERR\n{proc.stderr}\n",
                encoding="utf-8",
            )

            base = {
                "source_kind": args.source_kind,
                "source_commit": args.source_commit,
                "seed": seed,
                "feeder": args.feeder,
                "n_nodes": args.n_nodes,
                "n_agents": args.n_agents,
                "method": args.method,
                "ablation": args.ablation,
                "attack_type": args.attack_type,
                "attack_level": args.attack_level,
                "f_p": args.f_p,
                "B_z": args.B_z,
                "H_A": args.H_A,
                "epsilon_s": args.epsilon_s,
                "evidence_sources": args.evidence_sources,
                "provenance_groups": args.provenance_groups,
                "prereq_per_action": args.prereq_per_action,
                "raw_log_path": str(raw_log),
            }

            if proc.returncode != 0 or not result_path.exists():
                base.update({"status": "failed", "notes": "simulator failed or did not write KG_RESULT_JSON"})
                append_row(out_csv, base)
                failures += 1
                continue

            try:
                metrics = json.loads(result_path.read_text(encoding="utf-8"))
                if not isinstance(metrics, dict):
                    raise TypeError("result JSON must be an object")
                missing = sorted(k for k in FINAL_REQUIRED_METRICS if k not in metrics)
                if missing:
                    raise ValueError("missing metrics: " + ", ".join(missing))
                row = dict(base)
                for key in (
                    "AURC", "T_crit", "D_B", "P_FA", "T_corr", "D_pi",
                    "fallback_rate", "gate_latency_ms", "recovered_final",
                    "verifier_calls", "safety_violations", "notes"
                ):
                    if key in metrics:
                        row[key] = metrics[key]
                row["result_sha256"] = sha256_file(result_path)
                row["status"] = "ok"
                append_row(out_csv, row, require_final_metrics=True)
            except Exception as exc:
                base.update({"status": "invalid", "notes": f"invalid result JSON: {exc}"})
                append_row(out_csv, base)
                failures += 1

    if failures:
        print(f"completed with {failures} failed/invalid seed(s)", file=sys.stderr)
        return 2
    print(out_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
