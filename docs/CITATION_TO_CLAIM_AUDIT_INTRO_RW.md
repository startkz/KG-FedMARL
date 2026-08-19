# Citation-to-Claim Audit: Introduction + Related Work

## Scope and standard

This audit checks `manuscript/Introduction.tex` and `manuscript/RelatedWork.tex` against the cited literature and the current `ref.bib`. The standard is conservative: a citation is treated as adequate only when the cited work directly supports the adjacent positive claim, and literature-wide negative claims (e.g., `existing work does not`, `rarely`, `no prior work`) are not regarded as established merely because a few representative papers omit the feature. Such claims should be scoped to the reviewed literature or written as a contrast in problem/objective rather than as an absolute absence claim.

Status notation used below:

- **SAFE**: adjacent citation directly supports the claim.
- **HEDGE**: direction is reasonable, but wording is broader than the cited evidence.
- **REWRITE**: citation/claim mismatch or an unnecessarily strong novelty statement.
- **OWN-METHOD**: a statement about this paper; no external citation is required if the manuscript later substantiates it.

## Overall finding

The current narrative is substantially better aligned with the paper's security contribution than the earlier KG+MARL+FL framing. The main remaining issue is not false citation but **scope inflation in negative literature claims**. Positive descriptions of representative recovery, resilient-control, KG, and KGE-poisoning papers are mostly supportable. Claims such as `the integrity of the recovery knowledge itself is rarely treated`, `existing CPS-KG work ... does not provide`, and `such architectures ... do not address` should be narrowed to the reviewed literature or to the specific security objective that those papers were not designed to analyze.

A second issue is **category mixing** in the Introduction: `incremental2026causal` is causal-graph learning rather than a KG method, whereas `hybridtcdf2026` uses KG verification. The sentence should distinguish operational KGs from causal-graph/KG-verification work.

A third issue is bibliographic completeness. Several cited papers are real and independently verifiable but the current BibTeX entries omit DOI/volume/page metadata. These are not scientific-validity problems, but they should be corrected before submission.

---

## I. Introduction audit

### I-1. Cross-layer resilience is established across cyber, communication, control, and physical layers

**Current claim:**
> The need to reason across cyber, communication, control, and physical layers is well established in resilient CPS research.

**Status: SAFE.**

`zhu2020cross` explicitly presents a cross-layer CPS security/resilience framework spanning cyber and physical layers and interdisciplinary control/game/decision tools. `liao2025surveyresilient` is also appropriately used as a recent resilient-coordination survey.

**Recommendation:** keep.

### I-2. Existing studies use game-theoretic control, MPC, observer/event-triggered mechanisms against DoS/FDI/hybrid attacks

**Status: SAFE with a minor wording refinement.**

The cited works directly cover game-theoretic resilient control under DoS/FDI hybrid attacks (`game2026hybrid`), resilient MPC under DoS (`resilientmpc2025dos`), tube-based MPC under FDI (`stochastic2025tube`), and an observer/event-triggered controller under mixed FDI/DoS (`sampled2025observer`). The phrase `fault-tolerant coordination` is broader than this exact citation set.

**Safer wording:**
> Existing studies have developed game-theoretic resilient control, secure or resilient model predictive control, and observer/event-triggered mechanisms against DoS, false-data-injection, and hybrid attacks ...

### I-3. Power restoration incorporates communication impairment and cross-layer constraints

**Status: SAFE.**

`zhou2025faultresilient` explicitly couples communication-path recovery and physical topology reconfiguration in a cyber-physical distribution system.

**Recommendation:** keep, but avoid implying that this single 3-page IAS paper represents the full restoration literature. Use `Representative power-system restoration work has ...` rather than `Power-system restoration research has ...` if this remains the only citation.

### I-4. Runtime information is typically measurements/estimated states/fixed matrices/task annotations; recovery-knowledge integrity is rarely an explicit security boundary

**Status: HEDGE / high reviewer risk.**

The cited resilient-control papers indeed formulate measurements, states, attack signals, communication availability, and control constraints. However, the literature-wide conclusion `typically ... fixed coupling matrices or task-specific annotations` is not established by the adjacent citations, and `rarely treated as an explicit security boundary` is an absence claim.

**Recommended replacement:**
> In the representative recovery and resilient-control formulations above, runtime inputs are modeled mainly as measurements, estimated states, attack estimates, communication states, or predefined constraints. The CPS-recovery literature also highlights assumptions on diagnosis, attack history, and the recovery module itself. These formulations leave the integrity of a reusable recovery-knowledge state less explicit as a separate security object.

Add `\cite{lu2024recovery}` to the second sentence. This is both more defensible and closer to the actual gap.

### I-5. General KG capabilities: heterogeneous entities, relations, temporal attributes, rules, provenance, graph learning

**Status: HEDGE.**

`hogan2021knowledgegraphs` directly supports graph data models, schema/context, querying, validation, deductive/inductive techniques, embeddings and graph learning. The exact bundle `temporal attributes` + `provenance` is broader than what the adjacent sentence needs.

**Recommended replacement:**
> General KG research supports heterogeneous entities and relations, schema and context, query and validation languages, and deductive or inductive graph learning ...

Temporal/provenance properties can then be introduced specifically where the CPS papers or this paper define them.

### I-6. KGs have been used for temporal behavior, information dependencies, threats, causal attack evidence, and reconfiguration

**Status: REWRITE.**

The first, second, third and reconfiguration parts are supported by `liu2025timecontinuous`, `wang2025weightedkg`, `wu2026multidimensional`, and `knowledge2025dynamic`. However, `incremental2026causal` is an incremental **causal graph** paper, not itself a KG method. `hybridtcdf2026` combines temporal causal graphs with KG verification.

**Recommended replacement:**
> Recent CPS work has used KGs to represent time-continuous behavior, weighted information dependencies, cross-domain threats, and knowledge-driven control reconfiguration \cite{liu2025timecontinuous,wang2025weightedkg,wu2026multidimensional,knowledge2025dynamic}. Related work has also explored incremental causal-graph learning and KG-assisted verification for online attack detection \cite{incremental2026causal,hybridtcdf2026}.

### I-7. Existing KG work does not solve trustworthy online recovery knowledge under adversarial evidence

**Status: HEDGE.**

The conceptual distinction is strong, but `They do not, however, resolve ...` reads as a global absence claim. The cited KG works are aimed at representation, dependencies, threat modeling, detection, or reconfiguration, not at bounding adversarial belief-to-action propagation. That scope contrast is defensible.

**Recommended replacement:**
> These studies establish representation, reasoning, detection, or reconfiguration capabilities, but are not designed to bound how adversarial evidence changes a recovery belief and how that change propagates into action authorization and online learning.

This states a difference in **objective**, not an unverifiable claim that nobody has addressed it.

### I-8. An attacker need not attack the policy directly; poisoning recovery knowledge can alter prerequisites/transitions

**Status: OWN-METHOD / inference.**

This is a consequence of the paper's threat model rather than a literature claim.

**Recommended refinement:** prepend `Under the threat model considered here, ...` to make the scope explicit.

### I-9. Anomaly detection, safety filters, and federated learning alone do not close the propagation path

**Status: HEDGE.**

The logical point is valid, but `does not`/`is insufficient` can sound like a universal criticism of entire fields.

**Recommended replacement:**
> Anomaly detection, safety filtering, and federated learning address different parts of this pipeline; unless the trustworthiness of the information passed between them is explicitly modeled or verified, none by itself provides a bound on the complete knowledge-to-authorization-to-learning propagation path.

This is a systems argument and does not require a broad literature-negation claim.

### I-10. Method description, four objectives, and theorem summaries

**Status: OWN-METHOD.**

No external citation is necessary. These claims must remain exactly consistent with Sections III--VI and should not be strengthened beyond the proved assumptions. Current wording (`mechanism-level security properties`, no global MARL convergence claim) is appropriately conservative.

### I-11. Contribution: `We identify the recovery knowledge plane as an attack surface`

**Status: HEDGE / novelty wording.**

`identify` may be read as a first-to-discover claim.

**Recommended replacement:**
> We formalize the recovery knowledge plane as an explicit attack surface ...

`formalize` accurately describes the manuscript's contribution without claiming priority over all prior work.

### I-12. Contribution: `We establish explicit bounds ...`

**Status: SAFE as an own-paper claim**, provided the final Section VI retains the four stated bounds and their assumptions.

---

## II. Related Work audit

### II-1. `Existing studies ... largely address these components separately`

**Status: HEDGE.**

This is a literature-wide synthesis.

**Recommended replacement:**
> The representative literature reviewed below addresses these components mostly as separate problem classes.

### II-2. Lu et al. survey: shallow/deep recovery and open issues

**Status: SAFE with one qualification.**

The shallow/deep partition is directly supported. The survey also discusses diagnosis/history/recovery assumptions, but this detail should be retained only if the manuscript's reference copy supports the exact wording. The current statement is compatible with the survey and with the stored reference analysis.

### II-3. Representative recovery methods: Zhang 2020, Akowuah 2021, Fei 2020

**Status: SAFE.**

All three publications are real and match the described categories: real-time recovery using linearized dynamics; learning-assisted restoration from sensor attacks; RL-assisted UAV recovery/control under attacks.

### II-4. `Recent resilient-control work considers hybrid DoS/FDI attacks and multilayer coordination`

**Status: SAFE**, assuming `liao2025surveyresilient` remains the coordination-survey citation.

### II-5. `Runtime recovery knowledge is generally consumed ... integrity is not usually modeled ... explicitly bounded`

**Status: HEDGE / high reviewer risk.**

This is the same main gap as Introduction and should be phrased as an observation about the reviewed recovery literature, not all literature.

**Recommended replacement:**
> Across the representative recovery methods above, measurements, diagnosis outputs, estimated states, and predefined cyber-physical constraints are inputs to recovery. Their primary guarantees concern state recovery, control feasibility, stability, or attack mitigation rather than a separate bound on the distortion and downstream propagation of a reusable recovery-knowledge state.

This is much easier to defend paper-by-paper.

### II-6. KG foundations and KG--ML relation

**Status: SAFE.**

`hogan2021knowledgegraphs` supports query/validation and inductive/deductive graph methods; `damato2023machine` explicitly organizes work into ML-for-KG and KG-for-ML directions.

### II-7. Gill, Ji, Banerjee, Wu descriptions

**Status: SAFE.**

The paper descriptions match the publication scopes: time-continuous behavior in KGs; weighted KGs for information dependencies; ontology/knowledge-driven dynamic reconfiguration; heterogeneous cross-domain threat KG for critical power infrastructure.

### II-8. Sankaranarayanan et al. 2026: unified ontology/KG and real-time queries under structural updates

**Status: SAFE but bibliographically time-sensitive.**

The current arXiv version (2608.16001) explicitly reports unified cyber/physical ontology/KG integration, millisecond-level cross-domain queries, and evaluation under six cumulative structural mutations. This strongly supports the sentence. Because the work is extremely recent, avoid stating a final IEEE venue unless the accepted-publication status is independently confirmed in the final camera-ready bibliography.

### II-9. `Existing CPS-KG work ... does not provide a bound ... nor define when belief is sufficient to authorize a field action`

**Status: HEDGE.**

The reviewed papers are not designed for this objective, but an absolute negative claim across all CPS-KG literature is not proven.

**Recommended replacement:**
> The representative CPS-KG systems above focus on representation, interoperability, analysis, threat modeling, or reconfiguration. Their reported guarantees do not bound adversarial distortion of a recovery belief or connect such a belief to a quantified field-action authorization risk.

This is precise and auditable against the cited papers.

### II-10. KGE poisoning papers: Zhang 2019, Bhardwaj 2021, Zhou 2024

**Status: SAFE.**

- Zhang et al. manipulate targeted KGE facts by adding/deleting graph facts.
- Bhardwaj et al. poison KGE link prediction through relation-inference patterns.
- Zhou et al. attack federated KGE through malicious local poisoning and target false fact prediction at a victim client.

The current wording accurately characterizes this literature as embedding/link-prediction integrity attacks.

### II-11. `They do not consider a time-varying operational KG ... converted into physical action authority`

**Status: HEDGE.**

For the three cited papers, this contrast is accurate, but `They do not consider` is safest if explicitly scoped to those three works.

**Recommended replacement:**
> In these works, the attacked output is an embedding or link-prediction model; the papers do not study the distinct closed-loop setting considered here, where field evidence continually updates operational assertions that may authorize physical actions.

### II-12. Rodrigues et al. combines KG retrieval and game-theoretic multi-agent learning

**Status: SAFE.**

The 2026 ICPS work explicitly integrates domain-specific KG retrieval with game-theoretic/adversarial multi-agent DRL for robust process-control design.

### II-13. `Such architectures ... do not address transition persistence in replay`

**Status: HEDGE.**

The cited Rodrigues paper is not about replay contamination, but one paper cannot establish an absence across `such architectures` generally.

**Recommended replacement:**
> This line demonstrates semantic knowledge as a control-design input, but the cited framework is not designed around the replay-persistence problem studied here: a transition collected under contaminated recovery knowledge may continue to influence a deployed policy after the originating evidence has expired.

### II-14. Positioning statement

**Current claim:**
> KG-FedMARL therefore does not claim novelty from constructing a dynamic KG, using MARL, applying federated learning, or placing a safety filter after a learned policy.

**Status: SAFE and recommended.**

This is an effective novelty-boundary statement.

The final sentence should, however, avoid implying that this paper is definitively the first closed-loop work unless a systematic literature review supports that priority claim. Current wording (`this paper instead studies ...`) is acceptable because it describes focus rather than priority.

---

## III. Bibliographic authenticity and metadata notes

The following cited references were independently confirmed as real publications with matching titles/authors/venues or DOI records:

- `zhu2020cross`: Springer, *Cross-Layer Design for Secure and Resilient Cyber-Physical Systems: A Decision and Game Theoretic Approach*, 2020, DOI `10.1007/978-3-030-60251-2`.
- `lu2024recovery`: ACM Computing Surveys 56(8), 2024, DOI `10.1145/3653974`.
- `zhang2020real`: IEEE RTSS 2020, pp. 205--217, DOI `10.1109/RTSS49844.2020.00028`.
- `akowuah2021recovery`: IEEE RTCSA 2021, pp. 61--66, DOI `10.1109/RTCSA52859.2021.00015`.
- `fei2020learn`: IEEE ICRA 2020, pp. 7358--7364, DOI `10.1109/ICRA40945.2020.9196611`.
- `resilientmpc2025dos`: IEEE TSMC: Systems, DOI `10.1109/TSMC.2025.3555826`; bibliographic records report vol. 55, no. 7, pp. 4444--4457.
- `stochastic2025tube`: IEEE TSMC: Systems, DOI `10.1109/TSMC.2025.3612216`; Crossref-linked author metadata reports a 2026-01 journal issue. The current `year={2026}` is plausible, but volume/issue/pages should be synchronized from the final IEEE/Crossref record before submission.
- `sampled2025observer`: IEEE Transactions on Cybernetics, DOI `10.1109/TCYB.2025.3637776`; DOI year is 2025 while journal publication records list 2026. Keep the final issue year consistent with the official final record.
- `hogan2021knowledgegraphs`: ACM Computing Surveys 54(4), 2021, DOI `10.1145/3447772`.
- `damato2023machine`: TGDK 1(1), 2023, DOI `10.4230/TGDK.1.1.8`.
- `liu2025timecontinuous`: IEEE ETFA 2025, pp. 1--8, DOI `10.1109/ETFA65518.2025.11205677`.
- `wang2025weightedkg`: IEEE ICPS 2025, DOI `10.1109/ICPS65515.2025.11087841`.
- `knowledge2025dynamic`: IEEE IoT Journal, DOI `10.1109/JIOT.2024.3487578`.
- `wu2026multidimensional`: NNICE 2026, DOI `10.1109/NNICE68970.2026.11465638`.
- `sankaranarayanan2026ontology`: arXiv `2608.16001` (posted 2026-08-17); the manuscript's claims about unified ontology/KG and structural-update query evaluation are supported by the current preprint.
- `zhang2019kgpoison`: IJCAI 2019, pp. 4853--4859, DOI `10.24963/ijcai.2019/674`.
- `bhardwaj2021kgpoison`: ACL-IJCNLP 2021, pp. 1875--1888, DOI `10.18653/v1/2021.acl-long.147`.
- `zhou2024fkgepoison`: The Web Conference 2024, pp. 1998--2008, DOI `10.1145/3589334.3645422`.
- `rodrigues2026agentic`: IEEE ICPS 2026, DOI `10.1109/ICPS70486.2026.11567974`.

### Metadata fixes recommended before final bibliography freeze

1. Add missing DOI to `zhang2020real`, `akowuah2021recovery`, and `fei2020learn`.
2. Add the subtitle/DOI to `zhu2020cross` if the Springer book is cited as a book rather than an abbreviated title.
3. Complete volume/issue/pages for `resilientmpc2025dos`.
4. Recheck the final issue-year/volume/page metadata for `stochastic2025tube` and `sampled2025observer`; DOI year and final journal issue year differ, which is normal for online-first IEEE papers.
5. Treat `sankaranarayanan2026ontology` as a preprint unless the claimed accepted IEEE venue can be independently confirmed at submission time.

---

## IV. Recommended correction priority

### P0: change before the next manuscript freeze

- Introduction: replace the broad claim that recovery-knowledge integrity is `rarely` an explicit security boundary with a scoped contrast to representative recovery/control formulations.
- Introduction: separate causal-graph work from KG work.
- Introduction: replace universal `anomaly detection/safety filter/federated learning does not` language with a pipeline-scoped statement.
- Related Work: scope the two main negative claims (`existing CPS-KG work does not...`; `such architectures do not...`) to the cited representative papers or their stated objectives.
- Contribution 1: change `We identify` to `We formalize` to avoid an implicit first-discovery claim.

### P1: bibliography and style cleanup

- Complete DOI/volume/page metadata listed above.
- Use `representative` / `reviewed here` where a single or small citation set is used to characterize a broad field.
- Prefer `is not designed to provide X` or `its reported guarantees concern Y rather than X` over `does not address X` when making novelty contrasts.

## Audit conclusion

No core research claim in the Introduction or Related Work needs to be abandoned. The main gap is wording discipline: the manuscript should distinguish **(i) what a cited paper positively demonstrates**, **(ii) what its stated objective does not include**, and **(iii) what this paper adds under its own threat model**. With the P0 rewrites above, the novelty argument becomes harder to challenge because it no longer depends on unverifiable literature-wide absence claims; it rests on an auditable difference in security object and guarantee: prior recovery papers analyze state/control recovery, prior CPS-KG papers analyze representation/reasoning/reconfiguration, and prior KGE-poisoning papers analyze embedding/link-prediction integrity, whereas this paper bounds propagation from adversarial operational evidence to recovery belief, action authorization, and deployed-policy updates.
