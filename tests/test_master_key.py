"""
Tests for master_key functionality
"""

import os
import pytest
import tempfile
import yaml
import requests
from pathlib import Path
from freerouter.core.fetcher import FreeRouterFetcher


class TestMasterKeyGeneration:
    """Test master_key generation and management"""

    def test_env_master_key_used(self, tmp_path):
        """Test that LITELLM_MASTER_KEY env var is used when set"""
        config_path = tmp_path / "config.yaml"
        env_key = "sk-env-test-key-12345"

        # Set environment variable
        os.environ["LITELLM_MASTER_KEY"] = env_key

        try:
            fetcher = FreeRouterFetcher(config_path=str(config_path))
            key = fetcher.get_or_create_master_key()

            assert key == env_key, "Should use LITELLM_MASTER_KEY from environment"

        finally:
            # Cleanup
            del os.environ["LITELLM_MASTER_KEY"]

    def test_auto_generated_master_key(self, tmp_path):
        """Test auto-generation of ephemeral master_key when not provided"""
        config_path = tmp_path / "config.yaml"

        # Ensure no env var is set
        if "LITELLM_MASTER_KEY" in os.environ:
            del os.environ["LITELLM_MASTER_KEY"]

        fetcher = FreeRouterFetcher(config_path=str(config_path))
        key = fetcher.get_or_create_master_key()

        # Verify key format
        assert key.startswith("sk-"), "Generated key should start with 'sk-'"
        assert len(key) > 40, "Generated key should be long enough"

    def test_ephemeral_keys_are_different(self, tmp_path):
        """Test that each generation creates a different ephemeral key"""
        config_path = tmp_path / "config.yaml"

        # Ensure no env var
        if "LITELLM_MASTER_KEY" in os.environ:
            del os.environ["LITELLM_MASTER_KEY"]

        fetcher1 = FreeRouterFetcher(config_path=str(config_path))
        key1 = fetcher1.get_or_create_master_key()

        fetcher2 = FreeRouterFetcher(config_path=str(config_path))
        key2 = fetcher2.get_or_create_master_key()

        assert key1 != key2, "Ephemeral keys should be different on each generation"

    def test_master_key_in_config(self, tmp_path):
        """Test that master_key is included in generated config"""
        config_path = tmp_path / "config.yaml"

        # Set env var
        test_key = "sk-test-config-key-99999"
        os.environ["LITELLM_MASTER_KEY"] = test_key

        try:
            fetcher = FreeRouterFetcher(config_path=str(config_path))

            # Add a dummy provider to avoid empty config
            from freerouter.providers.static import StaticProvider
            static_provider = StaticProvider(
                model_name="test-model",
                provider="test",
                api_base="http://localhost:1234",
                api_key="test-key"
            )
            fetcher.add_provider(static_provider)

            # Generate config
            success = fetcher.generate_config()
            assert success, "Config generation should succeed"

            # Read and verify config
            with open(config_path) as f:
                config = yaml.safe_load(f)

            assert "litellm_settings" in config
            assert "master_key" in config["litellm_settings"]
            assert config["litellm_settings"]["master_key"] == test_key

        finally:
            del os.environ["LITELLM_MASTER_KEY"]


@pytest.mark.integration
class TestMasterKeyAuthentication:
    """Test API authentication with master_key (requires litellm running)"""

    @pytest.fixture
    def litellm_server(self, tmp_path):
        """Start a LiteLLM server with master_key for testing"""
        import subprocess
        import time

        config_path = tmp_path / "config.yaml"
        test_key = "sk-test-auth-key-11111"

        # Create minimal config with master_key
        config = {
            "model_list": [
                {
                    "model_name": "test-model",
                    "litellm_params": {
                        "model": "openai/gpt-3.5-turbo",
                        "api_key": "fake-key"
                    }
                }
            ],
            "litellm_settings": {
                "master_key": test_key,
                "drop_params": True
            }
        }

        with open(config_path, 'w') as f:
            yaml.dump(config, f)

        # Try to start LiteLLM server
        port = 4001
        try:
            process = subprocess.Popen(
                ["litellm", "--config", str(config_path), "--port", str(port), "--host", "127.0.0.1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
        except FileNotFoundError:
            pytest.skip("litellm not installed")

        # Wait for server to start
        max_wait = 15
        server_started = False
        for _ in range(max_wait):
            try:
                response = requests.get(f"http://127.0.0.1:{port}/health", timeout=1)
                if response.status_code == 200:
                    server_started = True
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        if not server_started:
            # Get stderr for debugging
            stderr = process.stderr.read().decode() if process.stderr else ""
            process.terminate()
            process.wait()
            pytest.skip(f"LiteLLM server failed to start: {stderr[:200]}")

        yield {"port": port, "key": test_key}

        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    def test_valid_master_key_access(self, litellm_server):
        """Test that valid master_key allows API access"""
        port = litellm_server["port"]
        key = litellm_server["key"]

        headers = {"Authorization": f"Bearer {key}"}
        response = requests.get(
            f"http://127.0.0.1:{port}/v1/models",
            headers=headers,
            timeout=5
        )

        assert response.status_code == 200, "Valid key should grant access"
        data = response.json()
        assert "data" in data, "Response should contain model list"

    def test_invalid_master_key_rejection(self, litellm_server):
        """Test that invalid master_key is rejected for chat completions"""
        port = litellm_server["port"]
        wrong_key = "sk-wrong-key-xxxxxx"

        headers = {
            "Authorization": f"Bearer {wrong_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "test"}]
        }

        response = requests.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=5
        )

        # LiteLLM should reject invalid keys with 401/403
        # Note: /v1/models endpoint doesn't require auth by design
        assert response.status_code in [401, 403], \
            f"Wrong key should be rejected, got {response.status_code}: {response.text[:100]}"

    def test_missing_master_key_rejection(self, litellm_server):
        """Test that missing master_key is rejected for chat completions"""
        port = litellm_server["port"]

        headers = {"Content-Type": "application/json"}
        data = {
            "model": "test-model",
            "messages": [{"role": "user", "content": "test"}]
        }

        # No Authorization header
        response = requests.post(
            f"http://127.0.0.1:{port}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=5
        )

        assert response.status_code in [401, 403], \
            f"Missing key should be rejected, got {response.status_code}: {response.text[:100]}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
