# FreeRouter 项目结构

```
freerouter/
├── freerouter/                          # 核心代码包
│   ├── __init__.py                   # 包初始化，导出公共 API
│   ├── __version__.py                # 版本信息
│   ├── core/                         # 核心功能模块
│   │   ├── __init__.py
│   │   ├── fetcher.py                # FreeRouterFetcher 主类
│   │   └── factory.py                # ProviderFactory 工厂类
│   └── providers/                    # Provider 实现
│       ├── __init__.py               # 导出所有 Provider
│       ├── base.py                   # BaseProvider 抽象基类
│       ├── openrouter.py             # OpenRouter Provider
│       ├── ollama.py                 # Ollama Provider
│       ├── modelscope.py             # ModelScope Provider
│       └── static.py                 # Static Provider
├── tests/                            # 测试代码
│   ├── __init__.py
│   ├── test_providers.py             # Provider 单元测试
│   └── test_fetcher.py               # Fetcher 单元测试
├── docs/                             # 文档目录
├── examples/                         # 示例配置
│   └── providers.yaml.example        # Provider 配置示例
├── config/                           # 配置文件目录 (gitignored)
│   ├── .gitkeep                      # 保持目录在 git 中
│   ├── providers.yaml                # 用户的 Provider 配置
│   └── config.yaml                   # 生成的 litellm 配置
├── .github/                          # GitHub 配置
│   └── workflows/                    # CI/CD 工作流
├── setup.py                          # 安装配置 (传统)
├── pyproject.toml                    # 现代 Python 项目配置
├── requirements.txt                  # 生产依赖
├── requirements-dev.txt              # 开发依赖
├── .env.example                      # 环境变量示例
├── .gitignore                        # Git 忽略规则
├── LICENSE                           # MIT 许可证
├── README.md                         # 项目说明 (中文)
├── CLAUDE.md                         # 项目规范和设计文档 ⭐
├── CONTRIBUTING.md                   # 贡献指南
├── CHANGELOG.md                      # 变更日志
├── Dockerfile                        # Docker 镜像
└── docker-compose.yml                # Docker Compose 配置
```

## 目录说明

### `/freerouter` - 核心代码包
标准 Python 包结构，包含所有核心代码。

#### `/freerouter/core` - 核心业务逻辑
- `fetcher.py`: 主要业务逻辑，管理 Provider 和生成配置
- `factory.py`: 工厂类，根据配置创建 Provider 实例

#### `/freerouter/providers` - Provider 实现
- `base.py`: 抽象基类，定义 Provider 接口
- 其他文件: 具体 Provider 实现

### `/tests` - 测试代码
单元测试和集成测试。

### `/config` - 配置文件目录
用户的配置文件，gitignored，不提交到仓库。

### `/examples` - 示例和模板
配置文件的示例，提交到仓库供用户参考。

### `/docs` - 文档
详细的技术文档（未来扩展）。

## 设计原则体现

1. **关注点分离**
   - `freerouter/`: 库代码
   - `tests/`: 测试代码
   - `config/`: 用户数据

2. **标准 Python 结构**
   - 符合 PEP 标准
   - 可以用 `pip install -e .` 安装
   - 可以发布到 PyPI

3. **清晰的层次**
   - 核心层 (core)
   - 提供商层 (providers)
   - 脚本层 (scripts)
   - 测试层 (tests)

## 文件命名规范

- **模块文件**: 小写+下划线 (`fetch_models.py`)
- **类名**: PascalCase (`FreeRouterFetcher`)
- **函数名**: 小写+下划线 (`get_services`)
- **常量**: 大写+下划线 (`DEFAULT_PORT`)

## 导入路径示例

```python
# 从外部导入
from freerouter import FreeRouterFetcher
from freerouter.providers.openrouter import OpenRouterProvider

# 包内部导入
from freerouter.core.factory import ProviderFactory
from freerouter.providers.base import BaseProvider
```

这样的结构让项目：
- ✅ 专业且易于理解
- ✅ 符合 Python 社区标准
- ✅ 易于测试和维护
- ✅ 可以轻松发布到 PyPI
