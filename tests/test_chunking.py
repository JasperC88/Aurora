"""
Tests for Memory Guard and Chunking Mechanisms
"""

import pandas as pd
from aurora.utils.memory import MemoryGuard, enforce_memory_limit, get_current_memory_mb


def test_get_current_memory():
    mem = get_current_memory_mb()
    assert mem > 0, "Memory usage should be positive"


def test_memory_guard_context():
    with MemoryGuard(stage_name="TestStage", max_allowed_mb=1024.0) as guard:
        # Create a small dummy array
        dummy = [x * 2 for x in range(10000)]
        assert len(dummy) == 10000
    assert guard.end_mem_mb >= 0


def test_chunking_iteration():
    # Simulate a stream of 5 DataFrame chunks
    def chunk_generator():
        for i in range(5):
            yield pd.DataFrame({"batch_id": [i] * 100, "val": range(100)})

    total_rows = 0
    for chunk in chunk_generator():
        total_rows += len(chunk)

    assert total_rows == 500
