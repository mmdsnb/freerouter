"""
ModelScope Provider

ModelScope 是中国的模型社区平台，提供 API-Inference 服务
API 文档: https://help.aliyun.com/zh/model-studio/getting-started/
免费额度: 每天 2000 次调用，每个模型上限 500 次
"""

import requests
from typing import List, Dict, Any
from .base import BaseProvider


class ModelScopeProvider(BaseProvider):
    """ModelScope Provider - 魔搭社区免费推理服务"""

    def __init__(self, api_key: str = None, **kwargs):
        """
        初始化 ModelScope Provider

        Args:
            api_key: ModelScope API Key (从 https://modelscope.cn/ 获取)
        """
        super().__init__(**kwargs)
        self.api_key = api_key or ""
        self.api_base = "https://api-inference.modelscope.cn/v1"

    @property
    def provider_name(self) -> str:
        return "modelscope"

    def fetch_models(self) -> List[Dict[str, Any]]:
        """
        从 ModelScope API 获取模型列表

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
                self.logger.info(f"Fetched {len(models)} models from ModelScope")
                return models
            else:
                self.logger.warning("No 'data' field in ModelScope response")
                return []

        except Exception as e:
            self.logger.error(f"Failed to fetch models from ModelScope: {e}")
            return []

    def format_service(self, model: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 ModelScope 模型格式化为 LiteLLM 配置

        ModelScope 使用 OpenAI 兼容格式，所以使用 openai/ 前缀

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
