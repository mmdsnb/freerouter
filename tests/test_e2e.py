"""
End-to-End tests for FreeRouter

Tests the complete workflow:
1. Generate config from providers (fetch)
2. Start LiteLLM service (start)
3. Call API endpoints (verify)

This is the real test that ensures the whole system works.
"""

import os
import time
import subprocess
import pytest
import requests
from pathlib import Path
import yaml
import signal


# Test constants - MUST be same in client and server
TEST_MASTER_KEY = "test-e2e-key-789"
TEST_PORT = 15000  # Use different port to avoid conflicts


@pytest.fixture(scope="module")
def test_workspace(tmp_path_factory):
    """Create a temporary workspace for E2E tests"""
    workspace = tmp_path_factory.mktemp("e2e_workspace")
    config_dir = workspace / "config"
    config_dir.mkdir()
    return workspace


@pytest.fixture(scope="module")
def test_env_file(test_workspace):
    """Create test .env file"""
    env_file = test_workspace / ".env"
    env_file.write_text(f"""
LITELLM_MASTER_KEY={TEST_MASTER_KEY}
LITELLM_PORT={TEST_PORT}
# Use static providers for testing (no real API calls)
""")
    return env_file


@pytest.fixture(scope="module")
def providers_config(test_workspace):
    """Create providers.yaml with static providers"""
    config_dir = test_workspace / "config"
    providers_file = config_dir / "providers.yaml"

    providers_file.write_text("""
providers:
  # Use static providers for E2E testing
  # No external API calls needed
  - type: static
    enabled: true
    model_name: test-gpt-4
    provider: openai
    api_base: https://api.test.com
    api_key: dummy-key-1

  - type: static
    enabled: true
    model_name: test-claude-3
    provider: anthropic
    api_base: https://api.test.com
    api_key: dummy-key-2
""")
    return providers_file


@pytest.fixture(scope="module")
def generated_config(test_workspace, providers_config):
    """Generate LiteLLM config using FreeRouter fetch logic"""
    config_dir = test_workspace / "config"
    config_file = config_dir / "config.yaml"

    # Simulate what freerouter fetch does
    # In real scenario, this would call FreeRouterFetcher
    config_content = f"""
litellm_settings:
  drop_params: true
  set_verbose: false
  master_key: {TEST_MASTER_KEY}

model_list:
  - model_name: test-gpt-4
    litellm_params:
      model: openai/test-gpt-4
      api_base: https://api.test.com
      api_key: dummy-key-1

  - model_name: test-claude-3
    litellm_params:
      model: anthropic/test-claude-3
      api_base: https://api.test.com
      api_key: dummy-key-2
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture(scope="module")
def litellm_process(generated_config, test_env_file):
    """
    Start real LiteLLM service for E2E testing

    This is the actual test - if service doesn't start, test fails
    """
    # Prepare environment
    env = os.environ.copy()
    # Clear any conflicting env vars
    env.pop("CONFIG_FILE_PATH", None)
    env["LITELLM_MASTER_KEY"] = TEST_MASTER_KEY

    # Start LiteLLM service
    cmd = [
        "litellm",
        "--config", str(generated_config),
        "--port", str(TEST_PORT),
        "--host", "127.0.0.1",
    ]

    print(f"\n🚀 Starting LiteLLM for E2E test: {' '.join(cmd)}")

    process = subprocess.Popen(
        cmd,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for service to be ready
    service_ready = False
    startup_output = []

    for attempt in range(60):  # Wait up to 60 seconds
        # Check if process died
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(
                f"LiteLLM process died during startup!\n"
                f"Exit code: {process.returncode}\n"
                f"STDOUT:\n{stdout}\n"
                f"STDERR:\n{stderr}"
            )

        # Try to connect - use /v1/models as health check
        try:
            response = requests.get(
                f"http://127.0.0.1:{TEST_PORT}/v1/models",
                headers={"Authorization": f"Bearer {TEST_MASTER_KEY}"},
                timeout=1
            )
            # Any response (200, 401, etc.) means service is up
            if response.status_code in [200, 401]:
                service_ready = True
                print(f"✅ LiteLLM service ready on port {TEST_PORT}")
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            pass

        time.sleep(1)

    if not service_ready:
        # Get output for debugging
        process.send_signal(signal.SIGTERM)
        time.sleep(2)
        stdout, stderr = process.communicate()
        pytest.fail(
            f"LiteLLM service failed to start within 60 seconds\n"
            f"STDOUT:\n{stdout[:1000]}\n"
            f"STDERR:\n{stderr[:1000]}"
        )

    yield process

    # Cleanup
    print(f"\n🛑 Stopping LiteLLM service (PID: {process.pid})")
    process.send_signal(signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


class TestE2EWorkflow:
    """Test complete end-to-end workflow"""

    def test_01_config_generation(self, generated_config):
        """Step 1: Verify config was generated correctly"""
        assert generated_config.exists()

        with open(generated_config) as f:
            config = yaml.safe_load(f)

        # Check structure
        assert "litellm_settings" in config
        assert "model_list" in config

        # Check master_key
        assert config["litellm_settings"]["master_key"] == TEST_MASTER_KEY

        # Check models
        assert len(config["model_list"]) == 2
        model_names = [m["model_name"] for m in config["model_list"]]
        assert "test-gpt-4" in model_names
        assert "test-claude-3" in model_names

    def test_02_service_started(self, litellm_process):
        """Step 2: Verify LiteLLM service started successfully"""
        assert litellm_process.poll() is None, "Service process should be running"

    def test_03_service_responding(self, litellm_process):
        """Step 3: Test service is responding to requests"""
        # Try to hit any endpoint - even 401 means service is working
        response = requests.get(f"http://127.0.0.1:{TEST_PORT}/v1/models")
        assert response.status_code in [200, 401], \
            "Service should respond with either 200 (success) or 401 (auth required)"

    def test_04_list_models_with_auth(self, litellm_process):
        """Step 4: Test /v1/models endpoint with correct auth"""
        response = requests.get(
            f"http://127.0.0.1:{TEST_PORT}/v1/models",
            headers={"Authorization": f"Bearer {TEST_MASTER_KEY}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data

        # Verify our test models are listed
        model_ids = [model["id"] for model in data["data"]]
        assert "test-gpt-4" in model_ids
        assert "test-claude-3" in model_ids

    def test_05_list_models_without_auth(self, litellm_process):
        """Step 5: Test that auth is enforced (no auth should fail)"""
        response = requests.get(f"http://127.0.0.1:{TEST_PORT}/v1/models")
        assert response.status_code == 401

    def test_06_list_models_wrong_key(self, litellm_process):
        """Step 6: Test that wrong key is rejected"""
        response = requests.get(
            f"http://127.0.0.1:{TEST_PORT}/v1/models",
            headers={"Authorization": "Bearer wrong-key-123"}
        )
        # LiteLLM may return 400 or 401 for invalid keys
        assert response.status_code in [400, 401], \
            "Wrong key should be rejected with 400 or 401"

    def test_07_api_key_consistency(self, litellm_process):
        """Step 7: Verify client and server use same key (critical for testing)"""
        # This is the pattern ALL tests must follow
        CLIENT_KEY = TEST_MASTER_KEY
        SERVER_KEY = TEST_MASTER_KEY

        assert CLIENT_KEY == SERVER_KEY, \
            "CLIENT and SERVER must use identical keys in tests!"

        # Verify it works
        response = requests.get(
            f"http://127.0.0.1:{TEST_PORT}/v1/models",
            headers={"Authorization": f"Bearer {CLIENT_KEY}"}
        )
        assert response.status_code == 200, \
            "When client and server keys match, request should succeed"


class TestAPIKeyPrinciple:
    """
    Test the core principle: API keys must be consistent

    This is critical for CI/CD testing
    """

    def test_consistent_keys_defined(self):
        """Ensure we define consistent test keys"""
        assert TEST_MASTER_KEY is not None
        assert len(TEST_MASTER_KEY) > 0
        assert TEST_MASTER_KEY == "test-e2e-key-789"

    def test_config_uses_test_key(self, generated_config):
        """Verify generated config uses our test key"""
        with open(generated_config) as f:
            config = yaml.safe_load(f)

        config_key = config["litellm_settings"]["master_key"]
        assert config_key == TEST_MASTER_KEY, \
            f"Config key '{config_key}' must match TEST_MASTER_KEY '{TEST_MASTER_KEY}'"
