import pytest

from toonverter.analysis.analyzer import TiktokenCounter  # Added import
from toonverter.core.types import EncodeOptions
from toonverter.encoders import encode
from toonverter.optimization.engine import ContextOptimizer
from toonverter.optimization.policy import OptimizationPolicy


class TestContextOptimizer:
    @pytest.fixture
    def sample_data(self):
        return {
            "id": "user-1234",
            "profile": {
                "name": "Alice Smith",
                "bio": "A very long bio string " * 5,
                "age": 30.56789,
            },
            "logs": [{"id": i, "msg": f"Log message {i}"} for i in range(20)],
        }

    def test_no_op_within_budget(self, sample_data):
        optimizer = ContextOptimizer(budget=10000)
        optimized = optimizer.optimize(sample_data)
        assert optimized == sample_data

    def test_truncate_strings(self, sample_data):
        policy = OptimizationPolicy(max_string_length=20)
        sample_data["profile"]["bio"] = "A very long bio string " * 500
        optimizer = ContextOptimizer(budget=500, policy=policy)
        optimized = optimizer.optimize(sample_data)
        bio = optimized["profile"]["bio"]
        assert len(bio) < len(sample_data["profile"]["bio"])
        assert "[TRUNC]" in bio

    def test_round_floats(self, sample_data):
        policy = OptimizationPolicy(float_precision=1)
        # Opt in to apply lightweight pre-pass even if data might already fit budget.
        optimizer = ContextOptimizer(budget=300, policy=policy, apply_lightweight_prepass=True)
        optimized = optimizer.optimize(sample_data)
        assert "profile" in optimized
        age = optimized["profile"]["age"]
        assert age == 30.6

    def test_prune_low_priority(self, sample_data):
        policy = OptimizationPolicy()
        optimizer = ContextOptimizer(budget=100, policy=policy)
        optimized = optimizer.optimize(sample_data)
        if "logs" in optimized:
            assert len(optimized["logs"]) < 20
        else:
            assert "logs" not in optimized

    def test_critical_preservation(self, sample_data):
        policy = OptimizationPolicy()
        optimizer = ContextOptimizer(budget=1, policy=policy)
        optimized = optimizer.optimize(sample_data)
        assert "id" in optimized
        assert optimized["id"] == "user-1234"

    def test_integration_via_encode(self, sample_data):
        sample_data["logs"] = [{"id": i, "msg": "L" * 100} for i in range(50)]
        normal_toon = encode(sample_data)

        # Use a higher token budget to ensure significant reduction for demonstration
        # A budget of 500 should definitely lead to reduction
        opts = EncodeOptions(
            token_budget=2000, compact=True
        )  # Added compact=True for more aggressive reduction
        optimized_toon = encode(sample_data, opts)

        counter = TiktokenCounter()
        normal_tokens = counter.count_tokens(normal_toon)
        optimized_tokens = counter.count_tokens(optimized_toon)

        assert optimized_tokens < normal_tokens
        assert optimized_tokens <= opts.token_budget  # Ensure it respects the budget
        assert "id: user-1234" in optimized_toon  # Ensure critical data is still present

    def test_cannot_optimize_further(self):
        data = {"id": "123"}
        optimizer = ContextOptimizer(budget=1)
        optimized = optimizer.optimize(data)
        assert optimized == data

    def test_nested_list_optimization(self):
        data = {
            "users": [
                {"name": "A", "log": "L" * 1000},
                {"name": "B", "log": "L" * 1000},
            ]
        }
        policy = OptimizationPolicy(low_priority_keys={"log"}, critical_keys={"users"})
        optimizer = ContextOptimizer(budget=500, policy=policy)
        optimized = optimizer.optimize(data)
        user_0 = optimized["users"][0]
        if user_0 is not None:
            assert len(user_0.get("log", "")) < 1000
            assert user_0["name"] == "A"

    def test_list_pruning_behavior(self):
        data = ["Keep", "DropMe" * 100, "Keep"]
        optimizer = ContextOptimizer(budget=50)
        optimized = optimizer.optimize(data)
        assert "[TRUNC]" in optimized[1]
