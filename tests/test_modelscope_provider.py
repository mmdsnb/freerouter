"""
Tests for ModelScope Provider
"""

import pytest
from unittest.mock import Mock, patch
from freerouter.providers.modelscope import ModelScopeProvider


class TestModelScopeProvider:
    """Test ModelScope Provider"""

    def test_create_provider(self):
        """Test creating ModelScope provider"""
        provider = ModelScopeProvider(api_key="test-key")

        assert provider.provider_name == "modelscope"
        assert provider.api_key == "test-key"
        assert provider.api_base == "https://api-inference.modelscope.cn/v1"

    def test_create_provider_without_key(self):
        """Test creating provider without API key"""
        provider = ModelScopeProvider()

        assert provider.provider_name == "modelscope"
        assert provider.api_key == ""

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_success(self, mock_get):
        """Test fetching models successfully"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            "object": "list",
            "data": [
                {"id": "Qwen/Qwen2.5-7B-Instruct", "object": "", "owned_by": "system", "created": 1737907200},
                {"id": "deepseek-ai/DeepSeek-V3.2", "object": "", "owned_by": "system", "created": 1764927217},
                {"id": "Qwen/Qwen3-235B-A22B", "object": "", "owned_by": "system", "created": 1745856000},
            ]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = ModelScopeProvider(api_key="test-key")
        models = provider.fetch_models()

        assert len(models) == 3
        assert models[0]["id"] == "Qwen/Qwen2.5-7B-Instruct"
        assert models[1]["id"] == "deepseek-ai/DeepSeek-V3.2"
        assert models[2]["id"] == "Qwen/Qwen3-235B-A22B"

        # Verify API was called correctly
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert "https://api-inference.modelscope.cn/v1/models" in call_args[0]
        assert call_args[1]["headers"]["Authorization"] == "Bearer test-key"

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_api_error(self, mock_get):
        """Test handling API errors"""
        mock_get.side_effect = Exception("API Error")

        provider = ModelScopeProvider(api_key="test-key")
        models = provider.fetch_models()

        assert models == []

    @patch('freerouter.providers.oai.requests.get')
    def test_fetch_models_invalid_response(self, mock_get):
        """Test handling invalid response format"""
        mock_response = Mock()
        mock_response.json.return_value = {"error": "Invalid key"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        provider = ModelScopeProvider(api_key="test-key")
        models = provider.fetch_models()

        assert models == []

    def test_format_service(self):
        """Test formatting model as LiteLLM service"""
        provider = ModelScopeProvider(api_key="test-key-123")

        model = {
            "id": "Qwen/Qwen2.5-7B-Instruct",
            "object": "",
            "created": 1737907200,
            "owned_by": "system"
        }

        service = provider.format_service(model)

        assert service["model_name"] == "Qwen/Qwen2.5-7B-Instruct"
        assert service["litellm_params"]["model"] == "openai/Qwen/Qwen2.5-7B-Instruct"
        assert service["litellm_params"]["api_base"] == "https://api-inference.modelscope.cn/v1"
        assert service["litellm_params"]["api_key"] == "test-key-123"

    def test_format_service_with_unknown_model(self):
        """Test formatting model with missing id"""
        provider = ModelScopeProvider(api_key="test-key")

        model = {"object": ""}  # No id field

        service = provider.format_service(model)

        assert service["model_name"] == "unknown"
        assert service["litellm_params"]["model"] == "openai/unknown"
