"""
ModelScope Provider - static model list (no API)
"""

from typing import List, Dict, Any
from .base import BaseProvider


class ModelScopeProvider(BaseProvider):
    """
    ModelScope provider with static model list
    (ModelScope doesn't have a public models API)
    """

    # Static list of popular ModelScope models
    MODELS = [
        "qwen-turbo",
        "qwen-plus",
        "qwen-max",
        "qwen-vl-plus",
        "qwen-vl-max",
    ]

    def __init__(self, api_key: str = None, models: List[str] = None, **kwargs):
        super().__init__(
            api_key=api_key or "dummy",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            **kwargs
        )
        self.models = models or self.MODELS

    @property
    def provider_name(self) -> str:
        return "openai"  # ModelScope uses OpenAI-compatible API

    def fetch_models(self) -> List[Dict[str, Any]]:
        """Return static model list"""
        return [{"id": model_id} for model_id in self.models]

    def format_service(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """Format for ModelScope/DashScope API"""
        model_id = model.get('id')
        return {
            "model_name": model_id,
            "litellm_params": {
                "model": f"openai/{model_id}",  # Use openai provider
                "api_base": self.api_base,
                "api_key": self.api_key
            }
        }
