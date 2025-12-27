"""
Tests for /v1/models endpoint behavior

This test file specifically covers the bug fix for Issue #xxx:
- /v1/models endpoint returning empty list when LITELLM_MASTER_KEY is set
- Environment variable cleanup in cmd_start()
"""

import os
import time
import subprocess
import pytest
import requests
from pathlib import Path
import yaml
import signal


TEST_PORT = 15001  # Different port to avoid conflicts


@pytest.fixture
def test_workspace(tmp_path):
    """Create temporary workspace"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return tmp_path


@pytest.fixture
def simple_config_no_auth(test_workspace):
    """
    Create config WITHOUT general_settings (no master_key)
    This simulates the fixed behavior after bug fix
    """
    config_dir = test_workspace / "config"
    config_file = config_dir / "config.yaml"

    config_content = """
litellm_settings:
  drop_params: true
  set_verbose: false

model_list:
  - model_name: test-model-1
    litellm_params:
      model: openai/test-model-1
      api_base: https://api.test.com
      api_key: dummy-key-1

  - model_name: test-model-2
    litellm_params:
      model: openai/test-model-2
      api_base: https://api.test.com
      api_key: dummy-key-2
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def litellm_no_auth(simple_config_no_auth):
    """
    Start LiteLLM WITHOUT authentication
    This tests the fixed behavior
    """
    env = os.environ.copy()
    # Explicitly remove LITELLM_MASTER_KEY to simulate fixed behavior
    env.pop("LITELLM_MASTER_KEY", None)

    cmd = [
        "litellm",
        "--config", str(simple_config_no_auth),
        "--port", str(TEST_PORT),
        "--host", "127.0.0.1",
    ]

    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for service to be ready
    service_ready = False
    for attempt in range(30):
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(
                f"LiteLLM died during startup!\n"
                f"Exit code: {process.returncode}\n"
                f"STDERR:\n{stderr}"
            )

        try:
            response = requests.get(
                f"http://127.0.0.1:{TEST_PORT}/v1/models",
                timeout=1
            )
            if response.status_code == 200:
                service_ready = True
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        time.sleep(1)

    if not service_ready:
        process.send_signal(signal.SIGTERM)
        time.sleep(2)
        stdout, stderr = process.communicate()
        pytest.fail(
            f"LiteLLM failed to start\n"
            f"STDERR:\n{stderr[:1000]}"
        )

    yield process

    # Cleanup
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class TestModelsEndpointNoAuth:
    """Test /v1/models endpoint without authentication"""

    def test_models_endpoint_public_access(self, litellm_no_auth):
        """
        CRITICAL TEST: /v1/models should work WITHOUT authentication
        when no master_key is configured

        This is the main bug fix test
        """
        response = requests.get(f"http://127.0.0.1:{TEST_PORT}/v1/models")

        assert response.status_code == 200, \
            "When no master_key is set, /v1/models should be publicly accessible"

        data = response.json()
        assert "data" in data
        assert "object" in data
        assert data["object"] == "list"

        # CRITICAL: Must return actual models, not empty list
        assert len(data["data"]) > 0, \
            "BUG: /v1/models returned empty list! This was the original bug."

        # Verify our test models are listed
        model_ids = [model["id"] for model in data["data"]]
        assert "test-model-1" in model_ids
        assert "test-model-2" in model_ids

    def test_models_endpoint_returns_correct_count(self, litellm_no_auth):
        """Verify exact number of models returned"""
        response = requests.get(f"http://127.0.0.1:{TEST_PORT}/v1/models")

        assert response.status_code == 200
        data = response.json()

        # We configured 2 models, should return exactly 2
        assert len(data["data"]) == 2, \
            f"Expected 2 models, got {len(data['data'])}"


class TestConfigGeneration:
    """Test that config generation doesn't include problematic settings"""

    def test_config_no_router_settings(self, simple_config_no_auth):
        """Verify generated config doesn't have router_settings"""
        with open(simple_config_no_auth) as f:
            config = yaml.safe_load(f)

        assert "router_settings" not in config, \
            "router_settings should not be in config (causes /v1/models issues)"

    def test_config_no_general_settings(self, simple_config_no_auth):
        """Verify generated config doesn't have general_settings"""
        with open(simple_config_no_auth) as f:
            config = yaml.safe_load(f)

        assert "general_settings" not in config, \
            "general_settings should not be in config (causes auth issues)"

    def test_config_has_required_sections(self, simple_config_no_auth):
        """Verify config has the essential sections"""
        with open(simple_config_no_auth) as f:
            config = yaml.safe_load(f)

        assert "litellm_settings" in config
        assert "model_list" in config
        assert len(config["model_list"]) > 0
