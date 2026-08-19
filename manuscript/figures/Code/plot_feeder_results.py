"""Generate publication result groups strictly from per-seed feeder CSV logs.

By default, rows marked ``legacy_draft``, ``controlled`` or ``mock`` are rejected.
The script writes group-level summary CSVs and publication PDF/PNG/EPS figures.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from feeder_experiment_io import read_rows, validate

ATTACK_ORDER = {"none": 0, "low": 1, "medium": 2, "high": 3}


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--min-seeds", type=int, default=5)
    p.add_argument("--full-method", default="KG-FedMARL")
    p.add_argument("--baseline-attack-type", default="mixed")
    p.add_argument("--baseline-attack-level", default="medium")
    p.add_argument("--allowed-source-kind", action="append", choices=["simulator", "measured"], default=[])
    p.add_argument("--allow-nonreal", action="store_true", help="Smoke-test only; allow controlled/mock/legacy rows")
    return p.parse_args()


def f(row, key):
    v = row.get(key, "")
    return np.nan if v == "" else float(v)


def mean_std(rows, key):
    vals = np.array([f(r, key) for r in rows], dtype=float)
    vals = vals[np.isfinite(vals)]
    return float(vals.mean()), float(vals.std(ddof=1) if len(vals) > 1 else 0.0), len(vals)


def require_seed_count(rows, min_seeds, label):
    seeds = {int(r["seed"]) for r in rows if r.get("status") == "ok"}
    if len(seeds) < min_seeds:
        raise ValueError(f"{label}: only {len(seeds)} unique seeds; need >= {min_seeds}")


def save_fig(fig, outdir, stem):
    for ext in ("pdf", "png", "eps"):
        fig.savefig(outdir / f"{stem}.{ext}", bbox_inches="tight", dpi=600)
    plt.close(fig)


def write_summary(path, rows):
    if not rows:
        return
    keys = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def plot_baseline(rows, outdir, args):
    sel = [r for r in rows if r["attack_type"] == args.baseline_attack_type and r["attack_level"] == args.baseline_attack_level and r.get("ablation", "full") in ("", "full")]
    methods = sorted({r["method"] for r in sel})
    if len(methods) < 2:
        raise ValueError("end-to-end baseline needs >=2 methods for the requested attack slice")
    summary = []
    means, stds = [], []
    for method in methods:
        rr = [r for r in sel if r["method"] == method]
        require_seed_count(rr, args.min_seeds, f"baseline/{method}")
        aurc, aurc_sd, n = mean_std(rr, "AURC")
        db, db_sd, _ = mean_std(rr, "D_B")
        pfa, pfa_sd, _ = mean_std(rr, "P_FA")
        dpi, dpi_sd, _ = mean_std(rr, "D_pi")
        means.append(aurc)
        stds.append(aurc_sd)
        summary.append({
            "method": method, "seeds": n,
            "AURC_mean": aurc, "AURC_std": aurc_sd,
            "D_B_mean": db, "D_B_std": db_sd,
            "P_FA_mean": pfa, "P_FA_std": pfa_sd,
            "D_pi_mean": dpi, "D_pi_std": dpi_sd,
        })
    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    x = np.arange(len(methods))
    ax.bar(x, means, yerr=stds, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(methods, rotation=25, ha="right")
    ax.set_ylabel("Restoration AURC")
    ax.set_xlabel("Method")
    ax.grid(True, axis="y", linestyle="--", alpha=.35)
    fig.tight_layout()
    save_fig(fig, outdir, "feeder_end_to_end_baseline")
    write_summary(outdir / "feeder_end_to_end_baseline.csv", summary)


def plot_attack_intensity(rows, outdir, args):
    sel = [r for r in rows if r["method"] == args.full_method and r.get("ablation", "full") in ("", "full") and r["attack_level"] in ATTACK_ORDER]
    levels = sorted({r["attack_level"] for r in sel}, key=lambda x: ATTACK_ORDER[x])
    if len(levels) < 3:
        raise ValueError("attack-intensity result needs >=3 attack levels")
    summary = []
    means, stds = [], []
    for level in levels:
        rr = [r for r in sel if r["attack_level"] == level]
        require_seed_count(rr, args.min_seeds, f"attack-intensity/{level}")
        db, db_sd, n = mean_std(rr, "D_B")
        aurc, aurc_sd, _ = mean_std(rr, "AURC")
        pfa, pfa_sd, _ = mean_std(rr, "P_FA")
        means.append(db)
        stds.append(db_sd)
        summary.append({
            "attack_level": level, "seeds": n,
            "D_B_mean": db, "D_B_std": db_sd,
            "AURC_mean": aurc, "AURC_std": aurc_sd,
            "P_FA_mean": pfa, "P_FA_std": pfa_sd,
        })
    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    x = np.arange(len(levels))
    ax.errorbar(x, means, yerr=stds, marker="o", capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(levels)
    ax.set_ylabel(r"Belief distortion $D_B$")
    ax.set_xlabel("Attack intensity")
    ax.grid(True, linestyle="--", alpha=.35)
    fig.tight_layout()
    save_fig(fig, outdir, "feeder_attack_intensity")
    write_summary(outdir / "feeder_attack_intensity.csv", summary)


def plot_ablation(rows, outdir, args):
    sel = [r for r in rows if r["method"] == args.full_method and r.get("ablation", "") != "" and r["attack_level"] == args.baseline_attack_level]
    ablations = sorted({r["ablation"] for r in sel})
    if "full" not in ablations or len(ablations) < 3:
        raise ValueError("security ablation needs 'full' plus >=2 ablations")
    summary = []
    means, stds = [], []
    for ablation in ablations:
        rr = [r for r in sel if r["ablation"] == ablation]
        require_seed_count(rr, args.min_seeds, f"ablation/{ablation}")
        pfa, pfa_sd, n = mean_std(rr, "P_FA")
        db, db_sd, _ = mean_std(rr, "D_B")
        dpi, dpi_sd, _ = mean_std(rr, "D_pi")
        aurc, aurc_sd, _ = mean_std(rr, "AURC")
        means.append(pfa)
        stds.append(pfa_sd)
        summary.append({
            "ablation": ablation, "seeds": n,
            "P_FA_mean": pfa, "P_FA_std": pfa_sd,
            "D_B_mean": db, "D_B_std": db_sd,
            "D_pi_mean": dpi, "D_pi_std": dpi_sd,
            "AURC_mean": aurc, "AURC_std": aurc_sd,
        })
    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    x = np.arange(len(ablations))
    ax.bar(x, means, yerr=stds, capsize=3)
    ax.set_xticks(x)
    ax.set_xticklabels(ablations, rotation=28, ha="right")
    ax.set_ylabel("False-authorization probability")
    ax.set_xlabel("Security-boundary ablation")
    ax.grid(True, axis="y", linestyle="--", alpha=.35)
    fig.tight_layout()
    save_fig(fig, outdir, "feeder_security_ablation")
    write_summary(outdir / "feeder_security_ablation.csv", summary)


def plot_scalability(rows, outdir, args):
    sel = [r for r in rows if r["method"] == args.full_method and r.get("ablation", "full") in ("", "full") and r["attack_level"] == args.baseline_attack_level]
    nodes = sorted({int(r["n_nodes"]) for r in sel if r.get("n_nodes", "") != ""})
    if len(nodes) < 3:
        raise ValueError("scalability result needs >=3 feeder sizes")
    summary = []
    means, stds = [], []
    for n_nodes in nodes:
        rr = [r for r in sel if int(r["n_nodes"]) == n_nodes]
        require_seed_count(rr, args.min_seeds, f"scalability/{n_nodes}")
        latency, latency_sd, n = mean_std(rr, "gate_latency_ms")
        aurc, aurc_sd, _ = mean_std(rr, "AURC")
        fallback, fallback_sd, _ = mean_std(rr, "fallback_rate")
        means.append(latency)
        stds.append(latency_sd)
        summary.append({
            "n_nodes": n_nodes, "seeds": n,
            "gate_latency_ms_mean": latency, "gate_latency_ms_std": latency_sd,
            "AURC_mean": aurc, "AURC_std": aurc_sd,
            "fallback_rate_mean": fallback, "fallback_rate_std": fallback_sd,
        })
    fig, ax = plt.subplots(figsize=(3.5, 2.45))
    ax.errorbar(nodes, means, yerr=stds, marker="o", capsize=3)
    ax.set_xscale("log")
    ax.set_xlabel("Feeder nodes")
    ax.set_ylabel("Gate latency (ms)")
    ax.grid(True, linestyle="--", alpha=.35)
    fig.tight_layout()
    save_fig(fig, outdir, "feeder_scalability")
    write_summary(outdir / "feeder_scalability.csv", summary)


def main():
    args = parse_args()
    rows = [r for r in read_rows(args.input) if r.get("status") == "ok"]
    if not rows:
        raise SystemExit("no successful rows")
    allowed = set(args.allowed_source_kind or ["simulator", "measured"])
    if args.allow_nonreal:
        allowed.update({"controlled", "mock", "legacy_draft"})
    rejected = Counter(r["source_kind"] for r in rows if r["source_kind"] not in allowed)
    rows = [r for r in rows if r["source_kind"] in allowed]
    if rejected and not args.allow_nonreal:
        print("excluded non-final provenance rows:", dict(rejected))
    if not rows:
        raise SystemExit("no simulator/measured rows remain after provenance filtering")
    for row in rows:
        validate(row, require_final_metrics=True)
    outdir = Path(args.output_dir)
    outdir.mkdir(parents=True, exist_ok=True)
    plot_baseline(rows, outdir, args)
    plot_attack_intensity(rows, outdir, args)
    plot_ablation(rows, outdir, args)
    plot_scalability(rows, outdir, args)
    print(outdir)


if __name__ == "__main__":
    main()
