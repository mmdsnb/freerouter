# FreeRouter - Project Standards and Design Document

> **CRITICAL**: This document records project design principles, architectural decisions, and code standards. All modifications MUST follow this document. This document is shared by all Claude Code instances working on this project to maintain consistency.

## Collaboration Guidelines for Claude Code

### Git Workflow
1. **Automatic Commits**: Create commits automatically when you complete meaningful work (feature additions, bug fixes, refactoring)
   - Use descriptive commit messages following the format: `<type>(<scope>): <subject>`
   - Examples: `feat(cli): add interactive init command`, `fix(config): handle missing file error`

2. **Push Policy**:
   - **NEVER push automatically** - only push when user explicitly requests it
   - User will say "push" or "git push" when they want to publish changes

3. **Code Quality**:
   - **Continuously review code for refactoring opportunities**
   - Prevent "spaghetti code" from accumulating
   - When you see code smells (duplication, complexity, unclear naming), proactively suggest or implement improvements
   - Balance refactoring with feature development - don't over-engineer

4. **Documentation Sync**:
   - Update CLAUDE.md whenever you make architectural decisions or add new patterns
   - Keep it as the source of truth for all Claude Code instances
   - Document "why" decisions were made, not just "what" was done

### Code Review Checklist (Self-Review Before Commit)
- [ ] Code follows KISS and Occam's Razor principles
- [ ] No code duplication (DRY principle)
- [ ] Functions/classes have single responsibility
- [ ] Clear, descriptive naming (no abbreviations unless standard)
- [ ] Error handling is appropriate
- [ ] No hardcoded values (use config/env vars)
- [ ] Internationalization (English for user-facing messages)
- [ ] Comments only where logic is non-obvious

## Core Design Principles

### 1. KISS (Keep It Simple, Stupid)
- 代码简洁明了，避免过度设计
- 每个模块只做一件事
- 优先使用清晰的解决方案，而非"聪明"的技巧

### 2. 奥卡姆剃刀 (Occam's Razor)
- 如无必要，勿增实体
- 最简单的解决方案往往是最好的
- 避免不必要的抽象和复杂性

### 3. 设计模式
- **策略模式**: Provider 体系 - 统一接口，多种实现
- **工厂模式**: ProviderFactory - 配置驱动的对象创建
- **单一职责**: 每个类只负责一个功能领域

## 标准项目结构

```
freerouter/                          # 项目根目录
├── freerouter/                      # 核心代码包
│   ├── __init__.py              # 包初始化
│   ├── __version__.py           # 版本信息
│   ├── core/                    # 核心功能
│   │   ├── __init__.py
│   │   ├── fetcher.py           # FreeRouterFetcher 主类
│   │   └── factory.py           # ProviderFactory
│   └── providers/               # Provider 实现
│       ├── __init__.py
│       ├── base.py              # BaseProvider 抽象基类
│       ├── openrouter.py        # OpenRouter Provider
│       ├── ollama.py            # Ollama Provider
│       ├── modelscope.py        # ModelScope Provider
│       └── static.py            # Static Provider
├── scripts/                      # 可执行脚本
│   ├── fetch.py                 # 获取模型并生成配置
│   ├── start.py                 # 启动 litellm 服务
│   └── update.sh                # 更新并重启服务
├── tests/                        # 测试代码
│   ├── __init__.py
│   ├── test_providers.py        # Provider 单元测试
│   └── test_fetcher.py          # Fetcher 单元测试
├── docs/                         # 文档
│   ├── architecture.md          # 架构设计文档
│   ├── providers.md             # Provider 使用指南
│   └── development.md           # 开发指南
├── examples/                     # 示例配置
│   └── providers.yaml.example   # Provider 配置示例
├── config/                       # 配置文件目录（git ignore）
│   ├── providers.yaml           # 用户的 Provider 配置
│   └── config.yaml              # 生成的 litellm 配置
├── .github/                      # GitHub 配置
│   └── workflows/               # CI/CD
│       └── test.yml
├── setup.py                      # 安装配置
├── pyproject.toml               # 现代 Python 项目配置
├── requirements.txt             # 依赖列表
├── requirements-dev.txt         # 开发依赖
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git 忽略规则
├── LICENSE                      # 许可证
├── README.md                    # 项目说明（英文）
├── README_ZH.md                 # 项目说明（中文）
├── CONTRIBUTING.md              # 贡献指南
├── CHANGELOG.md                 # 变更日志
├── CLAUDE.md                    # 本文档
├── Dockerfile                   # Docker 镜像
└── docker-compose.yml           # Docker Compose 配置
```

## 代码组织规范

### 1. 包结构

```python
freerouter/
├── __init__.py              # 导出公共 API
├── __version__.py           # 版本号
├── core/                    # 核心逻辑
│   ├── __init__.py
│   ├── fetcher.py           # 主要业务逻辑
│   └── factory.py           # 工厂类
└── providers/               # Provider 实现
    ├── __init__.py          # 导出所有 Provider
    ├── base.py              # 抽象基类
    ├── openrouter.py
    ├── ollama.py
    ├── modelscope.py
    └── static.py
```

### 2. 导入规范

```python
# 标准库
import os
import sys
from typing import List, Dict

# 第三方库
import yaml
import requests
from dotenv import load_dotenv

# 项目内部
from freerouter.providers.base import BaseProvider
from freerouter.core.factory import ProviderFactory
```

### 3. 类和函数命名

- **类名**: PascalCase (如 `OpenRouterProvider`)
- **函数/方法**: snake_case (如 `fetch_models`)
- **常量**: UPPER_SNAKE_CASE (如 `DEFAULT_PORT`)
- **私有方法**: 前缀 `_` (如 `_resolve_env_vars`)

### 4. 文档字符串

```python
def fetch_models(self) -> List[Dict[str, Any]]:
    """
    从 Provider 获取模型列表

    Returns:
        包含模型信息的字典列表，每个字典至少包含 'id' 字段

    Raises:
        requests.RequestException: 网络请求失败
    """
    pass
```

## 架构设计

### Provider 策略模式

**核心思想**: 每个 AI 服务提供商都是一个 Provider，实现统一的接口。

```python
class BaseProvider(ABC):
    """所有 Provider 的抽象基类"""

    @abstractmethod
    def fetch_models(self) -> List[Dict[str, Any]]:
        """获取模型列表 - 每个 Provider 实现不同"""
        pass

    def filter_models(self, models: List) -> List:
        """筛选模型 - 可选择性重写"""
        return models

    def format_service(self, model: Dict) -> Dict:
        """格式化为 litellm 配置 - 可选择性重写"""
        pass
```

**Provider 类型**:

1. **API Provider** (如 OpenRouter):
   - 调用 API 获取模型列表
   - 需要 API Key
   - 动态发现模型

2. **Local Provider** (如 Ollama):
   - 调用本地 API
   - 无需 API Key
   - 发现已安装模型

3. **Static Provider** (如 ModelScope):
   - 使用预定义模型列表
   - 可选 API Key
   - 静态配置

4. **Manual Provider** (Static):
   - 完全手动配置
   - 单个模型/服务
   - 最大灵活性

### Factory 工厂模式

**核心思想**: 通过配置文件声明式创建 Provider，解耦配置和实现。

```python
class ProviderFactory:
    @staticmethod
    def create_from_config(config: Dict) -> BaseProvider:
        """从配置字典创建 Provider 实例"""
        provider_type = config.get("type")

        if provider_type == "openrouter":
            return OpenRouterProvider(**config)
        elif provider_type == "ollama":
            return OllamaProvider(**config)
        # ...
```

**优势**:
- 添加新 Provider 不影响现有代码
- 配置文件控制所有 Provider
- 支持环境变量注入 (`${ENV_VAR}`)

### 配置管理

**两层配置结构**:

1. **providers.yaml** - 用户配置，声明要使用的 Provider
   ```yaml
   providers:
     - type: openrouter
       enabled: true
       api_key: ${OPENROUTER_API_KEY}
   ```

2. **config.yaml** - 自动生成，litellm 使用的配置
   ```yaml
   model_list:
     - model_name: gpt-3.5-turbo
       litellm_params: {...}
   ```

**环境变量解析**:
- 格式: `${ENV_VAR_NAME}`
- 运行时从 `.env` 或系统环境变量读取
- 支持嵌套配置

## 开发规范

### 1. 添加新 Provider

步骤：

1. 在 `freerouter/providers/` 创建新文件
2. 继承 `BaseProvider` 并实现必需方法
3. 在 `freerouter/providers/__init__.py` 导出
4. 在 `ProviderFactory.create_from_config()` 添加分支
5. 更新 `examples/providers.yaml.example`
6. 编写单元测试
7. 更新文档

示例：

```python
# freerouter/providers/my_provider.py
from .base import BaseProvider

class MyProvider(BaseProvider):
    @property
    def provider_name(self) -> str:
        return "myprovider"

    def fetch_models(self) -> List[Dict[str, Any]]:
        # 实现获取逻辑
        return [{"id": "model-1"}]
```

### 2. 测试规范

- 每个 Provider 必须有单元测试
- 使用 `pytest` 框架
- Mock 外部 API 调用
- 测试覆盖率 > 80%

```python
# tests/test_providers.py
def test_openrouter_provider():
    provider = OpenRouterProvider(api_key="test")
    models = provider.fetch_models()
    assert isinstance(models, list)
```

### 3. 文档规范

- README.md: 用户快速开始指南（中文）
- README_EN.md: 英文版 README
- docs/: 详细技术文档
- 代码内联文档: Docstring
- CHANGELOG.md: 版本变更记录

### 4. Git 规范

**分支策略**:
- `main`: 稳定版本
- `develop`: 开发分支
- `feature/*`: 功能分支
- `hotfix/*`: 紧急修复

**Commit 规范**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/工具

示例:
```
feat(providers): add ModelScope provider

- Implement ModelScopeProvider class
- Add static model list support
- Update factory and documentation

Closes #123
```

## 依赖管理

### 核心依赖

```
litellm>=1.0.0          # AI 路由核心
pyyaml>=6.0             # YAML 配置解析
requests>=2.31.0        # HTTP 请求
python-dotenv>=1.0.0    # 环境变量管理
```

### 开发依赖

```
pytest>=7.0.0           # 测试框架
pytest-cov>=4.0.0       # 测试覆盖率
black>=23.0.0           # 代码格式化
flake8>=6.0.0           # 代码检查
mypy>=1.0.0             # 类型检查
```

## 性能和安全

### 性能考虑

1. **Provider 并发**: 多个 Provider 可并发获取模型
2. **缓存策略**: 考虑缓存 API 响应（可选）
3. **超时设置**: 所有网络请求必须设置 timeout

### 安全考虑

1. **API Key 管理**:
   - 永远不要硬编码 API Key
   - 使用环境变量或 `.env` 文件
   - `.env` 文件必须在 `.gitignore` 中

2. **输入验证**:
   - 验证配置文件格式
   - 检查必需字段
   - 防止注入攻击

3. **错误处理**:
   - 捕获并记录异常
   - 不暴露敏感信息
   - 提供友好的错误消息

## 版本管理

遵循语义化版本 (Semantic Versioning):

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的 Bug 修复

当前版本: `0.1.0` (初始开发版本)

## CI/CD

### GitHub Actions

1. **测试工作流**:
   - 每次 push 和 PR 触发
   - 运行单元测试
   - 检查代码覆盖率

2. **发布工作流**:
   - Tag 触发
   - 构建 Docker 镜像
   - 发布到 Docker Hub

## 未来规划

### Phase 1 (Current)
- ✅ 核心架构设计
- ✅ OpenRouter, Ollama, ModelScope Provider
- ✅ 基础文档

### Phase 2
- [ ] 单元测试覆盖
- [ ] CI/CD 集成
- [ ] 更多 Provider (HuggingFace, Together AI)

### Phase 3
- [ ] Web UI 管理界面
- [ ] 模型性能监控
- [ ] 成本追踪

### Phase 4
- [ ] 分布式部署
- [ ] 高可用配置
- [ ] 企业级功能

## 常见问题

### Q: 为什么使用策略模式？
A: 因为不同 Provider 获取模型的方式完全不同（API、本地、静态），但最终目标相同（生成 litellm 配置）。策略模式让我们统一处理这些差异。

### Q: 为什么需要工厂模式？
A: 让配置和代码解耦。用户通过 YAML 声明要使用哪些 Provider，工厂负责创建实例。添加新 Provider 不需要修改配置加载逻辑。

### Q: 配置文件为什么分两层？
A: `providers.yaml` 是人类友好的配置，`config.yaml` 是机器友好的配置。分离关注点，让每个文件只做一件事。

### Q: 如何确保代码质量？
A:
1. 单元测试 + 高覆盖率
2. 代码审查（PR review）
3. 自动化工具（black, flake8, mypy）
4. 文档先行

## 联系方式

- 项目仓库: https://github.com/mmdsnb/freerouter
- Issues: https://github.com/mmdsnb/freerouter/issues
- Discussions: https://github.com/mmdsnb/freerouter/discussions

---

**最后更新**: 2025-12-25
**维护者**: @mmdsnb

记住：**简单、清晰、可维护** 永远比"聪明"更重要！
