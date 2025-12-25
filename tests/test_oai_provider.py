"""
Tests for OAI (OpenAI-Compatible) Provider
"""

import pytest
from unittest.mock import Mock, patch
from freerouter.providers.oai import OAIProvider


class TestOAIProvider:
    """Test OAI Provider"""

    def test_create_provider(self):
        """Test creating OAI provider"""
        provider = OAIProvider(
            name="myservice",
            api_base="https://api.example.com/v1",
            api_key="test-key"
        )

        assert provider.provider_name == "myservice"
        assert provider.name == "myservice"
        assert provider.api_key == "test-key"
        assert provider.api_base == "https://api.example.com/v1"

    def test_create_provider_without_key(self):
        """Test creating provider without API key"""
        provider = OAIProvider(
            name="myservice",
            api_base="https://api.example.com/v1"
        )

        assert provider.provider_name == "myservice"
        assert provider.api_key == ""

    def test_api_base_trailing_slash(self):
        """Test that trailing slash is removed from api_base"""
        provider = OAIProvider(
            name="test",
            api_base="https://api.example.com/v1/",
            api_key="test"
        )

        assert provider.api_base == "https://api.example.com/v1"

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_success(self, mock_get):
        """Test fetching models successfully"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {"id": "gpt-4", "object": "model", "created": 1677610602, "owned_by": "openai"},
                {"id": "claude-sonnet", "object": "model", "created": 1677610602, "owned_by": "anthropic"},
                {"id": "gemini-pro", "object": "model", "created": 1677610602, "owned_by": "google"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = OAIProvider(
            name="testservice",
            api_base="https://api.test.com/v1",
            api_key="test-key"
        )
        models = provider.fetch_models()

        assert len(models) == 3
        assert models[0]["id"] == "gpt-4"
        assert models[1]["id"] == "claude-sonnet"
        assert models[2]["id"] == "gemini-pro"

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api.test.com/v1/models" in call_args[0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_without_auth(self, mock_get):
        """Test fetching models without API key"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "model-1", "object": "model"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = OAIProvider(
            name="public-api",
            api_base="https://api.example.com/v1"
        )
        models = provider.fetch_models()

        assert len(models) == 1

        # Verify no Authorization header when no API key
        call_args = mock_get.call_args
        assert call_args[1]["headers"] == {}

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_api_error(self, mock_get):
        """Test handling API errors"""
        mock_get.side_effect = Exception("API Error")

        provider = OAIProvider(
            name="test",
            api_base="https://api.example.com/v1",
            api_key="test-key"
        )
        models = provider.fetch_models()

        assert models == []

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_invalid_response(self, mock_get):
        """Test handling invalid response format"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid key"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = OAIProvider(
            name="test",
            api_base="https://api.example.com/v1",
            api_key="test-key"
        )
        models = provider.fetch_models()

        assert models == []

    def test_format_service(self):
        """Test formatting model as LiteLLM service"""
        provider = OAIProvider(
            name="testservice",
            api_base="https://api.test.com/v1",
            api_key="test-key-123"
        )

        model = {
            "id": "claude-sonnet",
            "object": "model",
            "created": 1677610602,
            "owned_by": "anthropic"
        }

        service = provider.format_service(model)

        assert service["model_name"] == "claude-sonnet"
        assert service["litellm_params"]["model"] == "openai/claude-sonnet"
        assert service["litellm_params"]["api_base"] == "https://api.test.com/v1"
        assert service["litellm_params"]["api_key"] == "test-key-123"

    def test_format_service_with_unknown_model(self):
        """Test formatting model with missing id"""
        provider = OAIProvider(
            name="test",
            api_base="https://api.example.com/v1",
            api_key="test-key"
        )

        model = {"object": "model"}  # No id field

        service = provider.format_service(model)

        assert service["model_name"] == "unknown"
        assert service["litellm_params"]["model"] == "openai/unknown"

    def test_custom_provider_name(self):
        """Test that provider name is customizable"""
        provider1 = OAIProvider(
            name="service_a",
            api_base="https://a.com/v1",
            api_key="key-a"
        )

        provider2 = OAIProvider(
            name="service_b",
            api_base="https://b.com/v1",
            api_key="key-b"
        )

        assert provider1.provider_name == "service_a"
        assert provider2.provider_name == "service_b"
