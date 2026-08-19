# Sections III–VI Global Consistency Audit

## Scope

This audit covers `SystemModel.tex` (Section III), `ProblemFormulation.tex` (Section IV), `MU2MV-Framework.tex` (Section V), and `TheoreticalAnalysis.tex` (Section VI). The governing research line is: under missing, stale, conflicting, or adversarial recovery knowledge, maintain a bounded-trust online knowledge state and limit the propagation of erroneous knowledge into recovery constraints and recovery policies.

## Overall assessment

The current III→VI chain is structurally sound: Section III defines the recovery knowledge plane and adversary; Section IV defines constrained partially observable restoration and four security objectives; Section V implements three propagation barriers; Section VI provides mechanism-level guarantees. However, several notation collisions and three theorem-assumption gaps must be corrected before experiment design, otherwise reviewers can challenge whether the stated guarantees actually correspond to the implemented mechanisms.

## Priority findings

| Priority | Location | Finding | Required correction |
|---|---|---|---|
| P0 | IV vs V | `\lambda_f` denotes fallback-cost weight in the reward and forgetting factor in the belief update. | Keep `\lambda_f` for forgetting; rename fallback weight to `\lambda_{\rm fb}`. |
| P0 | III vs V | `\mathcal V_t` denotes temporal validity in the belief graph, while `\mathcal V_t` is reused as the policy validation suite. | Rename validation suite to `\mathcal D_t^{\rm val}`. |
| P0 | IV vs V | `\tau_{i,t}` denotes local action-observation history while `\tau_t` denotes a learning transition. | Rename local history to `h_{i,t}` or `\mathcal H_{i,t}`. |
| P0 | III/IV vs V | `\mathcal B_t` is the core belief state and `\mathcal B` is reused as a training minibatch. | Rename minibatch to `\mathcal D^{\rm mb}`. |
| P0 | IV vs V | `\mathcal C` is the constraint set, while `\mathcal C_t^0` is a candidate set and `\mathcal C_t(a)` is an authorization context. | Use `\mathbb U_t^0`/`\mathbb U_t^B` for candidate sets and `\mathcal H_t^{\rm auth}(a)` for authorization context. |
| P0 | IV vs V/VI | `\varepsilon_\pi(\Omega_A)` is the global attacked-vs-clean policy-deviation bound, but `\epsilon_\pi(\bar\Gamma)` is reused as a per-update KL trust-region radius. | Rename per-update radius to `\kappa_\pi(\bar\Gamma)` and derive the global `\varepsilon_\pi(\Omega_A)` from it. |
| P0 | V | The versioned transition uses an undefined global `\iota_t`; Section IV only defines `\iota_{i,t}`. | Define `\boldsymbol\iota_t=(\iota_{1,t},\ldots,\iota_{N,t})` and use it in joint transitions/losses. |
| P0 | V | Discounted Beta reliability update treats unresolved feedback ambiguously: `y_s^t` is said to be undefined, yet the equations always add `1-y_s^t`. | Introduce verification indicator `m_s^t`; update with `m_s^t y_s^t` and `m_s^t(1-y_s^t)`. |
| P0 | VI, Thm. 1 | The proof cancels all honest evidence terms, but this requires honest-evidence effective weights to be identical across attacked/reference trajectories. Current text only says honest evidence is the same. | Add an explicit assumption that compromised groups cannot change calibrated weights of uncompromised evidence, or absorb such changes into the adversarial budget. |
| P0 | VI, Thm. 3 | After attack termination, identical raw honest evidence does not imply identical effective contributions if source-reliability or consistency states differ. | State the sufficient condition in terms of identical post-attack effective honest contributions; otherwise derive a residual-error floor. |
| P0 | IV vs VI, Thm. 4 | Section IV defines policy propagation with expected KL; Theorem 4 primarily proves a TV bound. The proof also silently needs a common information-state distribution across promotions. | Prefer defining the security metric as expected TV on a fixed audit distribution; retain KL as the enforceable per-promotion trust region and use Pinsker to connect them. |
| P0 | III vs IV | Threat model allows compromised local controllers, but Section IV treats the adversary mainly as evidence manipulation. If a compromised controller can directly actuate, the physical transition is directly adversarial and the current guarantees no longer cover the threat. | Restrict compromise to telemetry/reporting interfaces unless direct actuation is explicitly modeled as exogenous disturbance; state that the protected actuation path cannot bypass the authoritative verifier. |
| P1 | III | `q_t^\star` is binary, while some examples are continuous quantities such as voltage. | State that uncertain KG facts are Boolean/finite predicates or interval assertions; raw continuous measurements remain evidence/physical-state variables. |
| P1 | IV | `F_B` is described as updating `\mathcal B_t`, while Algorithm 1 updates the full `\mathcal G_t^B`. | Define `F_B:(\mathcal G_t^B,\mathcal Z_{t+1})\mapsto\mathcal G_{t+1}^B`. |
| P1 | V | `\omega_q` is reused for belief-distance weights in Section IV and prerequisite weights in `\Gamma_B`. | Rename transition-trust weights to `\varpi_q` unless they are intentionally identical and explicitly stated as such. |
| P1 | V | Trust score exponents are only nonnegative; all-zero exponents make `\Gamma_t=1` regardless of evidence. | Require positive enabled exponents, preferably normalized, e.g. `\lambda_B+\lambda_P+\lambda_C+\lambda_O=1`. |
| P1 | V | Algorithm 2 complexity assumes a bounded candidate set but does not state that candidate-generation cost is excluded. | Explicitly scope complexity to gate processing after candidate generation. |
| P1 | V/VI | `\beta_{max}` is used in Theorem 1 but not defined in Section V. | Define `\beta_{\max}=\max_g\beta_g`. |
| P1 | IV/VI | Theorem 2 gives a per-action bound but does not explicitly close Section IV's `\delta_{\rm auth}` requirement. | Add condition `\bar\delta_B+\sum_q\varepsilon_q\le\delta_{\rm auth}`. |
| P1 | III/V/VI | Physical safety depends on the conservative state set, but no formal containment assumption is stated. | Add `x_t\in\widehat{\mathcal X}_t` as a verifier soundness assumption. |
| P1 | IV/VI | `\mathcal B_t^0` is a counterfactual clean belief under the same physical trajectory, but closed-loop actions can make attacked and clean trajectories diverge. | State that the belief-sensitivity metric is evaluated conditionally on a common physical/action trajectory; full closed-loop recovery is evaluated experimentally. |
| P2 | V | `K_{max}` should be typeset consistently as `K_{\max}`; numerical stabilizer `\epsilon` is used in two places. | Normalize typography and use `\epsilon_0` for numerical floors if desired. |
| P2 | III | `\mathcal T^0` is described as immutable yet may appear to contain mutable protection settings. | Clarify that `\mathcal T^0` stores rule semantics and authenticated invariant limits; mutable runtime settings/status are assertions. |

## Theorem-to-objective closure after correction

After the P0/P1 corrections, the intended mapping becomes exact:

- Algorithm 1 + provenance-group cap + forgetting ⇒ bounded belief distortion `\varepsilon_B(\Omega_A)` and finite correction time.
- Algorithm 2 + calibrated belief gate + sound authoritative verifier ⇒ false-authorization risk `\delta_{\rm auth}`.
- Algorithm 3 + quarantine + trust-dependent KL radius + stable/candidate separation ⇒ bounded deployed-policy deviation `\varepsilon_\pi(\Omega_A)`.

For Theorem 1, with `\beta_{\max}=\max_g\beta_g`, the per-assertion log-odds deviation remains

`|L_t^A(q)-L_t^0(q)| <= f_p beta_max/(1-lambda_f)`.

Because the Section-IV belief distance is a normalized weighted average, the same per-assertion bound implies

`D_B(B_t^A,B_t^0) <= f_p beta_max/[4(1-lambda_f)]`,

provided the theorem's honest-weight invariance assumption holds.

For Theorem 3, if post-attack effective honest contributions coincide, then the attacked/reference log-odds difference decays exactly as `lambda_f^k`. If this stronger condition is not desired, the theorem must include a bounded residual term caused by post-attack weight mismatch.

For Theorem 4, the cleanest formulation is to use expected total variation on a fixed audit distribution as the Section-IV propagation metric. A KL radius is still enforced at every promotion; Pinsker's inequality converts each KL radius into a TV step bound, and the triangle inequality yields the cumulative deployed-policy bound. This avoids an unnecessarily strong lower-bound assumption on every action probability.

## Compile/repository observations outside the III–VI semantic audit

`main.tex` currently references `Experimental-RPDRQL.tex`, `Acknowledgments.tex`, and bibliography `ref`, but these files are not present in the current `manuscript/` tree. This is a repository/compilation blocker rather than a Section-III–VI theory issue, but it must be resolved before producing a clean PDF from GitHub.

## Recommended remediation order

1. Fix symbol collisions and undefined variables without changing method semantics.
2. Correct the discounted-Beta update and explicitly define verifier-state containment.
3. Repair Theorems 1 and 3 by adding the exact effective-evidence assumptions they use.
4. Align the policy security metric and Theorem 4, preferably via expected TV + per-update KL trust region.
5. Add the explicit `delta_auth` closure and `beta_max` definition.
6. Recompile and run a label/reference scan before experiment redesign.
