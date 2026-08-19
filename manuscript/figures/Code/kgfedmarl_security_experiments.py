from pathlib import Path
import math
import numpy as np
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parents[1]
OUT.mkdir(parents=True, exist_ok=True)
SEED = 20260819
rng = np.random.default_rng(SEED)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9,
    "legend.fontsize": 8,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "ps.useafm": True,
    "pdf.use14corefonts": True,
})

def logistic(x):
    return 1.0 / (1.0 + np.exp(-x))

def save(fig, name):
    for ext in ("pdf","png","eps"):
        fig.savefig(OUT / f"{name}.{ext}", bbox_inches="tight", dpi=600)
    plt.close(fig)

# ---------------------------------------------------------------------
# 1) Bounded belief distortion under provenance-group poisoning
# ---------------------------------------------------------------------
lambda_f = 0.85
beta_max = 0.025
steps = 80
trials = 800
fps = np.arange(0, 6)
emp_mean, emp_p95, theorem = [], [], []
for fp in fps:
    vals = []
    if fp == 0:
        vals = [0.0] * trials
    else:
        for _ in range(trials):
            delta = 0.0
            max_b = 0.0
            for t in range(steps):
                # General attack can move a compromised group from one capped
                # contribution to an opposite capped contribution.  We draw a
                # bounded attack-induced group difference in [0, 2 beta_max].
                d = np.sum(rng.uniform(0.0, 2.0 * beta_max, size=fp))
                delta = lambda_f * delta + d
                # Compare against a zero-log-odds reference to obtain a direct
                # controlled belief sensitivity experiment.
                bdiff = abs(logistic(delta) - 0.5)
                max_b = max(max_b, bdiff)
            vals.append(max_b)
    vals = np.asarray(vals)
    emp_mean.append(vals.mean())
    emp_p95.append(np.quantile(vals, 0.95))
    theorem.append(min(1.0, fp * beta_max / (2.0 * (1.0 - lambda_f))))

fig, ax = plt.subplots(figsize=(3.5, 2.45))
ax.plot(fps, emp_mean, marker="o", label="controlled mean")
ax.plot(fps, emp_p95, marker="s", linestyle="--", label="controlled 95th pct.")
ax.plot(fps, theorem, marker="^", linestyle=":", label="Theorem 1 bound")
ax.set_xlabel(r"Compromised provenance groups $f_p$")
ax.set_ylabel(r"Maximum belief distortion $D_B$")
ax.set_xlim(0, 5)
ax.set_ylim(0, max(theorem)*1.08)
ax.grid(True, linestyle="--", alpha=.35)
ax.legend(frameon=True)
fig.tight_layout()
save(fig, "kgfedmarl_belief_budget")

# ---------------------------------------------------------------------
# 2) Finite correction after a bounded-duration poisoning interval
# ---------------------------------------------------------------------
fp = 2
eps_corr = 0.02
durations = np.array([2, 4, 6, 8, 10, 12, 16, 20])
corr_exact, corr_bound = [], []
for H in durations:
    delta = 0.0
    # deterministic worst-case signed difference during attack
    for _ in range(H):
        delta = lambda_f * delta + 2.0 * fp * beta_max
    k = 0
    while abs(logistic((lambda_f**k) * delta) - 0.5) > eps_corr and k < 500:
        k += 1
    corr_exact.append(k)
    delta_bound = 2.0 * fp * beta_max * (1.0 - lambda_f**H) / (1.0 - lambda_f)
    kb = math.ceil(
        math.log(max(1.0, delta_bound/(4.0*eps_corr))) / math.log(1.0/lambda_f)
    )
    corr_bound.append(kb)

fig, ax = plt.subplots(figsize=(3.5, 2.45))
ax.plot(durations, corr_exact, marker="o", label="controlled correction")
ax.plot(durations, corr_bound, marker="s", linestyle="--", label="Theorem 3 bound")
ax.set_xlabel(r"Attack duration $H_A$ (updates)")
ax.set_ylabel(r"Correction time $T_{\rm corr}$")
ax.grid(True, linestyle="--", alpha=.35)
ax.legend(frameon=True)
fig.tight_layout()
save(fig, "kgfedmarl_correction_time")

# ---------------------------------------------------------------------
# 3) False-authorization risk under calibrated prerequisite beliefs
# ---------------------------------------------------------------------
m = 4
eps_q = 0.005
budgets = np.array([0.01, 0.02, 0.04, 0.06, 0.08, 0.10])
mc_trials = 200_000
fa_emp, fa_bound = [], []
for b in budgets:
    delta_q = b / m
    p_false = min(1.0, delta_q + eps_q)
    # independent prerequisite failures are only for this controlled
    # calibration experiment; Theorem 2 itself does not require independence.
    samples = rng.random((mc_trials, m)) < p_false
    fa_emp.append(samples.any(axis=1).mean())
    fa_bound.append(min(1.0, b + m * eps_q))

fig, ax = plt.subplots(figsize=(3.5, 2.45))
ax.plot(budgets, fa_emp, marker="o", label="Monte Carlo false auth.")
ax.plot(budgets, fa_bound, marker="s", linestyle="--", label="Theorem 2 bound")
ax.set_xlabel(r"Aggregate semantic budget $\bar{\delta}_B$")
ax.set_ylabel("False-authorization probability")
ax.grid(True, linestyle="--", alpha=.35)
ax.legend(frameon=True)
fig.tight_layout()
save(fig, "kgfedmarl_false_authorization")

# ---------------------------------------------------------------------
# 4) Trust-gated deployed-policy drift on a fixed audit distribution
# ---------------------------------------------------------------------
n_states, n_actions = 64, 4
base_logits = rng.normal(0, 0.8, size=(n_states, n_actions))

def softmax(z):
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)

def kl_mean(p, q):
    p = np.clip(p, 1e-12, 1.0)
    q = np.clip(q, 1e-12, 1.0)
    return np.mean(np.sum(p * (np.log(p)-np.log(q)), axis=1))

def tv_mean(p, q):
    return np.mean(0.5*np.sum(np.abs(p-q), axis=1))

def step_with_kl(logits, direction, kappa):
    p0 = softmax(logits)
    lo, hi = 0.0, 4.0
    for _ in range(40):
        mid = (lo + hi)/2
        p1 = softmax(logits + mid*direction)
        if kl_mean(p1, p0) <= kappa:
            lo = mid
        else:
            hi = mid
    return logits + lo*direction

gamma_attack = 0.55
gamma_ref = 0.90
def kappa(gamma):
    return 0.0005 + 0.0030*gamma

kA, k0 = kappa(gamma_attack), kappa(gamma_ref)
KA = [0]
tv_vals = [0.0]
la = base_logits.copy()
l0 = base_logits.copy()
for k in range(1, 11):
    da = rng.normal(0, 1, size=la.shape)
    d0 = rng.normal(0, 1, size=l0.shape)
    la = step_with_kl(la, da, kA)
    l0 = step_with_kl(l0, d0, k0)
    KA.append(k)
    tv_vals.append(tv_mean(softmax(la), softmax(l0)))
policy_bound = [
    min(1.0, k*(math.sqrt(kA/2.0)+math.sqrt(k0/2.0))) for k in KA
]

fig, ax = plt.subplots(figsize=(3.5, 2.45))
ax.plot(KA, tv_vals, marker="o", label="controlled audit TV")
ax.plot(KA, policy_bound, marker="s", linestyle="--", label="Theorem 4 bound")
ax.set_xlabel("Successful promotion events $K$")
ax.set_ylabel(r"Deployed-policy deviation $D_\pi$")
ax.set_xlim(0, 10)
ax.set_ylim(0, min(1.0, max(policy_bound)*1.08))
ax.grid(True, linestyle="--", alpha=.35)
ax.legend(frameon=True)
fig.tight_layout()
save(fig, "kgfedmarl_policy_drift")

print("SUMMARY")
print("belief_mean", [round(float(v),4) for v in emp_mean])
print("belief_p95", [round(float(v),4) for v in emp_p95])
print("belief_bound", [round(float(v),4) for v in theorem])
print("correction_exact", corr_exact)
print("correction_bound", corr_bound)
print("fa_emp", [round(float(v),4) for v in fa_emp])
print("fa_bound", [round(float(v),4) for v in fa_bound])
print("policy_tv", [round(float(v),4) for v in tv_vals])
print("policy_bound", [round(float(v),4) for v in policy_bound])
print("kappa_attack", kA, "kappa_ref", k0)
