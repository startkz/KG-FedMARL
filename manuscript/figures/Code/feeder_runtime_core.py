"""Trust/evidence primitives for feeder-level KG-FedMARL experiments.

The implementation follows the revised manuscript's recovery-knowledge boundary:
receive-time anchored evidence, provenance-group influence caps, temporal
forgetting, semantic gating, and trust-dependent policy promotion.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Sequence

import numpy as np

ATTACK_BUDGETS = {
    "none": dict(f_p=0, B_z=0, H_A=0, epsilon_s=0.00),
    "low": dict(f_p=1, B_z=2, H_A=4, epsilon_s=0.01),
    "medium": dict(f_p=2, B_z=6, H_A=8, epsilon_s=0.02),
    "high": dict(f_p=3, B_z=12, H_A=12, epsilon_s=0.05),
}
GROUPS = ("rtu", "ids", "net", "ctrl")
BELIEF_THRESHOLD = 0.80
LAMBDA_F = 0.85
BETA_GROUP = 0.90
EPS_CORR = 0.03
STEPS = 24


def logit(p: float) -> float:
    p = min(1 - 1e-8, max(1e-8, float(p)))
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def softmax(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float) - np.max(z)
    e = np.exp(z)
    return e / e.sum()


def kl_cat(p: np.ndarray, q: np.ndarray) -> float:
    p = np.clip(p, 1e-12, 1.0)
    q = np.clip(q, 1e-12, 1.0)
    return float(np.sum(p * (np.log(p) - np.log(q))))


def tv_cat(p: np.ndarray, q: np.ndarray) -> float:
    return float(0.5 * np.abs(p - q).sum())


def project_policy_step(logits: np.ndarray, direction: np.ndarray, kappa: float) -> np.ndarray:
    p0 = softmax(logits)
    lo, hi = 0.0, 4.0
    for _ in range(36):
        mid = (lo + hi) / 2.0
        p1 = softmax(logits + mid * direction)
        if kl_cat(p1, p0) <= kappa:
            lo = mid
        else:
            hi = mid
    return logits + lo * direction


@dataclass
class Evidence:
    q: int
    value: int
    source: str
    group: str
    t_event: float
    t_recv: float
    conf: float


class BeliefState:
    """Versionless experiment kernel for Eq. (PATB) with true provenance groups."""
    def __init__(self, n: int, *, prior: float = 0.60, lambda_f: float = LAMBDA_F,
                 beta_group: float = BETA_GROUP, group_cap: bool = True):
        self.prior = np.full(n, logit(prior), dtype=float)
        self.L = self.prior.copy()
        self.lambda_f = float(lambda_f)
        self.beta_group = float(beta_group)
        self.group_cap = bool(group_cap)
        self.reliability = {f"{g}_{i}": 0.90 for g in GROUPS for i in range(1, 5)}

    def probs(self) -> np.ndarray:
        return np.array([sigmoid(x) for x in self.L], dtype=float)

    def update(self, evidence: Sequence[Evidence], t_now: float) -> None:
        by_q: Dict[int, List[Evidence]] = {}
        for z in evidence:
            by_q.setdefault(int(z.q), []).append(z)
        self.L = self.prior + self.lambda_f * (self.L - self.prior)
        for q, items in by_q.items():
            by_group: Dict[str, List[float]] = {}
            for z in items:
                rho = self.reliability.get(z.source, 0.80)
                recv_age = max(0.0, t_now - z.t_recv)
                event_gap = max(0.0, z.t_recv - z.t_event)
                phi_time = math.exp(-recv_age / 8.0) * math.exp(-event_gap / 6.0)
                calibrated = 0.05 + 0.90 * min(1.0, max(0.0, z.conf))
                support = 1.20 if z.value > 0 else -1.20
                raw = calibrated * rho * phi_time * support
                by_group.setdefault(z.group, []).append(raw)
            total = 0.0
            for vals in by_group.values():
                if not self.group_cap:
                    total += float(sum(vals))
                    continue
                u = float(sum(abs(v) for v in vals))
                scale = min(1.0, self.beta_group / (u + 1e-12))
                total += scale * float(sum(vals))
            self.L[q] += total


def availability_schedule(seed: int, steps: int, n_blocks: int) -> np.ndarray:
    rng = np.random.default_rng(seed * 1009 + n_blocks * 17)
    a = np.ones((steps, n_blocks), dtype=bool)
    for b in range(n_blocks):
        if rng.random() < 0.48:
            start = int(rng.integers(1, max(2, steps // 3)))
            dur = int(rng.integers(2, 7))
            a[start:min(steps, start + dur), b] = False
        if rng.random() < 0.15:
            start = int(rng.integers(max(2, steps // 2), steps - 1))
            a[start:min(steps, start + 3), b] = False
    return a


def evidence_for_step(true_avail: np.ndarray, step: int, budget: Mapping[str, float],
                      rng: np.random.Generator, *, attacked: bool) -> List[Evidence]:
    n_blocks = true_avail.shape[1]
    active = attacked and int(budget["H_A"]) > 0 and 2 <= step < 2 + int(budget["H_A"])
    compromised = set(GROUPS[:int(budget["f_p"])]) if active else set()
    dup_budget = int(budget["B_z"]) if active else 0
    eps_s = float(budget["epsilon_s"]) if active else 0.0
    mode = ("fabrication", "replay", "delay", "missing", "correlated")[step % 5] if active else "clean"
    out: List[Evidence] = []
    for b in range(n_blocks):
        truth = 1 if true_avail[step, b] else -1
        prev_truth = 1 if true_avail[max(0, step - 3), b] else -1
        for gi, g in enumerate(GROUPS):
            if active and g in compromised and mode == "missing":
                continue
            value, t_event = truth, float(step)
            if active and g in compromised:
                if mode in ("fabrication", "correlated"):
                    value = -truth
                elif mode == "replay":
                    value, t_event = prev_truth, float(max(0, step - 3))
                elif mode == "delay":
                    t_event = float(max(0, step - 5))
            conf = min(1.0, 0.88 + 0.03 * gi + eps_s)
            out.append(Evidence(b, value, f"{g}_{1 + b % 3}", g, t_event, float(step), conf))
        if active and mode == "correlated" and dup_budget and compromised:
            g = sorted(compromised)[0]
            for j in range(min(dup_budget, 6)):
                out.append(Evidence(b, -truth, f"{g}_dup{j}", g, float(step), float(step), 0.99))
    rng.shuffle(out)
    return out


def latest_estimate(evidence: Sequence[Evidence], n_blocks: int) -> np.ndarray:
    score = np.zeros(n_blocks, dtype=float)
    for z in evidence:
        score[int(z.q)] += 1.0 if z.value > 0 else -1.0
    return score > 0


def update_policy(logits: np.ndarray, action: int | None, reward: float, trust: float,
                  *, quarantine: bool, fixed_radius: bool) -> np.ndarray:
    if action is None or (quarantine and trust < 0.65):
        return logits
    p = softmax(logits)
    direction = -p
    direction[int(action)] += 1.0
    direction *= float(reward)
    if np.allclose(direction, 0):
        return logits
    kappa = 0.004 if fixed_radius else 0.0006 + 0.0034 * min(1.0, max(0.0, trust))
    return project_policy_step(logits, direction, kappa)
