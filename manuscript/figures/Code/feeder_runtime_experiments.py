"""Run the real feeder-level KG-FedMARL experiment suite and emit per-seed CSV.

The suite uses a common priority candidate policy for every baseline. This makes
the end-to-end comparison a test of recovery-knowledge integrity and
authorization rather than a comparison between unrelated RL architectures.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
import zipfile
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from feeder_experiment_io import append_row
from feeder_runtime_core import (
    ATTACK_BUDGETS, BELIEF_THRESHOLD, EPS_CORR, LAMBDA_F, STEPS,
    BeliefState, availability_schedule, evidence_for_step, latest_estimate,
    softmax, tv_cat, update_policy,
)
from feeder_runtime_models import INITIAL_BLOCK_FRACTION, N_AGENTS, make_adapter

METHODS = ("Oracle-AC", "Latest-Evidence", "Static-KG", "KG-FedMARL")
ABLATIONS = (
    "full", "no_provenance_cap", "no_forgetting", "no_semantic_gate",
    "no_transition_quarantine", "fixed_promotion_radius",
)


def choose_block(method: str, ablation: str, pending: Sequence[int], block_kw: np.ndarray,
                 belief: np.ndarray, latest: np.ndarray, static_avail: np.ndarray,
                 true_now: np.ndarray, logits: np.ndarray):
    candidates = []
    for b in pending:
        if method == "Oracle-AC":
            ok = bool(true_now[b])
        elif method == "Latest-Evidence":
            ok = bool(latest[b])
        elif method == "Static-KG":
            ok = bool(static_avail[b])
        else:
            ok = ablation == "no_semantic_gate" or belief[b] >= BELIEF_THRESHOLD
        if ok:
            candidates.append(int(b))
    if not candidates:
        return None
    scale = max(1e-9, float(np.max(block_kw)))
    return max(candidates, key=lambda b: float(block_kw[b]) / scale + 0.12 * float(logits[b]))


def run_episode(adapter, seed: int, method: str, attack_level: str, ablation: str = "full"):
    budget = ATTACK_BUDGETS[attack_level]
    salt = sum(map(ord, method + ablation + attack_level))
    rng_attack = np.random.default_rng(seed * 7919 + salt)
    rng_clean = np.random.default_rng(seed * 7919 + 17)
    n = len(adapter.blocks)
    schedule = availability_schedule(seed, STEPS, n)
    static_avail = schedule[0].copy()
    attacked = BeliefState(
        n,
        lambda_f=1.0 if ablation == "no_forgetting" else LAMBDA_F,
        group_cap=ablation != "no_provenance_cap",
    )
    clean = BeliefState(n)
    adapter.initialize_partial(INITIAL_BLOCK_FRACTION)
    pending = [i for i in range(n) if i not in adapter.enabled_blocks]
    served = [adapter.served_ratio]
    false_auth = attempts = fallbacks = decision_opportunities = 0
    latencies = []
    db_trace = []
    logits_a = np.zeros(n, dtype=float)
    logits_0 = np.zeros(n, dtype=float)

    for step in range(STEPS):
        ev0 = evidence_for_step(schedule, step, budget, rng_clean, attacked=False)
        evA = evidence_for_step(schedule, step, budget, rng_attack, attacked=(method != "Oracle-AC"))
        clean.update(ev0, step); attacked.update(evA, step)
        p0, pA = clean.probs(), attacked.probs()
        db_trace.append(float(np.mean(np.abs(pA - p0))))
        latestA = latest_estimate(evA, n)
        latest0 = latest_estimate(ev0, n)

        had_pending = bool(pending)
        if had_pending:
            decision_opportunities += 1
        tg = time.perf_counter()
        action = choose_block(method, ablation, pending, adapter.block_kw, pA, latestA,
                              static_avail, schedule[step], logits_a)
        latency = (time.perf_counter() - tg) * 1000.0
        ref_action = choose_block("KG-FedMARL", "full", pending, adapter.block_kw, p0, latest0,
                                  static_avail, schedule[step], logits_0)

        restored = false = False
        if action is None:
            # Once all restoration blocks have been completed there is no
            # decision opportunity and therefore no fallback event.
            if had_pending:
                fallbacks += 1
        else:
            attempts += 1
            if not bool(schedule[step, action]):
                # Ground truth is used here only to score semantic false
                # authorization in the experiment harness; the invalid action is
                # not committed to the physical simulator.
                false_auth += 1; fallbacks += 1; false = True
            else:
                ok, physical_ms = adapter.try_restore(action)
                latency += physical_ms
                if ok:
                    restored = True
                    if action in pending:
                        pending.remove(action)
                else:
                    fallbacks += 1
        if had_pending:
            latencies.append(latency)

        trust = float(pA[action]) if action is not None else 0.5
        if false:
            trust *= 0.35
        reward = 1.0 if restored else (-0.60 if false else -0.15)
        logits_a = update_policy(
            logits_a, action, reward, trust,
            quarantine=ablation != "no_transition_quarantine",
            fixed_radius=ablation == "fixed_promotion_radius",
        )
        if ref_action is not None:
            r0 = 1.0 if bool(schedule[step, ref_action]) else -0.15
            logits_0 = update_policy(logits_0, ref_action, r0, float(p0[ref_action]),
                                     quarantine=True, fixed_radius=False)
        served.append(adapter.served_ratio)

    served = np.asarray(served, dtype=float)
    aurc = float(np.trapezoid(served, dx=1.0) / max(1, len(served) - 1))
    hit = np.where(served >= 0.90)[0]
    tcrit = float(hit[0]) if len(hit) else float(STEPS + 1)
    attack_end = 2 + int(budget["H_A"])
    tcorr = 0.0
    if int(budget["H_A"]) > 0:
        tcorr = float(STEPS + 1)
        for t in range(min(attack_end, len(db_trace)), len(db_trace)):
            if db_trace[t] <= EPS_CORR:
                tcorr = float(t - attack_end + 1); break
    return {
        "AURC": aurc,
        "T_crit": tcrit,
        "D_B": float(max(db_trace) if db_trace else 0.0),
        "P_FA": float(false_auth / max(1, attempts)),
        "T_corr": tcorr,
        "D_pi": tv_cat(softmax(logits_a), softmax(logits_0)),
        "fallback_rate": float(fallbacks / max(1, decision_opportunities)),
        "gate_latency_ms": float(np.mean(latencies)) if latencies else 0.0,
        "recovered_final": float(served[-1]),
        "verifier_calls": int(adapter.verifier_calls),
        "safety_violations": int(adapter.safety_violations),
        "n_nodes": int(adapter.n_nodes),
    }


def make_row(seed: int, feeder: str, method: str, ablation: str, level: str,
             metrics: Mapping[str, float], source_commit: str, notes: str = ""):
    b = ATTACK_BUDGETS[level]
    return {
        "source_kind": "simulator", "source_commit": source_commit,
        "seed": seed, "feeder": feeder, "n_nodes": metrics["n_nodes"],
        "n_agents": N_AGENTS[feeder], "method": method, "ablation": ablation,
        "attack_type": "mixed" if level != "none" else "none", "attack_level": level,
        "f_p": b["f_p"], "B_z": b["B_z"], "H_A": b["H_A"], "epsilon_s": b["epsilon_s"],
        "evidence_sources": 12, "provenance_groups": 4, "prereq_per_action": 1,
        "AURC": metrics["AURC"], "T_crit": metrics["T_crit"], "D_B": metrics["D_B"],
        "P_FA": metrics["P_FA"], "T_corr": metrics["T_corr"], "D_pi": metrics["D_pi"],
        "fallback_rate": metrics["fallback_rate"], "gate_latency_ms": metrics["gate_latency_ms"],
        "recovered_final": metrics["recovered_final"], "verifier_calls": metrics["verifier_calls"],
        "safety_violations": metrics["safety_violations"], "status": "ok", "notes": notes,
    }


def run_one(feeder, seed, method, level, ablation, env_root, opendss_root):
    adapter = make_adapter(feeder, env_root, opendss_root)
    return run_episode(adapter, seed, method, level, ablation)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--env-zip", required=True)
    p.add_argument("--opendss-root", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--seeds", type=int, default=5)
    p.add_argument("--work-dir", default="/tmp/kgfedmarl_env")
    p.add_argument("--source-commit", default=os.environ.get("GITHUB_SHA", ""))
    args = p.parse_args()

    # OpenDSS changes its internal data directory while compiling redirected
    # files. Resolve all host-side paths before the first DSS compile so result
    # provenance never depends on that simulator-side working directory.
    env_zip = Path(args.env_zip).resolve()
    env_root = Path(args.work_dir).resolve()
    out = Path(args.output).resolve()
    odss = Path(args.opendss_root).resolve()
    if env_root.exists(): shutil.rmtree(env_root)
    env_root.mkdir(parents=True)
    with zipfile.ZipFile(env_zip) as zf: zf.extractall(env_root)
    if out.exists(): out.unlink()
    seeds = range(1, args.seeds + 1)

    for method in METHODS:
        for seed in seeds:
            print("baseline", method, seed, flush=True)
            m = run_one("IEEE33", seed, method, "medium", "full", env_root, odss)
            append_row(out, make_row(seed, "IEEE33", method, "full", "medium", m,
                                     args.source_commit, "common priority candidate policy + exact AC verifier"),
                       require_final_metrics=True)

    for level in ("none", "low", "high"):
        for seed in seeds:
            print("intensity", level, seed, flush=True)
            m = run_one("IEEE33", seed, "KG-FedMARL", level, "full", env_root, odss)
            append_row(out, make_row(seed, "IEEE33", "KG-FedMARL", "full", level, m,
                                     args.source_commit), require_final_metrics=True)

    for ablation in ABLATIONS[1:]:
        for seed in seeds:
            print("ablation", ablation, seed, flush=True)
            m = run_one("IEEE33", seed, "KG-FedMARL", "medium", ablation, env_root, odss)
            append_row(out, make_row(seed, "IEEE33", "KG-FedMARL", ablation, "medium", m,
                                     args.source_commit), require_final_metrics=True)

    for feeder in ("Radial69-env", "IEEE123", "IEEE8500"):
        note = ("supplied programmatic 69-bus radial benchmark" if feeder == "Radial69-env"
                else "canonical OpenDSS test feeder at pinned upstream commit")
        for seed in seeds:
            print("scale", feeder, seed, flush=True)
            m = run_one(feeder, seed, "KG-FedMARL", "medium", "full", env_root, odss)
            append_row(out, make_row(seed, feeder, "KG-FedMARL", "full", "medium", m,
                                     args.source_commit, note), require_final_metrics=True)
    print(out)

if __name__ == "__main__":
    main()
