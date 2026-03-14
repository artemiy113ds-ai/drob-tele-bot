"""
pytest configuration for tests
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

@pytest.fixture
def app():
    """App fixture"""
    from main_v3 import app as fastapi_app
    return fastapi_app

@pytest.fixture
def client(app):
    """Test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)
