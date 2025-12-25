# FreeRouter

🛠️ **LiteLLM 配置管理工具** - 自动化多 Provider 配置生成

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

中文文档 | [English](README.md)

## 这是什么？

FreeRouter 是 [LiteLLM](https://github.com/BerriAI/litellm) 的**配置管理辅助工具**。

**核心功能**：
- 📋 自动从各 Provider API 获取模型列表
- ⚙️ 生成 LiteLLM 的 `config.yaml` 配置文件
- 🚀 一键启动 LiteLLM 服务

**重要**：
- FreeRouter 不提供 AI 服务，所有 API 和路由由 [LiteLLM](https://github.com/BerriAI/litellm) 提供
- 建议先了解 [LiteLLM 文档](https://docs.litellm.ai/)
- 如果你熟悉手写配置，可能不需要 FreeRouter

## 支持的 Provider

| Provider | 类型 | 免费 |
|----------|------|------|
| **OpenRouter** | 文本、视觉、多模态 | ✅ 部分免费 |
| **iFlow** | 文本 | ✅ 全部免费 |
| **Ollama** | 文本、视觉 | ✅ 本地免费 |
| **ModelScope** | 文本 | ✅ 有免费额度 |
| **自定义** | 任意 | 视服务而定 |

**免费 Provider**：
- **OpenRouter** (https://openrouter.ai/) - 30+ 免费模型（GPT-3.5、Gemini、Llama 等）
- **iFlow** (https://iflow.cn/) - 中文免费模型（Qwen、GLM、DeepSeek 等）

## 快速开始

### 1. 安装

```bash
pip install freerouter
```

或从源码：
```bash
git clone https://github.com/mmdsnb/freerouter.git
cd freerouter
pip install -e .
```

### 2. 初始化配置

```bash
freerouter init
```

### 3. 配置 Provider

编辑 `.env` 添加 API Key：
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
IFLOW_API_KEY=sk-xxxxx
```

编辑 `config/providers.yaml` 启用服务：
```yaml
providers:
  # OpenRouter - 免费模型
  - type: openrouter
    enabled: true
    api_key: ${OPENROUTER_API_KEY}

  # iFlow - 中文免费模型
  - type: iflow
    enabled: true
    api_key: ${IFLOW_API_KEY}

  # Ollama - 本地模型
  - type: ollama
    enabled: true
    api_base: http://localhost:11434

  # ModelScope - 中文模型（每天 2000 次免费）
  - type: modelscope
    enabled: false
    api_key: ${MODELSCOPE_API_KEY}

  # 自定义服务
  - type: static
    enabled: false
    model_name: gpt-3.5-turbo
    provider: openai
    api_base: https://your-api.com/v1
    api_key: ${YOUR_KEY}
```

### 4. 启动服务

```bash
# 获取模型列表并启动服务
freerouter

# 或分步执行
freerouter fetch   # 获取模型列表
freerouter start   # 启动服务
```

服务将在 `http://localhost:4000` 启动。

### 5. 使用 API

所有 API 使用方式请参考 [LiteLLM 文档](https://docs.litellm.ai/)。

```bash
# 查看可用模型
curl http://localhost:4000/v1/models

# 调用模型（OpenAI 兼容 API）
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer sk-1234" \
  -d '{
    "model": "google/gemini-pro",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## CLI 命令

```bash
freerouter              # 启动服务（默认命令，自动 fetch + start）
freerouter init         # 初始化配置目录
freerouter fetch        # 获取模型列表并生成配置
freerouter start        # 启动 LiteLLM 服务
freerouter list         # 查看已配置的模型
freerouter --version    # 查看版本
freerouter --help       # 查看帮助
```

**配置文件查找顺序**：
1. `./config/providers.yaml` (当前目录)
2. `~/.config/freerouter/providers.yaml` (用户配置)

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 链接

- [GitHub](https://github.com/mmdsnb/freerouter)
- [LiteLLM](https://github.com/BerriAI/litellm)
- [OpenRouter](https://openrouter.ai/)
- [iFlow](https://iflow.cn/)
- [Ollama](https://ollama.ai/)

---

如有问题，欢迎提 [Issue](https://github.com/mmdsnb/freerouter/issues)
