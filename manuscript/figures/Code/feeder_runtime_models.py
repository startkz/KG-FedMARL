"""Physical feeder adapters for the feeder-level recovery experiment.

IEEE33 and the supplied 69-bus radial benchmark are loaded from the uploaded
``kgfedmarl_env.zip``. Canonical IEEE123/8500 OpenDSS cases are loaded from a
pinned public OpenDSS test-feeder checkout supplied by the workflow.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import numpy as np

V_MIN, V_MAX = 0.90, 1.10
N_BLOCKS = {"IEEE33": 8, "Radial69-env": 10, "IEEE123": 12, "IEEE8500": 32}
N_AGENTS = {"IEEE33": 8, "Radial69-env": 10, "IEEE123": 12, "IEEE8500": 16}
INITIAL_BLOCK_FRACTION = 0.35


def balanced_blocks(names: Sequence[str], weights_kw: Sequence[float], n_blocks: int):
    n_blocks = max(1, min(int(n_blocks), len(names)))
    blocks: List[List[str]] = [[] for _ in range(n_blocks)]
    sums = np.zeros(n_blocks, dtype=float)
    order = np.argsort(-np.asarray(weights_kw, dtype=float))
    for idx in order:
        b = int(np.argmin(sums))
        blocks[b].append(str(names[int(idx)]))
        sums[b] += float(weights_kw[int(idx)])
    return blocks, sums


class BaseAdapter:
    def initialize_partial(self, fraction: float = INITIAL_BLOCK_FRACTION) -> None:
        n0 = max(1, int(round(len(self.blocks) * fraction)))
        initial = set(np.argsort(self.block_kw)[:n0].astype(int).tolist())
        self.set_enabled_blocks(initial)
        self.enabled_blocks = set(initial)

    @property
    def total_kw(self) -> float:
        return float(self.load_kw.sum())

    @property
    def served_ratio(self) -> float:
        if self.total_kw <= 0:
            return 0.0
        return float(sum(self.block_kw[i] for i in self.enabled_blocks) / self.total_kw)


class PandapowerAdapter(BaseAdapter):
    def __init__(self, feeder: str, net, n_blocks: int):
        import pandapower as pp
        self.pp = pp
        self.feeder = feeder
        self.net = net
        self.n_nodes = int(len(net.bus))
        self.load_names = [str(i) for i in net.load.index]
        self.load_kw = np.asarray(net.load.p_mw, dtype=float) * 1000.0
        self.blocks, self.block_kw = balanced_blocks(self.load_names, self.load_kw, n_blocks)
        self.enabled_blocks = set(range(len(self.blocks)))
        self.verifier_calls = 0
        self.safety_violations = 0

    def _apply(self, enabled: set[int]) -> None:
        active = {name for i in enabled for name in self.blocks[i]}
        self.net.load["in_service"] = [str(idx) in active for idx in self.net.load.index]

    def _solve(self) -> Tuple[bool, float]:
        t0 = time.perf_counter()
        try:
            self.pp.runpp(self.net, algorithm="nr", tolerance_mva=1e-8,
                          max_iteration=80, init="results", numba=False)
            converged = bool(self.net.converged)
        except Exception:
            converged = False
        elapsed = (time.perf_counter() - t0) * 1000.0
        if not converged:
            return False, elapsed
        v = np.asarray(self.net.res_bus.vm_pu, dtype=float)
        v = v[np.isfinite(v)]
        ok = bool(len(v) and v.min() >= V_MIN - 1e-9 and v.max() <= V_MAX + 1e-9)
        return ok, elapsed

    def set_enabled_blocks(self, blocks: Iterable[int]) -> None:
        self.enabled_blocks = {int(i) for i in blocks}
        self._apply(self.enabled_blocks)
        self._solve()

    def try_restore(self, block: int) -> Tuple[bool, float]:
        if block in self.enabled_blocks:
            return True, 0.0
        old = set(self.enabled_blocks)
        candidate = set(old); candidate.add(int(block))
        self._apply(candidate)
        self.verifier_calls += 1
        ok, ms = self._solve()
        if ok:
            self.enabled_blocks = candidate
            return True, ms
        self._apply(old); self._solve()
        return False, ms


class OpenDSSAdapter(BaseAdapter):
    def __init__(self, feeder: str, master: Path, n_blocks: int):
        from dss import DSS
        self.DSS = DSS
        self.feeder = feeder
        self.master = Path(master).resolve()
        DSS.Text.Command = f"Compile [{self.master}]"
        # Static mode is the OpenDSS snapshot-control mode intended for power
        # flows that may require several regulator tap changes.  The default
        # MaxControlIter=10 is too small for the 8500-node feeder after large
        # block-shedding changes, so allow the regulator/capacitor controls to
        # settle rather than freezing them at the pre-disturbance state.
        DSS.Text.Command = "Set Maxiterations=50"
        DSS.Text.Command = "Set MaxControlIter=1000"
        DSS.Text.Command = "Set ControlMode=Static"
        DSS.Text.Command = "Solve"
        if not bool(DSS.ActiveCircuit.Solution.Converged):
            raise RuntimeError(f"OpenDSS base case did not converge: {self.master}")
        self.n_nodes = int(DSS.ActiveCircuit.NumBuses)
        loads = DSS.ActiveCircuit.Loads
        names, kws = [], []
        i = loads.First
        while i:
            names.append(str(loads.Name))
            kws.append(max(0.0, float(loads.kW)))
            i = loads.Next
        if not names:
            raise RuntimeError(f"No loads found in {self.master}")
        self.load_names = names
        self.load_kw = np.asarray(kws, dtype=float)
        self.blocks, self.block_kw = balanced_blocks(names, kws, n_blocks)
        self.enabled_blocks = set(range(len(self.blocks)))
        self.verifier_calls = 0
        self.safety_violations = 0

    def initialize_partial(self, fraction: float = INITIAL_BLOCK_FRACTION) -> None:
        if self.feeder != "IEEE8500":
            super().initialize_partial(fraction)
            return

        # The 8500-node feeder is sensitive to coarse, globally balanced load
        # blocks. Build the starting state through the same authoritative AC
        # verifier used online instead of assuming that an arbitrary 35% block
        # subset is feasible. Smaller 32-way blocks preserve enough decision
        # granularity for a 24-step restoration horizon while avoiding the
        # all-or-nothing 14-block behavior observed in the first stress test.
        self.set_enabled_blocks(set())
        target = max(0.0, min(1.0, float(fraction)))
        order = np.argsort(self.block_kw)
        for b in order:
            ok, _ = self.try_restore(int(b))
            if ok and self.served_ratio >= target - 1e-9:
                break
        if not self.enabled_blocks:
            raise RuntimeError("IEEE8500: no AC-feasible initial restoration block")
        # Initialization is part of scenario construction rather than online
        # authorization, so do not charge its verifier calls to T_gate/results.
        self.verifier_calls = 0
        self.safety_violations = 0

    def _edit(self, names: Iterable[str], enabled: bool) -> None:
        value = "yes" if enabled else "no"
        for name in names:
            self.DSS.Text.Command = f"Edit Load.{name} enabled={value}"

    def _solve(self) -> Tuple[bool, float]:
        t0 = time.perf_counter()
        try:
            self.DSS.Text.Command = "Solve"
            converged = bool(self.DSS.ActiveCircuit.Solution.Converged)
        except Exception:
            converged = False
        elapsed = (time.perf_counter() - t0) * 1000.0
        if not converged:
            return False, elapsed
        # DSS-Python exposes per-unit bus magnitudes through AllBusVmagPu.
        # De-energized entries are filtered because partial restoration can
        # intentionally leave buses without energized load.
        v = np.asarray(self.DSS.ActiveCircuit.AllBusVmagPu, dtype=float)
        v = v[np.isfinite(v) & (v > 0.05)]
        ok = bool(len(v) and v.min() >= V_MIN - 1e-9 and v.max() <= V_MAX + 1e-9)
        return ok, elapsed

    def set_enabled_blocks(self, blocks: Iterable[int]) -> None:
        wanted_blocks = {int(i) for i in blocks}
        wanted = {name for i in wanted_blocks for name in self.blocks[i]}
        for name in self.load_names:
            self.DSS.Text.Command = f"Edit Load.{name} enabled={'yes' if name in wanted else 'no'}"
        self.enabled_blocks = wanted_blocks
        self._solve()

    def try_restore(self, block: int) -> Tuple[bool, float]:
        if block in self.enabled_blocks:
            return True, 0.0
        self._edit(self.blocks[int(block)], True)
        self.verifier_calls += 1
        ok, ms = self._solve()
        if ok:
            self.enabled_blocks.add(int(block))
            return True, ms
        self._edit(self.blocks[int(block)], False); self._solve()
        return False, ms


def make_adapter(feeder: str, env_root: Path, opendss_root: Path):
    if feeder in ("IEEE33", "Radial69-env"):
        if str(env_root) not in sys.path:
            sys.path.insert(0, str(env_root))
        from feeders import pandapower_33_69 as f
        net = f.build_33() if feeder == "IEEE33" else f.build_69()
        return PandapowerAdapter(feeder, net, N_BLOCKS[feeder])
    if feeder == "IEEE123":
        master = opendss_root / "Distrib/IEEETestCases/123Bus/IEEE123Master.dss"
        return OpenDSSAdapter(feeder, master, N_BLOCKS[feeder])
    if feeder == "IEEE8500":
        master = opendss_root / "Distrib/IEEETestCases/8500-Node/Master.dss"
        return OpenDSSAdapter(feeder, master, N_BLOCKS[feeder])
    raise ValueError(feeder)
