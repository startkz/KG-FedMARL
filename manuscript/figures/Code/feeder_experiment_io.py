"""Standard per-seed CSV contract for KG-FedMARL feeder experiments.

The contract is intentionally provenance-aware: submission plots should only use
rows whose ``source_kind`` is ``simulator`` or ``measured``. Legacy hard-coded
plot arrays may be exported for traceability with ``source_kind=legacy_draft``
but are rejected by the final plotting pipeline by default.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping

SCHEMA_VERSION = "1.0"

FIELDS = [
    "schema_version", "run_id", "timestamp_utc", "source_kind", "source_commit",
    "seed", "feeder", "n_nodes", "n_agents", "method", "ablation",
    "attack_type", "attack_level", "f_p", "B_z", "H_A", "epsilon_s",
    "evidence_sources", "provenance_groups", "prereq_per_action",
    "AURC", "T_crit", "D_B", "P_FA", "T_corr", "D_pi",
    "fallback_rate", "gate_latency_ms", "recovered_final", "verifier_calls",
    "safety_violations", "status", "raw_log_path", "result_sha256", "notes",
]

NUMERIC_INT_FIELDS = {
    "seed", "n_nodes", "n_agents", "f_p", "B_z", "H_A",
    "evidence_sources", "provenance_groups", "prereq_per_action",
    "verifier_calls", "safety_violations",
}
NUMERIC_FLOAT_FIELDS = {
    "epsilon_s", "AURC", "T_crit", "D_B", "P_FA", "T_corr", "D_pi",
    "fallback_rate", "gate_latency_ms", "recovered_final",
}
FINAL_REQUIRED_METRICS = {
    "AURC", "T_crit", "D_B", "P_FA", "T_corr", "D_pi",
    "fallback_rate", "gate_latency_ms",
}
ALLOWED_SOURCE_KINDS = {"simulator", "measured", "controlled", "legacy_draft", "mock"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(path: os.PathLike[str] | str) -> str:
    p = Path(path)
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def _to_number(name: str, value):
    if value in (None, ""):
        return ""
    if name in NUMERIC_INT_FIELDS:
        return int(value)
    if name in NUMERIC_FLOAT_FIELDS:
        v = float(value)
        if not math.isfinite(v):
            raise ValueError(f"{name} must be finite, got {value!r}")
        return v
    return value


def canonicalize(row: Mapping[str, object]) -> Dict[str, object]:
    out: Dict[str, object] = {k: "" for k in FIELDS}
    for key, value in row.items():
        if key not in out:
            raise KeyError(f"Unknown feeder-log field: {key}")
        out[key] = _to_number(key, value)
    out["schema_version"] = str(out["schema_version"] or SCHEMA_VERSION)
    out["timestamp_utc"] = str(out["timestamp_utc"] or utc_now())
    out["source_kind"] = str(out["source_kind"] or "simulator")
    out["status"] = str(out["status"] or "ok")
    if out["source_kind"] not in ALLOWED_SOURCE_KINDS:
        raise ValueError(f"Unsupported source_kind={out['source_kind']!r}")

    identity = {
        k: out[k] for k in (
            "source_kind", "source_commit", "seed", "feeder", "n_nodes",
            "n_agents", "method", "ablation", "attack_type", "attack_level",
            "f_p", "B_z", "H_A", "epsilon_s"
        )
    }
    if not out["run_id"]:
        payload = json.dumps(identity, sort_keys=True, separators=(",", ":"), default=str)
        out["run_id"] = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]
    return out


def validate(row: Mapping[str, object], *, require_final_metrics: bool = False) -> None:
    for key in ("seed", "feeder", "method", "attack_type", "attack_level", "source_kind"):
        if row.get(key, "") == "":
            raise ValueError(f"Missing required field {key!r}")
    if str(row.get("status", "ok")) != "ok":
        return
    if require_final_metrics:
        missing = [k for k in FINAL_REQUIRED_METRICS if row.get(k, "") == ""]
        if missing:
            raise ValueError("Missing final-result metrics: " + ", ".join(sorted(missing)))


def append_row(csv_path: os.PathLike[str] | str, row: Mapping[str, object], *, require_final_metrics: bool = False) -> Dict[str, object]:
    out = canonicalize(row)
    validate(out, require_final_metrics=require_final_metrics)
    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS, extrasaction="raise")
        if not exists:
            writer.writeheader()
        writer.writerow(out)
    return out


def read_rows(csv_path: os.PathLike[str] | str) -> List[Dict[str, object]]:
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames != FIELDS:
            missing = [k for k in FIELDS if k not in (reader.fieldnames or [])]
            extra = [k for k in (reader.fieldnames or []) if k not in FIELDS]
            raise ValueError(f"CSV schema mismatch; missing={missing}, extra={extra}")
        rows = []
        for raw in reader:
            rows.append(canonicalize(raw))
    return rows


def parse_seed_spec(spec: str) -> List[int]:
    """Parse '1,2,5-8' into an ordered unique list."""
    vals: List[int] = []
    seen = set()
    for token in spec.split(","):
        token = token.strip()
        if not token:
            continue
        if "-" in token:
            a, b = token.split("-", 1)
            lo, hi = int(a), int(b)
            step = 1 if hi >= lo else -1
            seq = range(lo, hi + step, step)
        else:
            seq = [int(token)]
        for x in seq:
            if x not in seen:
                vals.append(x)
                seen.add(x)
    if not vals:
        raise ValueError("Seed specification is empty")
    return vals
