"""Generate four final result groups strictly from per-seed feeder CSV logs.

Rows marked legacy_draft/controlled/mock are rejected by default. Baseline,
attack-intensity, and ablation plots are explicitly feeder-scoped so scalability
rows cannot contaminate their statistics.
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
ABLATION_ORDER = [
    "full", "no_provenance_cap", "no_forgetting", "no_semantic_gate",
    "no_transition_quarantine", "fixed_promotion_radius",
]
ABLATION_LABELS = {
    "full": "Full", "no_provenance_cap": "No prov. cap",
    "no_forgetting": "No forgetting", "no_semantic_gate": "No sem. gate",
    "no_transition_quarantine": "No quarantine",
    "fixed_promotion_radius": "Fixed radius",
}
# Preserve the historical raw method key in per-seed logs so previously recorded
# seeds and RNG salts remain reproducible. Manuscript-facing outputs use RK-Guard.
FULL_METHOD_KEY = "KG-FedMARL"
METHOD_DISPLAY = {FULL_METHOD_KEY: "RK-Guard"}


def method_label(method):
    return METHOD_DISPLAY.get(method, method)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--output-dir", required=True)
    p.add_argument("--min-seeds", type=int, default=5)
    p.add_argument("--full-method", default=FULL_METHOD_KEY)
    p.add_argument("--baseline-feeder", default="IEEE33")
    p.add_argument("--intensity-feeder", default="IEEE33")
    p.add_argument("--ablation-feeder", default="IEEE33")
    p.add_argument("--baseline-attack-type", default="mixed")
    p.add_argument("--baseline-attack-level", default="medium")
    p.add_argument("--allowed-source-kind", action="append", choices=["simulator", "measured"], default=[])
    p.add_argument("--allow-nonreal", action="store_true")
    return p.parse_args()


def f(row, key):
    v = row.get(key, "")
    return np.nan if v == "" else float(v)


def mean_std(rows, key):
    vals = np.array([f(r, key) for r in rows], dtype=float)
    vals = vals[np.isfinite(vals)]
    if not len(vals):
        raise ValueError(f"no finite values for {key}")
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
    if not rows: return
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def plot_baseline(rows, outdir, args):
    sel = [r for r in rows if r["feeder"] == args.baseline_feeder
           and r["attack_type"] == args.baseline_attack_type
           and r["attack_level"] == args.baseline_attack_level
           and r.get("ablation", "full") in ("", "full")]
    methods = [m for m in ("Oracle-AC", "Latest-Evidence", "Static-KG", FULL_METHOD_KEY)
               if any(r["method"] == m for r in sel)]
    if len(methods) < 2: raise ValueError("end-to-end baseline needs >=2 methods")
    summary=[]; means=[]; stds=[]
    for method in methods:
        rr=[r for r in sel if r["method"]==method]
        require_seed_count(rr,args.min_seeds,f"baseline/{method}")
        aurc,aurc_sd,n=mean_std(rr,"AURC"); db,db_sd,_=mean_std(rr,"D_B")
        pfa,pfa_sd,_=mean_std(rr,"P_FA"); dpi,dpi_sd,_=mean_std(rr,"D_pi")
        means.append(aurc); stds.append(aurc_sd)
        summary.append({"feeder":args.baseline_feeder,"method":method_label(method),"seeds":n,
                        "AURC_mean":aurc,"AURC_std":aurc_sd,"D_B_mean":db,"D_B_std":db_sd,
                        "P_FA_mean":pfa,"P_FA_std":pfa_sd,"D_pi_mean":dpi,"D_pi_std":dpi_sd})
    fig,ax=plt.subplots(figsize=(3.5,2.45)); x=np.arange(len(methods))
    ax.bar(x,means,yerr=stds,capsize=3); ax.set_xticks(x)
    ax.set_xticklabels([method_label(m) for m in methods],rotation=25,ha="right")
    ax.set_ylabel("Restoration AURC"); ax.grid(True,axis="y",linestyle="--",alpha=.35)
    fig.tight_layout(); save_fig(fig,outdir,"feeder_end_to_end_baseline")
    write_summary(outdir/"feeder_end_to_end_baseline.csv",summary)


def plot_attack_intensity(rows,outdir,args):
    sel=[r for r in rows if r["feeder"]==args.intensity_feeder and r["method"]==args.full_method
         and r.get("ablation","full") in ("","full") and r["attack_level"] in ATTACK_ORDER]
    levels=sorted({r["attack_level"] for r in sel},key=lambda x:ATTACK_ORDER[x])
    if len(levels)<3: raise ValueError("attack-intensity result needs >=3 levels")
    summary=[]; means=[]; stds=[]
    for level in levels:
        rr=[r for r in sel if r["attack_level"]==level]
        require_seed_count(rr,args.min_seeds,f"attack/{level}")
        db,db_sd,n=mean_std(rr,"D_B"); aurc,aurc_sd,_=mean_std(rr,"AURC"); pfa,pfa_sd,_=mean_std(rr,"P_FA")
        means.append(db); stds.append(db_sd)
        summary.append({"feeder":args.intensity_feeder,"attack_level":level,"seeds":n,
                        "D_B_mean":db,"D_B_std":db_sd,"AURC_mean":aurc,"AURC_std":aurc_sd,
                        "P_FA_mean":pfa,"P_FA_std":pfa_sd})
    fig,ax=plt.subplots(figsize=(3.5,2.45)); x=np.arange(len(levels))
    ax.errorbar(x,means,yerr=stds,marker="o",capsize=3); ax.set_xticks(x); ax.set_xticklabels(levels)
    ax.set_ylabel(r"Belief distortion $D_B$"); ax.set_xlabel("Attack intensity"); ax.grid(True,linestyle="--",alpha=.35)
    fig.tight_layout(); save_fig(fig,outdir,"feeder_attack_intensity")
    write_summary(outdir/"feeder_attack_intensity.csv",summary)


def plot_ablation(rows,outdir,args):
    sel=[r for r in rows if r["feeder"]==args.ablation_feeder and r["method"]==args.full_method
         and r.get("ablation","")!="" and r["attack_level"]==args.baseline_attack_level]
    present={r["ablation"] for r in sel}; ablations=[a for a in ABLATION_ORDER if a in present]
    if "full" not in ablations or len(ablations)<3: raise ValueError("security ablation needs full + >=2 variants")
    summary=[]; means=[]; stds=[]
    for abl in ablations:
        rr=[r for r in sel if r["ablation"]==abl]
        require_seed_count(rr,args.min_seeds,f"ablation/{abl}")
        pfa,pfa_sd,n=mean_std(rr,"P_FA"); db,db_sd,_=mean_std(rr,"D_B")
        dpi,dpi_sd,_=mean_std(rr,"D_pi"); aurc,aurc_sd,_=mean_std(rr,"AURC")
        means.append(pfa); stds.append(pfa_sd)
        summary.append({"feeder":args.ablation_feeder,"ablation":abl,"seeds":n,
                        "P_FA_mean":pfa,"P_FA_std":pfa_sd,"D_B_mean":db,"D_B_std":db_sd,
                        "D_pi_mean":dpi,"D_pi_std":dpi_sd,"AURC_mean":aurc,"AURC_std":aurc_sd})
    fig,ax=plt.subplots(figsize=(3.5,2.55)); x=np.arange(len(ablations))
    ax.bar(x,means,yerr=stds,capsize=3); ax.set_xticks(x)
    ax.set_xticklabels([ABLATION_LABELS[a] for a in ablations],rotation=28,ha="right")
    ax.set_ylabel("False-authorization probability"); ax.grid(True,axis="y",linestyle="--",alpha=.35)
    fig.tight_layout(); save_fig(fig,outdir,"feeder_security_ablation")
    write_summary(outdir/"feeder_security_ablation.csv",summary)


def plot_scalability(rows,outdir,args):
    sel=[r for r in rows if r["method"]==args.full_method and r.get("ablation","full") in ("","full")
         and r["attack_level"]==args.baseline_attack_level]
    feeders=[]
    for name in ("IEEE33","Radial69-env","IEEE123","IEEE8500"):
        if any(r["feeder"]==name for r in sel): feeders.append(name)
    if len(feeders)<3: raise ValueError("scalability result needs >=3 feeders")
    summary=[]; nodes=[]; means=[]; stds=[]
    for feeder in feeders:
        rr=[r for r in sel if r["feeder"]==feeder]
        require_seed_count(rr,args.min_seeds,f"scale/{feeder}")
        latency,lat_sd,n=mean_std(rr,"gate_latency_ms"); aurc,aurc_sd,_=mean_std(rr,"AURC")
        fb,fb_sd,_=mean_std(rr,"fallback_rate"); nn=int(rr[0]["n_nodes"])
        nodes.append(nn); means.append(latency); stds.append(lat_sd)
        summary.append({"feeder":feeder,"n_nodes":nn,"seeds":n,"gate_latency_ms_mean":latency,
                        "gate_latency_ms_std":lat_sd,"AURC_mean":aurc,"AURC_std":aurc_sd,
                        "fallback_rate_mean":fb,"fallback_rate_std":fb_sd})
    order=np.argsort(nodes); nodes=np.array(nodes)[order]; means=np.array(means)[order]; stds=np.array(stds)[order]
    fig,ax=plt.subplots(figsize=(3.5,2.45)); ax.errorbar(nodes,means,yerr=stds,marker="o",capsize=3)
    ax.set_xscale("log"); ax.set_xlabel("Feeder buses/nodes"); ax.set_ylabel("Authorization latency (ms)")
    ax.grid(True,which="both",linestyle="--",alpha=.35); fig.tight_layout(); save_fig(fig,outdir,"feeder_scalability")
    write_summary(outdir/"feeder_scalability.csv",summary)


def main():
    args=parse_args(); rows=[r for r in read_rows(args.input) if r.get("status")=="ok"]
    if not rows: raise SystemExit("no successful rows")
    allowed=set(args.allowed_source_kind or ["simulator","measured"])
    if args.allow_nonreal: allowed.update({"controlled","mock","legacy_draft"})
    rejected=Counter(r["source_kind"] for r in rows if r["source_kind"] not in allowed)
    rows=[r for r in rows if r["source_kind"] in allowed]
    if rejected and not args.allow_nonreal: print("excluded non-final provenance rows:",dict(rejected))
    if not rows: raise SystemExit("no simulator/measured rows remain")
    for row in rows: validate(row,require_final_metrics=True)
    outdir=Path(args.output_dir); outdir.mkdir(parents=True,exist_ok=True)
    plot_baseline(rows,outdir,args); plot_attack_intensity(rows,outdir,args)
    plot_ablation(rows,outdir,args); plot_scalability(rows,outdir,args)
    print(outdir)

if __name__=="__main__": main()