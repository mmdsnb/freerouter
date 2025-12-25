# FreeRouter Tests

## 测试原则

### API Key 一致性

**重要**: 在所有测试中，客户端和服务端必须使用相同的 API Key。

```python
# tests/test_integration.py 中定义
TEST_MASTER_KEY = "test-master-key-12345"

# 服务端配置 (config.yaml)
litellm_settings:
  master_key: test-master-key-12345

# 客户端调用
headers = {"Authorization": f"Bearer {TEST_MASTER_KEY}"}
```

### 为什么这样做？

1. **可重复性**: 测试应该是可重复的，不依赖外部环境
2. **CI/CD 友好**: 在自动化测试中，使用固定的测试密钥
3. **一致性**: 客户端和服务端使用相同的密钥，确保测试有效

### 测试类型

1. **单元测试** (`test_providers.py`, `test_fetcher.py`)
   - 测试单个组件的功能
   - 不依赖外部服务
   - 使用 mock 模拟外部调用

2. **集成测试** (`test_integration.py`)
   - 测试配置生成流程
   - 测试 API Key 一致性
   - 快速测试（不启动服务）

3. **E2E 端到端测试** (`test_e2e.py`) ⭐
   - **完整的服务端测试流程**
   - 测试从 fetch 到 start 的完整流程：
     1. 生成配置文件
     2. 启动真实的 LiteLLM 服务
     3. 调用 API 验证功能
   - 使用 static providers（不依赖外部 API）
   - 自动清理服务进程

## 运行测试

### 运行所有测试

```bash
pytest
```

**提示**: E2E 测试会启动真实服务，需要 ~10 秒

### 运行指定测试类型

```bash
# 只运行单元测试（快速）
pytest tests/test_providers.py tests/test_fetcher.py -v

# 只运行集成测试（快速）
pytest tests/test_integration.py -v

# 只运行 E2E 测试（完整服务端测试）
pytest tests/test_e2e.py -v
```

### 查看覆盖率

```bash
pytest --cov=freerouter --cov-report=term-missing
```

### E2E 测试说明

E2E 测试是**真正测试服务端的测试**：
- ✅ 测试完整流程：fetch → config → start → API
- ✅ 启动真实 LiteLLM 服务（自动清理）
- ✅ 验证 API 端点功能
- ✅ 测试认证机制
- ✅ 适合 CI/CD（使用 static providers，无外部依赖）

## CI/CD 注意事项

在 CI/CD 环境中：

1. 使用测试密钥（不是真实的 API Key）
2. 不要启动真实的 LiteLLM 服务（会有端口冲突）
3. 使用 mock 模拟外部 API 调用
4. 确保测试是幂等的（可以重复运行）

## 手动测试

如果需要测试真实的服务：

```bash
# 1. 启动服务
export LITELLM_MASTER_KEY=sk-1234
freerouter start

# 2. 在另一个终端测试
curl http://localhost:4000/v1/models \
  -H "Authorization: Bearer sk-1234"
```

注意：手动测试使用真实的 API Key 和服务，不适合自动化测试。
