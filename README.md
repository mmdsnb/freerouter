# FreeRouter

🛠️ **LiteLLM 配置管理工具** - 自动化多 Provider 配置生成

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 这是什么？

FreeRouter 是 [LiteLLM](https://github.com/BerriAI/litellm) 的**配置管理辅助工具**，帮你：

- 📋 **自动获取模型列表** - 从各个 Provider API 动态发现可用模型
- ⚙️ **生成 LiteLLM 配置** - 自动生成标准的 `config.yaml`
- 🎯 **简化配置流程** - 用简单的 `providers.yaml` 管理多个 Provider
- 🚀 **一键启动服务** - 获取配置 + 启动 LiteLLM 一步完成

**重要**:
- FreeRouter 本身不提供 AI 路由功能，所有 API 和路由能力由 [LiteLLM](https://github.com/BerriAI/litellm) 提供
- 建议先了解 [LiteLLM 文档](https://docs.litellm.ai/) 以理解配置和使用方式
- 如果你已经熟悉手写 LiteLLM 配置，可能不需要 FreeRouter

## 为什么需要这个？

**场景**: 你想用 LiteLLM 聚合多个 AI Provider，但是...

**问题**:
- 手动写 LiteLLM 配置文件太繁琐（几十上百个模型）
- 每个 Provider 的模型列表要自己查文档
- 模型更新了需要手动维护配置
- 多个 Provider 配置容易出错

**FreeRouter 的解决**:
```yaml
# 你只需要写简单的 providers.yaml
providers:
  - type: openrouter
    enabled: true
    api_key: ${OPENROUTER_API_KEY}

# FreeRouter 自动获取模型列表并生成完整的 config.yaml
# 然后启动 LiteLLM 服务
```

**本质**: FreeRouter 是配置生成器 + LiteLLM 启动器，真正的 AI 服务由 LiteLLM 提供。

## 快速开始

### 1. 安装

```bash
pip install freerouter
```

或从源码安装：
```bash
git clone https://github.com/mmdsnb/freerouter.git
cd freerouter
pip install -e .
```

### 2. 初始化配置

```bash
freerouter init
```

这会在当前目录创建 `config/` 文件夹和配置模板。

### 3. 配置你的服务

编辑 `.env` 添加 API Keys（如果需要）：
```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxx
```

编辑 `config/providers.yaml` 启用你想要的服务：
```yaml
providers:
  # OpenRouter - 支持文本和视觉模型
  - type: openrouter
    enabled: true
    api_key: ${OPENROUTER_API_KEY}

  # Ollama - 本地模型（免费）
  - type: ollama
    enabled: true
    api_base: http://localhost:11434
```

### 4. 获取模型并启动

```bash
# 获取模型列表
freerouter fetch

# 启动服务
freerouter start
```

或者直接启动（会自动查找配置）：
```bash
freerouter
```

服务将在 `http://localhost:4000` 启动。

### 5. 使用 API

FreeRouter 启动的是标准 LiteLLM 服务，所有 API 使用方式请参考 [LiteLLM 文档](https://docs.litellm.ai/)。

简单示例：

```bash
# 查看可用模型
curl http://localhost:4000/models

# 调用模型（OpenAI 兼容 API）
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-pro",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

Python 使用：
```python
import openai

client = openai.OpenAI(
    api_key="dummy",  # LiteLLM 默认不需要 key
    base_url="http://localhost:4000"
)

response = client.chat.completions.create(
    model="google/gemini-pro",
    messages=[{"role": "user", "content": "你好"}]
)
print(response.choices[0].message.content)
```

**更多用法**：
- 流式响应、函数调用、视觉模型等用法请查看 [LiteLLM 文档](https://docs.litellm.ai/)
- FreeRouter 只负责配置生成，API 功能全部由 LiteLLM 提供

## CLI 命令

FreeRouter 提供简洁的命令行工具：

```bash
freerouter          # 启动服务（默认命令）
freerouter init     # 初始化配置目录
freerouter fetch    # 获取模型列表并生成配置
freerouter start    # 启动服务
freerouter list     # 查看已配置的模型
freerouter --version # 查看版本
```

### 配置文件查找优先级

FreeRouter 按以下顺序查找配置：

1. **当前目录**: `./config/providers.yaml`
2. **用户配置**: `~/.config/freerouter/providers.yaml`

推荐在项目目录使用 `freerouter init` 创建本地配置。

## Docker 部署

如果你喜欢 Docker：

```bash
# 克隆仓库
git clone https://github.com/mmdsnb/freerouter.git
cd freerouter

# 配置
cp examples/providers.yaml.example config/providers.yaml
cp .env.example .env
# 编辑 .env 添加 API Keys

# 启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

## 支持的服务

| 服务 | 模型类型 | 免费额度 | 配置难度 | 推荐指数 |
|------|----------|----------|----------|----------|
| **OpenRouter** | 文本、视觉、多模态 | ✅ 有免费模型 | ⭐ 简单 | ⭐⭐⭐⭐⭐ |
| **Ollama** | 文本、视觉 | ✅ 完全免费 | ⭐⭐ 需本地安装 | ⭐⭐⭐⭐ |
| **ModelScope** | 文本 | ✅ 有免费额度 | ⭐ 简单 | ⭐⭐⭐ |
| **自定义服务** | 任意 | 视服务而定 | ⭐ 简单 | ⭐⭐⭐ |

### OpenRouter

最推荐！提供大量免费模型（文本、视觉、多模态）

```yaml
- type: openrouter
  enabled: true
  api_key: ${OPENROUTER_API_KEY}
```

支持的模型包括：
- 文本: GPT-3.5, Claude, Llama, Mistral 等
- 视觉: Gemini Pro Vision, GPT-4 Vision 等
- 多模态: Gemini Pro, Claude 3 等

注册地址: https://openrouter.ai/

### Ollama

本地运行，完全免费，隐私性好

```yaml
- type: ollama
  enabled: true
  api_base: http://localhost:11434
```

支持：
- 文本模型: Llama 2/3, Mistral, Qwen 等
- 视觉模型: LLaVA, BakLLaVA 等

安装: https://ollama.ai/

### ModelScope (魔搭)

国内服务，中文友好

```yaml
- type: modelscope
  enabled: true
  api_key: ${MODELSCOPE_API_KEY}
  models:
    - qwen-turbo
    - qwen-plus
    - qwen-vl-plus  # 视觉模型
```

### 自定义服务

支持任何 OpenAI 兼容的 API：

```yaml
- type: static
  enabled: true
  model_name: gpt-3.5-turbo
  provider: openai
  api_base: https://your-api.com/v1
  api_key: ${YOUR_KEY}
```

## 与 LiteLLM 的关系

FreeRouter 做的事情：
1. ✅ 从各个 Provider API 获取模型列表
2. ✅ 生成 LiteLLM 的 `config.yaml` 配置文件
3. ✅ 启动 LiteLLM 服务（可选）

LiteLLM 做的事情：
1. ✅ 提供统一的 OpenAI 兼容 API
2. ✅ 路由请求到不同 Provider
3. ✅ 负载均衡、故障切换、重试等
4. ✅ 所有高级功能（流式、函数调用、缓存等）

**简单理解**: FreeRouter 是"配置文件生成器"，LiteLLM 是"AI 服务代理"。

**如果你会手写配置**: 可以直接用 LiteLLM，不需要 FreeRouter。
**如果配置太多太繁琐**: FreeRouter 帮你自动生成，省时省力。

## 更新服务

当你修改配置后，重新获取模型并重启：

```bash
freerouter fetch  # 重新获取模型列表
freerouter start  # 重启服务（Ctrl+C 停止旧服务）
```

## 故障排查

### 服务启动失败

```bash
# 检查配置是否存在
freerouter list

# 重新生成配置
freerouter fetch
```

### 找不到配置文件

```bash
# 查看当前目录
ls config/providers.yaml

# 或在用户目录
ls ~/.config/freerouter/providers.yaml

# 重新初始化
freerouter init
```

### API 调用失败

```bash
# 查看可用模型
freerouter list

# 检查服务状态
curl http://localhost:4000/health
```

### 查看详细日志

```bash
# 前台运行查看日志
freerouter start
```

## 常见问题

### Q: FreeRouter 和 LiteLLM 什么关系？

A: FreeRouter 是 LiteLLM 的配置管理工具。它帮你自动生成 LiteLLM 配置文件，然后启动 LiteLLM 服务。所有 API 功能由 LiteLLM 提供。

### Q: 我需要了解 LiteLLM 吗？

A: **强烈建议**先看 [LiteLLM 文档](https://docs.litellm.ai/)，了解：
- LiteLLM 的配置格式
- 支持的 API 功能
- 路由和负载均衡策略

FreeRouter 只是帮你生成配置，具体怎么用还是要看 LiteLLM。

### Q: 我已经会写 LiteLLM 配置了，还需要 FreeRouter 吗？

A: 不一定。如果你的配置很简单，或者喜欢手动控制，直接用 LiteLLM 就好。FreeRouter 适合管理很多 Provider 和模型的场景。

### Q: 支持哪些模型？

A: 取决于：
1. 你配置的 Provider（OpenRouter、Ollama 等）
2. LiteLLM 支持的模型格式

查看 [LiteLLM 支持的 Provider](https://docs.litellm.ai/docs/providers)

### Q: 可以商用吗？

A: FreeRouter 本身是 MIT 协议，可以商用。但：
- 确保你使用的 AI 服务允许商用
- LiteLLM 的许可证请查看其官方说明

## 文档

- **README.md** (本文档) - 快速开始和使用指南
- **[QUICKSTART.md](QUICKSTART.md)** - 3 分钟快速上手
- **[CLAUDE.md](CLAUDE.md)** - 项目设计和开发指南
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - 如何贡献代码
- **[CHANGELOG.md](CHANGELOG.md)** - 版本更新记录

## 贡献

欢迎提交 Issue 和 Pull Request！

开发指南见 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 致谢

- [LiteLLM](https://github.com/BerriAI/litellm) - 核心路由引擎
- [OpenRouter](https://openrouter.ai/) - 优秀的 API 聚合服务
- [Ollama](https://ollama.ai/) - 本地 AI 模型运行工具

---

如有问题，欢迎提 [Issue](https://github.com/mmdsnb/freerouter/issues)
