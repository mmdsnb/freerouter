# FreeRouter

🚀 **免费 AI 模型路由服务** - 聚合多个免费 AI 服务，统一接口调用文本、视觉、多模态模型

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

## 这是什么？

FreeRouter 是一个 **AI 模型服务聚合器**，让你可以：

- 🌐 **聚合多种 AI 服务** - 支持文本、视觉、多模态模型（GPT、Claude、Gemini Vision 等）
- 🔄 **统一接口调用** - OpenAI 兼容 API，无需改代码
- ⚡ **自动负载均衡** - 请求自动分发到可用模型
- 🔁 **故障自动切换** - 一个服务挂了自动用其他的
- 📝 **配置即代码** - 一个 YAML 文件搞定所有配置

简单来说：**把多个免费的 AI 服务整合成一个稳定可靠的 API 接口。**

## 为什么需要这个？

**问题**:
- 免费 AI 服务不稳定，经常挂
- 每个服务 API 不一样，切换麻烦
- 想用多个服务但管理复杂
- 文本、视觉模型分散在不同平台

**解决**:
```python
# 不用这个 ❌
if openrouter_down:
    try ollama
    if ollama_down:
        try modelscope
        ...

# 用这个 ✅
response = client.chat.completions.create(
    model="google/gemini-pro-vision",  # FreeRouter 自动选择可用服务
    messages=[...]
)
```

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

### 5. 使用服务

```bash
# 文本模型
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-pro",
    "messages": [{"role": "user", "content": "你好"}]
  }'

# 视觉模型
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-pro-vision",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "这张图片里有什么？"},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
      ]
    }]
  }'
```

或者用 Python：
```python
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:4000"
)

# 文本模型
response = client.chat.completions.create(
    model="google/gemini-pro",
    messages=[{"role": "user", "content": "你好"}]
)

# 视觉模型
response = client.chat.completions.create(
    model="google/gemini-pro-vision",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "描述这张图片"},
            {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
        ]
    }]
)

print(response.choices[0].message.content)
```

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

## 常见使用场景

### 场景 1: 文本+视觉混合使用

配置多个支持不同能力的服务：

```yaml
providers:
  - type: openrouter  # 文本和视觉
    enabled: true

  - type: ollama      # 本地文本模型
    enabled: true
```

### 场景 2: 提高稳定性

配置多个服务作为备份：

```yaml
providers:
  - type: openrouter
    enabled: true

  - type: modelscope
    enabled: true
```

### 场景 3: 本地 + 云端

本地 Ollama 跑小任务（快、免费），复杂任务调云端：

```yaml
providers:
  - type: ollama
    enabled: true

  - type: openrouter
    enabled: true
```

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

### Q: 完全免费吗？

A: FreeRouter 本身免费开源。但使用的 AI 服务可能需要 API Key 或有免费额度限制。推荐 OpenRouter（有免费模型）和 Ollama（完全免费）。

### Q: 支持哪些模型？

A: 取决于你配置的 Provider。OpenRouter 支持 100+ 文本和视觉模型，Ollama 支持所有开源模型。

### Q: 支持视觉模型吗？

A: 是的！支持 Gemini Pro Vision、GPT-4 Vision、LLaVA 等视觉和多模态模型。

### Q: 性能怎么样？

A: FreeRouter 只是代理层，性能主要取决于底层服务。增加的延迟 < 50ms。

### Q: 可以商用吗？

A: FreeRouter 本身是 MIT 协议，可以商用。但请确保你使用的 AI 服务允许商用。

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
