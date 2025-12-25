# FreeRouter 快速开始指南

3 分钟上手 FreeRouter！

## 安装

```bash
pip install freerouter
```

## 使用

### 方式 1: 零配置快速启动

如果你已经有 OpenRouter API Key：

```bash
# 设置环境变量
export OPENROUTER_API_KEY=sk-or-v1-xxxxx

# 初始化
freerouter init

# 获取模型
freerouter fetch

# 启动
freerouter
```

访问 http://localhost:4000 就可以使用了！

### 方式 2: 完整配置

```bash
# 1. 初始化配置目录
freerouter init

# 2. 编辑配置
nano config/providers.yaml

# 添加你的服务:
# providers:
#   - type: openrouter
#     enabled: true
#     api_key: ${OPENROUTER_API_KEY}

# 3. 设置环境变量
nano .env
# OPENROUTER_API_KEY=sk-or-v1-xxxxx

# 4. 获取模型列表
freerouter fetch

# 5. 查看可用模型
freerouter list

# 6. 启动服务
freerouter start
```

## 使用示例

### cURL

```bash
curl http://localhost:4000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-pro",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Python

```python
import openai

client = openai.OpenAI(
    api_key="dummy",
    base_url="http://localhost:4000"
)

response = client.chat.completions.create(
    model="google/gemini-pro",
    messages=[{"role": "user", "content": "Hello!"}]
)

print(response.choices[0].message.content)
```

## 常用命令

```bash
freerouter          # 启动服务
freerouter init     # 初始化配置
freerouter fetch    # 获取模型列表
freerouter list     # 查看已配置模型
freerouter --help   # 查看帮助
```

## 配置位置

FreeRouter 会按顺序查找配置：

1. `./config/providers.yaml` (当前目录)
2. `~/.config/freerouter/providers.yaml` (用户目录)

推荐在项目目录使用本地配置。

## 下一步

- 阅读完整文档: [README.md](README.md)
- 了解设计原理: [CLAUDE.md](CLAUDE.md)
- 添加更多服务: 编辑 `config/providers.yaml`

就这么简单！
