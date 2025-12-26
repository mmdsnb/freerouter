"""
Tests for FreeRouterFetcher
"""

import pytest
import tempfile
import yaml
import time
from pathlib import Path
from unittest.mock import Mock, patch

from freerouter.core.fetcher import FreeRouterFetcher
from freerouter.providers.static import StaticProvider
from freerouter.providers.base import BaseProvider


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

    def test_parallel_fetch(self):
        """Test that providers are fetched in parallel"""
        
        class SlowProvider(BaseProvider):
            """Mock provider that simulates slow API call"""
            
            def __init__(self, name: str, delay: float = 0.5):
                super().__init__()
                self._name = name
                self._delay = delay
            
            @property
            def provider_name(self) -> str:
                return self._name
            
            def fetch_models(self):
                # Simulate slow API call
                time.sleep(self._delay)
                return [{"id": f"{self._name}-model"}]
        
        fetcher = FreeRouterFetcher()
        
        # Add 3 providers with 0.5s delay each
        for i in range(3):
            provider = SlowProvider(f"provider-{i}", delay=0.5)
            fetcher.add_provider(provider)
        
        # Measure time for parallel fetch
        start_time = time.time()
        services = fetcher.fetch_all()
        elapsed_time = time.time() - start_time
        
        # Should complete in ~0.5s (parallel) not ~1.5s (sequential)
        # Allow some overhead, so check < 1.0s
        assert elapsed_time < 1.0, f"Parallel fetch took {elapsed_time}s, expected < 1.0s"
        assert len(services) == 3
    
    def test_parallel_fetch_with_error(self):
        """Test that one provider error doesn't block others"""
        
        class ErrorProvider(BaseProvider):
            """Mock provider that raises an error"""
            
            @property
            def provider_name(self) -> str:
                return "error-provider"
            
            def fetch_models(self):
                raise Exception("Simulated API error")
        
        fetcher = FreeRouterFetcher()
        
        # Add one error provider and one good provider
        fetcher.add_provider(ErrorProvider())
        fetcher.add_provider(StaticProvider(
            model_name="good-model",
            provider="openai",
            api_base="https://api.test.com"
        ))
        
        # Should still get services from good provider
        services = fetcher.fetch_all()
        assert len(services) == 1
        assert services[0]["model_name"] == "good-model"


# TODO: Add more tests
# - test_load_providers_from_yaml
# - test_environment_variable_resolution
