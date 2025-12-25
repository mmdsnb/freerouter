"""
Tests for Provider implementations
"""

import pytest
from freerouter.providers.base import BaseProvider
from freerouter.providers.static import StaticProvider


class TestStaticProvider:
    """Test Static Provider"""

    def test_create_static_provider(self):
        """Test creating a static provider"""
        provider = StaticProvider(
            model_name="test-model",
            provider="openai",
            api_base="https://api.test.com",
            api_key="test-key"
        )

        assert provider.provider_name == "openai"
        assert provider.model_name == "test-model"

    def test_fetch_models(self):
        """Test fetching models returns single model"""
        provider = StaticProvider(
            model_name="test-model",
            provider="openai",
            api_base="https://api.test.com"
        )

        models = provider.fetch_models()
        assert len(models) == 1
        assert models[0]["id"] == "test-model"

    def test_format_service(self):
        """Test service formatting"""
        provider = StaticProvider(
            model_name="test-model",
            provider="openai",
            api_base="https://api.test.com",
            api_key="test-key"
        )

        service = provider.format_service({"id": "test-model"})
        assert service["model_name"] == "test-model"
        assert service["litellm_params"]["model"] == "openai/test-model"
        assert service["litellm_params"]["api_key"] == "test-key"


# TODO: Add more tests for other providers
# - TestOpenRouterProvider (needs mocking)
# - TestOllamaProvider (needs mocking)
# - TestModelScopeProvider
