"""
Pytest configuration and shared fixtures for backend tests.
"""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file in project root
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")


def pytest_configure(config):
    """Configure pytest with environment setup and custom markers."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires external APIs)"
    )
    config.addinivalue_line(
        "markers", "openai: mark test as requiring OpenAI API"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test (no external dependencies)"
    )
    
    # Verify required environment variables are available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  WARNING: OPENAI_API_KEY not found in environment variables.")
        print("   Tests that require OpenAI API access will be skipped.")
        print("   Please create a .env file with your OpenAI API key.\n")


def pytest_collection_modifyitems(config, items):
    """Mark tests that require API keys and handle missing environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    
    for item in items:
        # Skip tests that require OpenAI API if key is not available
        if hasattr(item, 'get_closest_marker'):
            if item.get_closest_marker('openai') and not api_key:
                item.add_marker(pytest.mark.skip(reason="Requires OPENAI_API_KEY"))


@pytest.fixture(scope="session")
def openai_api_key():
    """Provide OpenAI API key for tests that need it."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY environment variable not set")
    return api_key 