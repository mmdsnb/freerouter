"""
Tests for iFlow Provider
"""

import pytest
from unittest.mock import Mock, patch
from freerouter.providers.iflow import IFlowProvider


class TestIFlowProvider:
    """Test iFlow Provider"""

    def test_create_provider(self):
        """Test creating iFlow provider"""
        provider = IFlowProvider(api_key="test-key")

        assert provider.provider_name == "iflow"
        assert provider.api_key == "test-key"
        assert provider.api_base == "https://apis.iflow.cn/v1"

    def test_create_provider_without_key(self):
        """Test creating provider without API key"""
        provider = IFlowProvider()

        assert provider.provider_name == "iflow"
        assert provider.api_key == ""

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_success(self, mock_get):
        """Test fetching models successfully"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {"id": "qwen3-max", "object": "model", "created": 1759056466, "owned_by": "iflow"},
                {"id": "glm-4.6", "object": "model", "created": 1759993272, "owned_by": "iflow"},
                {"id": "deepseek-v3", "object": "model", "created": 1755178234, "owned_by": "iflow"},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = IFlowProvider(api_key="test-key")
        models = provider.fetch_models()

        assert len(models) == 3
        assert models[0]["id"] == "qwen3-max"
        assert models[1]["id"] == "glm-4.6"
        assert models[2]["id"] == "deepseek-v3"

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://apis.iflow.cn/v1/models" in call_args[0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_api_error(self, mock_get):
        """Test handling API errors"""
        mock_get.side_effect = Exception("API Error")

        provider = IFlowProvider(api_key="test-key")
        models = provider.fetch_models()

        assert models == []

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_invalid_response(self, mock_get):
        """Test handling invalid response format"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid key"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = IFlowProvider(api_key="test-key")
        models = provider.fetch_models()

        assert models == []

    def test_format_service(self):
        """Test formatting model as LiteLLM service"""
        provider = IFlowProvider(api_key="test-key-123")

        model = {
            "id": "qwen3-max",
            "object": "model",
            "created": 1759056466,
            "owned_by": "iflow"
        }

        service = provider.format_service(model)

        assert service["model_name"] == "qwen3-max"
        assert service["litellm_params"]["model"] == "openai/qwen3-max"
        assert service["litellm_params"]["api_base"] == "https://apis.iflow.cn/v1"
        assert service["litellm_params"]["api_key"] == "test-key-123"

    def test_format_service_with_unknown_model(self):
        """Test formatting model with missing id"""
        provider = IFlowProvider(api_key="test-key")

        model = {"object": "model"}  # No id field

        service = provider.format_service(model)

        assert service["model_name"] == "unknown"
        assert service["litellm_params"]["model"] == "openai/unknown"
