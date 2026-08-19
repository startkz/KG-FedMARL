# Literature Knowledge Base for the KG-FedMARL Revision

This note records the reusable knowledge extracted from the 33 reference-text files embedded in the original manuscript archive (`tmp/reference_texts/`). One file is a duplicate copy of the same game-theoretic resilient-control paper, leaving 32 unique references. The governing revision question is:

> 在恢复所依据的知识本身可能缺失、过时、相互冲突或被攻击者污染时，如何建立一个有界可信的在线知识状态，并限制错误知识向恢复约束和恢复策略传播。

The references below are therefore read from the perspective of four needs: threat modeling, trustworthy dynamic knowledge, safe recovery constraints, and stable online policy adaptation.

## 1. Knowledge-graph foundations and knowledge/learning integration

### Hogan et al., *Knowledge Graphs*, ACM Computing Surveys
Useful knowledge: formal KG components (entities, relations, ontologies, rules, query, validation, deduction, induction, embeddings, graph neural networks); explicit distinction between data representation, semantic constraints, deductive reasoning, and learned completion. For this paper, it supports separating a relatively trusted schema/rule layer from uncertain runtime assertions. It also provides the conceptual basis for validation rather than treating every incoming triple as true.

Novelty boundary: generic KG construction, querying, validation, rule reasoning, embeddings, and GNN encoding are established techniques and must not be claimed as primary novelty.

### Reinanda et al., *Knowledge Graphs: An Information Retrieval Perspective*
Useful knowledge: entity recognition/linking, relation extraction, KG enrichment, retrieval over KG, and quality problems that arise when KGs are incomplete. For the revision, the key lesson is that evidence ingestion is itself an uncertain retrieval/alignment process, so the system should distinguish raw evidence confidence from system-calibrated belief.

### d'Amato et al., *Machine Learning and Knowledge Graphs: Existing Gaps and Future Research Challenges*
Useful knowledge: two-way KG/ML interaction—ML can complete/refine KGs and KGs can constrain/improve ML; open issues include integration of semantic knowledge into learning, interpretability, benchmark quality, and neuro-symbolic interfaces. This directly supports a bidirectional recovery loop in which the KG constrains policy execution while verified execution outcomes update knowledge.

Novelty boundary: “KG + ML” or “neuro-symbolic learning” is not sufficient novelty by itself.

### *A Comprehensive Survey of Knowledge Graph Reasoning Approaches and Applications*
Useful knowledge: KG reasoning must explicitly address incompleteness; reasoning families include embedding-based, path-based, rule-guided, neural, and hybrid methods. For this paper, the important distinction is between inference of missing facts and security-sensitive activation of operational facts. A recovery system should not convert an inferred relation directly into a hard operational prerequisite without confidence calibration and safety checks.

### *A Comprehensive Survey of Knowledge-Driven Deep Learning for Intelligent Wireless Network Optimization in 6G*
Useful knowledge: domain knowledge can enter learning through architecture, loss, constraints, initialization, model structure, and hybrid optimization. This supports treating physical constraints and KG semantics as explicit control interfaces rather than concatenated features. It also reinforces the need to state where knowledge enters the policy and what happens when that knowledge is wrong.

### *Unveiling Knowledge Insights from Large-Scale Knowledge Graphs for the Research Community*
Useful knowledge: graph organization and relationship discovery can expose latent structure in large-scale data. Its direct contribution to the new manuscript is limited; it is background for KG analytics rather than a direct recovery/security baseline.

## 2. Dynamic and cyber-physical knowledge representation

### *Representing Time-Continuous Behavior of Cyber-Physical Systems in Knowledge Graphs*
Useful knowledge: CPS knowledge cannot be represented only as static triples; time-continuous behavior, state evolution, intervals, and temporal semantics are required. This supports explicit event time, receive time, validity interval, and temporal decay in the new belief graph.

Novelty boundary: adding timestamps to KG facts is not enough. The new contribution must be adversarial temporal belief maintenance, not temporal representation alone.

### *Leveraging Weighted Knowledge Graphs for Modeling and Analyzing Information Dependencies in Automated Production Systems*
Useful knowledge: weighted relations can represent differing strengths/reliabilities of information dependency rather than binary edges. This is relevant to measurement paths, command paths, and cross-layer dependencies. The new paper should extend weighting into calibrated, source-aware, temporally decayed belief rather than a static edge weight.

### *A Multi-dimensional Heterogeneous Knowledge Graph Framework for Cross-domain Threat Modeling in Critical Power Infrastructure*
Useful knowledge: critical-power threats span cyber, physical, spatial, and potentially human/social domains; heterogeneous graph representation is useful for cross-domain threat reasoning. This supports the need for typed provenance and cross-layer dependency groups. It also means heterogeneous cyber-physical KG construction itself is not novel.

### *A Knowledge-Driven Approach for Dynamic Reconfiguration of Control Design in IoT and CPS*
Useful knowledge: ontology/capability knowledge can drive controller/device reconfiguration, candidate generation, sequencing, verification, and deployment. This is a direct novelty boundary: knowledge-driven control reconfiguration already exists. Our paper must focus on whether the knowledge supporting reconfiguration can be stale, conflicting, or poisoned, and how its influence is bounded.

### *Cyber-Physical Computer in Action: Generative Recommendation via Spatial-Temporal Subgraph Reasoning for Production Logistics Orchestration*
Useful knowledge: spatial-temporal subgraph reasoning can reduce a large graph to a task-relevant context and support action recommendation. This supports task-subgraph extraction for computational efficiency. It does not establish safety under adversarial evidence, so subgraph reasoning should be supporting infrastructure, not the core contribution.

### *The Agentic Control Framework: Integrating Knowledge Graph Retrieval and Game-Theoretic Multi-Agent Learning for Robust Process Design*
Useful knowledge: KG retrieval, semantic reasoning, digital twins, game-theoretic multi-agent learning, and robust control can already be integrated into an end-to-end control architecture. This makes “KG retrieval + multi-agent learning + robust control” a weak novelty claim. The new paper must differentiate through adversarial evidence integrity, bounded knowledge poisoning, risk-aware constraint synthesis, and safe online adaptation.

## 3. Online graph learning, causal reasoning, and attack detection

### Malarkkan et al., *Incremental Causal Graph Learning for Online Cyberattack Detection in Cyber-Physical Infrastructures (INCADET)*
Useful knowledge: online CPS graphs must adapt to evolving attacks and concept drift; incremental graph learning faces catastrophic forgetting, changing causal relationships, partial observability, and computational/memory cost. INCADET uses incremental causal graph updates, experience replay/edge reinforcement, and graph classification for online attack detection.

Direct implication: online graph evolution is already established. Our paper should not claim online graph update as novelty. Instead, it must address a different question: how to maintain bounded trustworthy recovery beliefs when the evidence stream used to update the graph may itself be malicious.

### *Hybrid TCDF with Knowledge Graph Verification for Temporal Causal Graphs in Industrial Systems*
Useful knowledge: data-driven temporal causal discovery can be cross-checked against domain knowledge/KG constraints. This supports a dual-source validation principle: runtime evidence should not be accepted solely because a learned detector reports it; semantic and physical consistency can serve as independent checks.

### *Graph Reinforcement Learning for Scalable Zero-Day Behavioral Intrusion Detection in Social Networks*
Useful knowledge: graph RL can act on graph-structured security states and scale to changing/unknown attack behavior. Its direct relevance is methodological rather than domain-specific. It further weakens any novelty claim based only on graph representation plus RL.

### *Hybrid Knowledge Graph and Deep Reinforcement Learning Model for Intelligent Anomaly Detection in EV Charging Behavior*
Useful knowledge: KG and DRL have already been combined in power/energy cyber contexts for anomaly detection. For our revision, KG+DRL must therefore be treated as prior art; the novelty is the trustworthy transition from uncertain evidence to recovery belief, constraints, and policy.

### *TS Fuzzy Dual-Residual-Driven Attack Detection and Resilient Control for Discrete-Time Nonlinear CPSs*
Useful knowledge: detection and resilient control should be coupled rather than treated independently; multiple residual channels improve detection under nonlinear dynamics and privacy/communication restrictions. This supports using independent evidence channels and outcome consistency rather than trusting a single detector confidence.

## 4. Cross-layer resilience and resilient-control theory

### Zhu and Xu, *Cross-Layer Design for Secure and Resilient Cyber-Physical Systems*
Useful knowledge: CPS security must be modeled across cyber, communication, control, and physical layers; attacker/defender knowledge, strategic behavior, temporal evolution, and cross-layer consequence propagation are central. This is the foundational reference for defining the recovery knowledge plane as an attack surface and for making the attacker’s capability, knowledge, budget, and objective explicit.

### *A Survey of Resilient Coordination for CPSs Against Malicious Attacks*
Useful knowledge: resilient coordination literature explicitly parameterizes adversarial node fractions, neighborhood structure, graph/connectivity assumptions, filtering rules, and convergence/safety conditions. This supports introducing a bounded compromised-source/provenance-group budget rather than an unconstrained attacker.

### *Game Theory-Based Resilient Control of Time-Varying CPSs Under Hybrid Attacks*
Useful knowledge: hybrid attacks combine multiple attack modes and time-varying system behavior; game-theoretic formulations make attack/defense strategies and budgets explicit. One duplicate copy exists in the archive. For the new paper, the reusable lesson is to define hybrid evidence poisoning jointly with physical/cyber disruption instead of treating poisoning as an isolated data-cleaning problem.

### *Adaptive Event-Triggered Secure Control for Attacked CPSs Based on Resilient Observer*
Useful knowledge: observer-based state/fault estimation and event-triggered communication can maintain control under attacks while reducing communication. Relevant to the new design: evidence can be produced by estimators with nonzero error bounds, so the belief graph should ingest bounded-confidence observations rather than binary facts.

### *Anti-Windup Secure Fault-Tolerant Control for Input-Saturated Nonlinear CPSs Against Multichannel Nonperiodic DoS Attacks*
Useful knowledge: actuator saturation and multi-channel DoS jointly affect feasible control; resilient control must incorporate physical input constraints and communication loss. This supports keeping physical invariant constraints outside the uncertain KG belief layer and always checking them authoritatively.

### *Fixed-Time Adaptive Sliding-Mode Resilient Control for Strict-Feedback Nonlinear CPSs Against Deception Attacks*
Useful knowledge: fixed-time/fault-resilient control gives explicit settling-time behavior under deception. It motivates a finite correction/recovery-time property rather than only asymptotic statements.

### *Fully Distributed Resilient Consensus of Multi-Agent Systems ... Under Stochastic DoS Attacks*
Useful knowledge: distributed resilience depends on network connectivity, local information, stochastic DoS assumptions, and bounded adversarial effects. This supports explicit availability/communication assumptions for recovery agents and helps frame the boundary under which distributed recovery remains feasible.

### *Resilient Adaptive Hybrid-Triggered Control for Cyber-Physical Direct-Drive-Wheel Systems Under Hybrid Cyberattacks*
Useful knowledge: hybrid triggering combines communication efficiency with resilience under mixed attacks. The paper is useful for defining latency/communication trade-offs and for avoiding the assumption that every evidence change should trigger a policy update.

### *Resilient Control of Stochastic CPSs Against Stealthy Attacks: Complex Dynamical Networks Encryption Strategy*
Useful knowledge: stealthy attacks can remain below conventional detection thresholds, so detector outputs cannot be treated as ground truth. This is directly relevant to the threat model and supports testing low-amplitude, persistent evidence poisoning.

### *Resilient MPC With Switched Cost Functions for CPSs Against DoS Attacks*
Useful knowledge: recovery/control behavior can switch according to communication availability and attack mode. It supports representing recovery-mode context explicitly in the belief state and using safe fallback control when remote actuation is unavailable.

### *Sampled Data-Based Observer and Resilient Event-Triggered Controller Design ... Mixed Cyber Attacks*
Useful knowledge: simultaneous FDI and DoS can affect observation and actuation channels; observers can estimate state/attacks under bounded assumptions, and event-triggered mechanisms tolerate communication attacks. This is useful for modeling multiple evidence channels and for giving sensor/communication attacks separate semantics in the belief graph.

### *Stochastic Tube-Based MPC for CPSs Under FDI Attacks With Bounded Probability*
Useful knowledge: probabilistic attack/detection assumptions can be propagated into robust/tube-based safety guarantees. This supports replacing binary `KGOK` with confidence/risk-aware admissibility and deriving a false-authorization probability bound.

## 5. Power-system and restoration-specific references

### *A Fault-Resilient Reconfiguration Strategy for Cyber-Physical Distribution Systems Based on Hybrid Flow Constraints*
Useful knowledge: distribution restoration is explicitly cyber-physical; communication recovery and electrical topology restoration can be co-optimized, with critical information flows and remote switch reachability affecting load restoration. This is a direct baseline for the claim that physical feasibility alone is insufficient.

Direct implication: the new paper should represent communication-path availability as an uncertain recovery prerequisite, not a deterministic annotation, and should compare against cyber-physical reconfiguration methods rather than only RL baselines.

### *Graph Neural Networks and Their Applications in Power Systems: A Review*
Useful knowledge: GNNs naturally encode non-Euclidean grid topology and support state estimation, prediction, control, and security applications. This establishes GAT/GNN encoding as standard infrastructure. The paper should not claim the relation-aware GAT itself as a primary novelty.

## 6. Security design rationale and explainability

### *Communicating Cybersecurity Decisions and Their Rationales Explicitly During and After CPS Design*
Useful knowledge: security decisions should preserve rationale, assumptions, and traceability so that later operators can understand why a decision was made. This strongly supports versioned provenance, explanation paths, and audit logs linking evidence version, KG version, policy version, verifier version, action, and outcome.

## 7. Cross-paper conclusions that directly determine the manuscript redesign

1. **Separate trusted schema from uncertain runtime knowledge.** Ontology/rules/physical invariants can form a relatively stable TBox/TCB; runtime device availability, measurement trust, cyber reachability, attack diagnosis, and action-success memory must be treated as uncertain ABox/belief state.

2. **Treat evidence ingestion as an attack surface.** Existing resilient-control work often assumes observer/detector outputs under specified bounds, while KG work often assumes graph-update inputs are benign. The new paper should explicitly connect these two gaps through a recovery-knowledge poisoning model.

3. **Use provenance as influence control, not metadata.** Evidence from multiple observations that share one compromised upstream source cannot be counted as independent support. Provenance groups should have capped total influence.

4. **Replace binary fact activation with calibrated belief.** Missing, stale, conflicting, and malicious evidence require a continuous or three-valued belief state. Operational activation thresholds should be asymmetric and risk-aware.

5. **Do not let uncertain knowledge bypass invariant physics.** Voltage, thermal, radiality, protection interlock, and actuator-capacity constraints remain authoritative. Evidence-dependent cyber prerequisites are probabilistic and should be checked separately.

6. **Use two time scales.** KG/belief updates can be frequent, but policy updates should be gated by trusted transitions, stability checks, candidate/stable model separation, and rollback.

7. **Theoretical claims should bound error propagation.** Useful theorems are bounded poisoning influence, false-authorization risk, finite poison correction time, policy-drift bounds under belief shift, and tolerable malicious provenance ratio—not generic full-MARL convergence.

8. **Experiments must vary evidence integrity directly.** Core variables should include missing-evidence ratio, stale/replayed evidence, conflicting-source ratio, compromised provenance-group ratio, confidence manipulation, outcome-memory poisoning, and attack duration/stealthiness. Physical recovery metrics should be connected causally to knowledge-integrity and decision-integrity metrics.

9. **Novelty boundary is now clear.** Dynamic KG, GAT/GNN, KG+DRL, knowledge-driven reconfiguration, online incremental graph learning, and cross-layer restoration all have direct prior art. The defensible new contribution is a bounded trustworthy online recovery knowledge state under adversarial evidence and mechanisms that prevent knowledge errors from propagating unchecked into recovery constraints and policies.

10. **Federated/heterogeneous learning remains inherited infrastructure.** It can remain in implementation if needed, but should not dominate the contribution statement or threat model because it overlaps the previous TDSC work and distracts from the new security question.
