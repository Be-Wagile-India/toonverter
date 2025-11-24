import copy
from dataclasses import dataclass
from typing import Any

from toonverter.analysis.analyzer import count_tokens

from .policy import OptimizationPolicy, PriorityLevel


@dataclass
class DegradationCandidate:
    path: list[str]
    original_size: int
    degraded_size: int
    priority: float
    action: str  # "prune", "truncate", "round"
    node_ref: Any  # Reference to parent or container
    key: Any  # Key/Index in parent


class ContextOptimizer:
    """
    Intelligently optimizes data structure to fit within a token budget.
    """

    def __init__(self, budget: int, policy: OptimizationPolicy | None = None):
        self.budget = budget
        self.policy = policy or OptimizationPolicy()

    def optimize(self, data: Any) -> Any:
        """
        Main entry point. Returns a modified copy of data fitting the budget.
        """
        # 1. Quick Check
        # We need a deep copy because we will destructively modify the data
        optimized_data = copy.deepcopy(data)

        current_size = self._measure(optimized_data)
        if current_size <= self.budget:
            return optimized_data

        # 2. Iterative Optimization Loop
        # We assume a max of 10 passes to prevent infinite loops,
        # though usually 1-2 passes are enough.
        for _ in range(10):
            if current_size <= self.budget:
                break

            # Scan for candidates
            candidates = self._scan_candidates(optimized_data)

            if not candidates:
                # Cannot optimize further without destroying structure
                # Fallback: Depending on strictness, we might return as-is or raise error.
                # For "fool-proof", we return best effort.
                break

            # Sort by Efficiency: (Savings * (1 - Priority))
            # High savings + Low priority = High Score
            candidates.sort(
                key=lambda c: (c.original_size - c.degraded_size) * (1.1 - c.priority), reverse=True
            )

            # Apply degradations until we are close to budget
            savings_accumulated = 0

            for cand in candidates:
                self._apply_degradation(cand)
                savings = cand.original_size - cand.degraded_size
                savings_accumulated += savings

                # Update current size estimate
                current_size -= savings

                if current_size <= self.budget:
                    break

            # Re-measure to be precise (accounting for structural overhead changes)
            current_size = self._measure(optimized_data)

        return optimized_data

    def _measure(self, data: Any) -> int:
        """Measure token count of data."""
        # Local import to avoid circular dependency with ToonEncoder
        from toonverter.encoders import encode  # noqa: PLC0415

        return count_tokens(encode(data))

    def _scan_candidates(self, data: Any) -> list[DegradationCandidate]:
        """
        Walks the tree and identifies potential optimization actions.
        """
        candidates: list[DegradationCandidate] = []
        self._visit(data, [], candidates)
        return candidates

    def _visit(self, node: Any, path: list[str], candidates: list[DegradationCandidate]):
        """Recursive visitor."""

        # We only look at containers (Dict/List) and Strings for now.
        if isinstance(node, dict):
            for k, v in node.items():
                self._analyze_node(v, [*path, str(k)], candidates, parent=node, key=k)
                if isinstance(v, (dict, list)):
                    self._visit(v, [*path, str(k)], candidates)

        elif isinstance(node, list):
            for i, v in enumerate(node):
                # For lists, we might not want to visit every single item if list is huge.
                # But for correctness, we do.
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
    ):
        """Analyze a specific node for degradation potential."""

        # Heuristic Priority
        # Use the last key in path for name-based priority
        key_name = path[-1] if path else "root"
        priority = self.policy.get_priority(key_name, len(path))

        # Don't touch criticals
        if priority >= PriorityLevel.CRITICAL.value:
            return

        # Strategy 1: Truncate Long Strings
        if isinstance(node, str) and len(node) > self.policy.max_string_length:
            est_tokens = len(node) // 3  # Rough estimate
            # Degraded: truncated string
            degraded_len = self.policy.max_string_length // 3

            candidates.append(
                DegradationCandidate(
                    path=path,
                    original_size=est_tokens,
                    degraded_size=degraded_len,
                    priority=priority,
                    action="truncate",
                    node_ref=parent,
                    key=key,
                )
            )
            return  # Don't propose pruning if we can truncate (for now)

        # Strategy 2: Round Floats
        if isinstance(node, float) and self.policy.float_precision is not None:
            # Check if rounding saves space
            s_orig = str(node)
            s_new = f"{node:.{self.policy.float_precision}f}"
            if len(s_new) < len(s_orig):
                candidates.append(
                    DegradationCandidate(
                        path=path,
                        original_size=len(s_orig) // 3,
                        degraded_size=len(s_new) // 3,
                        priority=priority,  # Higher priority than prune
                        action="round",
                        node_ref=parent,
                        key=key,
                    )
                )

        # Strategy 3: Prune (Remove)
        # We propose removing this node entirely if it's low priority
        # Size estimation is expensive, so we do it only for likely candidates
        if priority <= PriorityLevel.NORMAL.value:
            # Fast estimation of node size
            from toonverter.encoders import encode  # noqa: PLC0415

            node_str = encode(node)
            size = count_tokens(node_str)

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

    def _apply_degradation(self, candidate: DegradationCandidate):
        """Apply the action to the data structure."""
        parent = candidate.node_ref
        key = candidate.key

        if candidate.action == "prune":
            if isinstance(parent, dict):
                del parent[key]
            elif isinstance(parent, list):
                # Replacing with None to preserve index alignment for others,
                # or we could remove. Removing from list shifts indices which breaks
                # other candidates targeting this list.
                # Safe approach: Replace with None (or minimal placeholder)
                # Ideally, we should handle list index shifts, but for simplicity:
                parent[key] = None  # Or specialized "Removed" marker if supported

        elif candidate.action == "truncate":
            original = parent[key]
            limit = self.policy.max_string_length
            parent[key] = original[:limit] + "...[TRUNC]"

        elif candidate.action == "round":
            original = parent[key]
            parent[key] = float(f"{original:.{self.policy.float_precision}f}")
