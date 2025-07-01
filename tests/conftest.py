import pytest
import os
import sys

# Add the source directories to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambdas/upload'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambdas/process'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../src/lambdas/status'))

# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )

def pytest_collection_modifyitems(config, items):
    """Automatically mark integration tests as slow"""
    for item in items:
        if "integration" in str(item.fspath) or "test_full_workflow" in item.name:
            item.add_marker(pytest.mark.slow)