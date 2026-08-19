# Feeder experiment logging and final-figure pipeline

## Why this pipeline exists

The current repository contains plotting programs and controlled mechanism-level experiments, but it does **not** contain an executable IEEE 33/69/123/8500 feeder power-flow/co-simulation environment or raw per-seed feeder logs. Several legacy scripts store draft arrays directly in Python source. Those arrays are useful for layout recovery, but they are not seed-level simulation evidence.

The feeder pipeline therefore separates three things that must not be conflated:

1. `source_kind=simulator` — rows emitted by an executable feeder simulator/co-simulator;
2. `source_kind=measured` — rows derived from archived measured/co-simulation logs;
3. `source_kind=legacy_draft` — values recovered from old hard-coded plotting arrays; retained only for provenance and excluded from final plots by default.

## Standard CSV contract

Every successful seed is one row. The core identity fields are `seed`, `feeder`, `n_nodes`, `n_agents`, `method`, `ablation`, `attack_type`, `attack_level`, and the attack budget `(f_p, B_z, H_A, epsilon_s)`. The primary result tuple is:

`AURC, T_crit, D_B, P_FA, T_corr, D_pi, fallback_rate, gate_latency_ms`.

Optional diagnostics include `recovered_final`, `verifier_calls`, and `safety_violations`. Each row also stores `source_kind`, `source_commit`, `raw_log_path`, and a SHA-256 digest of the simulator result JSON.

## Running an actual simulator per seed

The actual simulator can be in this repository or external. It must write a JSON object to the path supplied through `KG_RESULT_JSON`. The wrapper also exports experiment metadata as `KG_*` environment variables.

Example:

```bash
python figures/Code/feeder_seed_runner.py \
  --output figures/results/feeder_runs.csv \
  --seeds 1-5 \
  --feeder IEEE33 --n-nodes 33 --n-agents 8 \
  --method KG-FedMARL --ablation full \
  --attack-type mixed --attack-level medium \
  --f-p 2 --B-z 8 --H-A 10 --epsilon-s 0.02 \
  --evidence-sources 24 --provenance-groups 8 --prereq-per-action 4 \
  -- python /path/to/actual_feeder_simulator.py
```

The simulator result JSON must contain at least:

```json
{
  "AURC": 0.0,
  "T_crit": 0.0,
  "D_B": 0.0,
  "P_FA": 0.0,
  "T_corr": 0.0,
  "D_pi": 0.0,
  "fallback_rate": 0.0,
  "gate_latency_ms": 0.0
}
```

Do not synthesize missing metrics in the runner. A failed or incomplete seed is written with `status=failed`/`invalid` and is excluded from final aggregation.

## Generating the four final result groups

After collecting at least five successful seeds for every compared configuration:

```bash
python figures/Code/plot_feeder_results.py \
  --input figures/results/feeder_runs.csv \
  --output-dir figures/final_feeder_results \
  --min-seeds 5 \
  --baseline-attack-type mixed \
  --baseline-attack-level medium
```

The script produces four result groups from **simulator/measured rows only**:

- `feeder_end_to_end_baseline.*` — physical end-to-end comparison, with a summary CSV that also records `D_B`, `P_FA`, and `D_pi`;
- `feeder_attack_intensity.*` — belief distortion under increasing attack intensity, with AURC and false-authorization statistics in the summary CSV;
- `feeder_security_ablation.*` — false-authorization effect of trust-boundary ablations, with `D_B`, `D_pi`, and AURC in the summary CSV;
- `feeder_scalability.*` — gate latency versus feeder size, with AURC and fallback statistics in the summary CSV.

`legacy_draft`, `controlled`, and `mock` rows are rejected unless `--allow-nonreal` is explicitly supplied for smoke testing. Outputs generated with that flag must not be used as submission evidence.

## Legacy provenance export

To archive the old hard-coded arrays without treating them as measured data:

```bash
python figures/Code/export_legacy_draft_csv.py \
  --legacy-script figures/Code/kgfedmarl_experiment_figures.py \
  --output figures/results/legacy_draft.csv
```

These rows use `seed=-1` and `source_kind=legacy_draft` by design.
