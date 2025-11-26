import copy
from dataclasses import dataclass
from typing import Any

from toonverter.analysis.analyzer import TiktokenCounter
from toonverter.encoders import encode

from .policy import OptimizationPolicy, PriorityLevel


@dataclass
class DegradationCandidate:
    path: list[str]
    original_size: int
    degraded_size: int
    priority: float
    action: str  # "prune", "truncate", "round"
    node_ref: Any
    key: Any


class ContextOptimizer:
    """Optimizes data structure to fit within a token budget."""

    def __init__(
        self,
        budget: int,
        policy: OptimizationPolicy | None = None,
        apply_lightweight_prepass: bool = False,
        model: str = "gpt-4",  # Added model parameter for TiktokenCounter
    ) -> None:
        self.budget = budget
        self.policy = policy or OptimizationPolicy()
        # When False (default) the lightweight pre-pass is only applied if the
        # structure is OVER the budget. When True, it runs once even if within budget.
        self.apply_lightweight_prepass = apply_lightweight_prepass
        self._counter = TiktokenCounter(model=model)  # Initialize counter once

    def optimize(self, data: Any) -> Any:
        optimized_data = copy.deepcopy(data)

        current_size = self._measure(optimized_data)

        # Run lightweight pre-pass only if:
        #  - structure is over budget (common case)
        #  - OR caller explicitly opted in via apply_lightweight_prepass
        if current_size > self.budget or self.apply_lightweight_prepass:
            candidates = self._scan_candidates(optimized_data)
            light_candidates = [c for c in candidates if c.action in ("round", "truncate")]
            if light_candidates:

                def _light_score(c: DegradationCandidate) -> float:
                    weight = 2.0 if c.action == "round" else 1.5
                    return (c.original_size - c.degraded_size) * (1.1 - c.priority) * weight

                light_candidates.sort(key=_light_score, reverse=True)
                for cand in light_candidates:
                    self._apply_degradation(cand)
                    savings = cand.original_size - cand.degraded_size
                    current_size -= savings
                    if current_size <= self.budget:
                        break
                current_size = self._measure(optimized_data)

        # If within budget now, return (preserve no-op behaviour)
        if current_size <= self.budget:
            return optimized_data

        # Full degradations pass (including prune)
        for _ in range(10):
            if current_size <= self.budget:
                break

            candidates = self._scan_candidates(optimized_data)
            if not candidates:
                break

            def _score(c: DegradationCandidate) -> float:
                base = (c.original_size - c.degraded_size) * (1.1 - c.priority)
                if c.action == "round":
                    return base * 2.0
                if c.action == "truncate":
                    return base * 1.5
                return base

            candidates.sort(key=_score, reverse=True)

            for cand in candidates:
                self._apply_degradation(cand)
                savings = cand.original_size - cand.degraded_size
                current_size -= savings
                if current_size <= self.budget:
                    break

            current_size = self._measure(optimized_data)

        return optimized_data

    def _measure(self, data: Any) -> int:
        return self._counter.count_tokens(encode(data))

    def _scan_candidates(self, data: Any) -> list[DegradationCandidate]:
        candidates: list[DegradationCandidate] = []
        self._visit(data, [], candidates)
        return candidates

    def _visit(self, node: Any, path: list[str], candidates: list[DegradationCandidate]) -> None:
        if isinstance(node, dict):
            for k, v in list(node.items()):
                self._analyze_node(v, [*path, str(k)], candidates, parent=node, key=k)
                if isinstance(v, (dict, list)):
                    self._visit(v, [*path, str(k)], candidates)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                self._analyze_node(v, [*path, str(i)], candidates, parent=node, key=i)
                if isinstance(v, (dict, list)):
                    self._visit(v, [*path, str(i)], candidates)

    def _analyze_node(
        self,
        node: Any,
        path: list[str],
        candidates: list[DegradationCandidate],
        parent: Any,
        key: Any,
    ) -> None:
        key_name = path[-1] if path else "root"
        priority = self.policy.get_priority(key_name, len(path))

        if priority >= PriorityLevel.CRITICAL.value:
            return

        if isinstance(node, str) and len(node) > self.policy.max_string_length:
            est = len(node) // 3
            degraded = self.policy.max_string_length // 3
            candidates.append(
                DegradationCandidate(
                    path=path,
                    original_size=est,
                    degraded_size=degraded,
                    priority=priority,
                    action="truncate",
                    node_ref=parent,
                    key=key,
                )
            )
            return

        if isinstance(node, float) and self.policy.float_precision is not None:
            s_orig = str(node)
            s_new = f"{node:.{self.policy.float_precision}f}"
            if len(s_new) < len(s_orig) or s_new != s_orig:
                candidates.append(
                    DegradationCandidate(
                        path=path,
                        original_size=max(1, len(s_orig) // 3),
                        degraded_size=max(1, len(s_new) // 3),
                        priority=priority,
                        action="round",
                        node_ref=parent,
                        key=key,
                    )
                )

        if priority <= PriorityLevel.NORMAL.value:
            try:
                node_str = encode(node)
                size = self._counter.count_tokens(node_str)  # Use self._counter here
            except Exception:
                size = 1

            candidates.append(
                DegradationCandidate(
                    path=path,
                    original_size=size,
                    degraded_size=0,
                    priority=priority,
                    action="prune",
                    node_ref=parent,
                    key=key,
                )
            )

    def _apply_degradation(self, candidate: DegradationCandidate) -> None:
        parent = candidate.node_ref
        key = candidate.key

        if candidate.action == "prune":
            if isinstance(parent, dict) and key in parent:
                del parent[key]
            elif isinstance(parent, list) and isinstance(key, int) and 0 <= key < len(parent):
                parent[key] = None

        elif candidate.action == "truncate":
            original = parent[key]
            if isinstance(original, str):
                limit = self.policy.max_string_length
                parent[key] = original[:limit] + "...[TRUNC]"

        elif candidate.action == "round":
            original = parent[key]
            if isinstance(original, float):
                parent[key] = float(f"{original:.{self.policy.float_precision}f}")
