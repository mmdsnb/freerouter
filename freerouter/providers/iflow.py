"""
iFlow Provider

iFlow 是一个提供免费 AI 模型的服务
API 文档: https://iflow.cn/
"""

import requests
from typing import List, Dict, Any
from .base import BaseProvider


class IFlowProvider(BaseProvider):
    """iFlow Provider - 免费模型服务"""

    def __init__(self, api_key: str = None, **kwargs):
        """
        初始化 iFlow Provider

        Args:
            api_key: iFlow API Key (从 https://iflow.cn/ 获取)
        """
        super().__init__(**kwargs)
        self.api_key = api_key or ""
        self.api_base = "https://apis.iflow.cn/v1"

    @property
    def provider_name(self) -> str:
        return "iflow"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        从 iFlow API 获取模型列表

        Returns:
            模型列表，每个模型包含 id 字段
        """
        url = f"{self.api_base}/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "data" in data:
                models = data["data"]
                self.logger.info(f"Fetched {len(models)} models from iFlow")
                return models
            else:
                self.logger.warning("No 'data' field in iFlow response")
                return []

        except Exception as e:
            self.logger.error(f"Failed to fetch models from iFlow: {e}")
            return []

    def format_service(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 iFlow 模型格式化为 LiteLLM 配置

        iFlow 使用 OpenAI 兼容格式，所以使用 openai/ 前缀

        Args:
            model: 模型信息字典

        Returns:
            LiteLLM service 配置
        """
        model_id = model.get("id", "unknown")

        return {
            "model_name": model_id,
            "litellm_params": {
                "model": f"openai/{model_id}",
                "api_base": self.api_base,
                "api_key": self.api_key,
            }
        }
