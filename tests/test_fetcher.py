"""
Tests for FreeRouterFetcher
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from freerouter.core.fetcher import FreeRouterFetcher
from freerouter.providers.static import StaticProvider


class TestFreeRouterFetcher:
    """Test FreeRouterFetcher"""

    def test_create_fetcher(self):
        """Test creating a fetcher"""
        fetcher = FreeRouterFetcher()
        assert fetcher.providers == []

    def test_add_provider(self):
        """Test adding a provider"""
        fetcher = FreeRouterFetcher()
        provider = StaticProvider(
            model_name="test",
            provider="openai",
            api_base="https://api.test.com"
        )

        fetcher.add_provider(provider)
        assert len(fetcher.providers) == 1

    def test_fetch_all(self):
        """Test fetching from all providers"""
        fetcher = FreeRouterFetcher()

        # Add two providers
        provider1 = StaticProvider(
            model_name="model-1",
            provider="openai",
            api_base="https://api.test.com"
        )
        provider2 = StaticProvider(
            model_name="model-2",
            provider="anthropic",
            api_base="https://api.test2.com"
        )

        fetcher.add_provider(provider1)
        fetcher.add_provider(provider2)

        services = fetcher.fetch_all()
        assert len(services) == 2

    def test_generate_config(self):
        """Test generating config file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            fetcher = FreeRouterFetcher(config_path=str(config_path))
            provider = StaticProvider(
                model_name="test",
                provider="openai",
                api_base="https://api.test.com"
            )
            fetcher.add_provider(provider)

            result = fetcher.generate_config()
            assert result is True
            assert config_path.exists()

            # Check config content
            with open(config_path) as f:
                config = yaml.safe_load(f)

            assert "model_list" in config
            assert len(config["model_list"]) == 1
            assert "litellm_settings" in config
            assert "router_settings" in config


# TODO: Add more tests
# - test_load_providers_from_yaml
# - test_environment_variable_resolution
