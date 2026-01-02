# opaqAI

A compact AI for redaction with website GUI and OpenAI API proxy with automatic text desensitization.

这是一个使用HanLP进行文本脱敏的AI应用，支持Web界面和符合OpenAI API规范的代理功能。

## 功能特性

- 🔒 **智能脱敏**: 使用HanLP模型识别和脱敏中文敏感信息（姓名、电话、邮箱等）
- 🌐 **Web界面**: 提供友好的Web界面进行文本脱敏
- 🔌 **OpenAI API代理**: 符合OpenAI API规范的本地代理，自动对用户输入进行脱敏
- 📊 **演示功能**: 展示脱敏处理的详细过程
- 🎯 **灵活配置**: 支持多种脱敏范围和自定义替换文本

## 脱敏范围

- **basic**: 基础脱敏（PHONE, PERSON, EMAIL, INTEGER）- 默认
- **enhanced**: 增强脱敏（排除TIME, DATE, AREA）
- **full**: 完全脱敏（所有识别到的实体）

## 快速开始

### 使用Docker Compose（推荐）

```bash
# 克隆仓库
git clone https://github.com/invictus-z/opaqAI.git
cd opaqAI

# 复制环境变量模板
cp .env.example .env

# 编辑.env文件配置你的环境变量
vim .env

# 启动服务
docker-compose up -d
```

### 使用Docker

```bash
# 克隆仓库
git clone https://github.com/invictus-z/opaqAI.git
cd opaqAI

# 构建镜像
docker build -t opaqai .

# 运行容器
docker run -p 8000:8000 opaqai
```

### 使用Python

```bash
# 安装依赖
pip install -r requirements.txt

# 运行应用
python run.py
```

应用将在 `http://localhost:8000` 启动。

## 环境变量配置

可以通过环境变量配置应用行为：

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEBUG` | `False` | 调试模式 |
| `PORT` | `8000` | 应用端口 |
| `DEFAULT_REPLACEMENT` | `[SECRET]` | 默认替换文本 |
| `DEFAULT_SCOPE` | `basic` | 默认脱敏范围 |
| `REMOTE_API_ENDPOINT` | `https://api.openai.com` | 远程API端点 |
| `REMOTE_API_KEY` | `""` | 远程API密钥（作为fallback，优先使用请求头） |
| `PROXY_TIMEOUT` | `300` | 代理超时时间（秒，5分钟） |
| `GUNICORN_WORKERS` | `1` | Gunicorn worker数量 |
| `GUNICORN_WORKER_CLASS` | `gevent` | Gunicorn worker类（gevent/sync/eventlet等） |
| `GUNICORN_BIND` | `0.0.0.0:8000` | Gunicorn绑定地址（默认使用PORT） |

### 配置示例

#### 使用.env文件（推荐）

创建`.env`文件（可以从`.env.example`复制）：

```bash
# 复制模板
cp .env.example .env

# 编辑.env文件
vim .env
```

.env文件内容示例：

```bash
DEBUG=False
PORT=8000
DEFAULT_REPLACEMENT=[SECRET]
DEFAULT_SCOPE=basic
REMOTE_API_ENDPOINT=https://api.openai.com
REMOTE_API_KEY=your-api-key-here
PROXY_TIMEOUT=300
GUNICORN_WORKERS=1
```

#### 使用命令行设置

```bash
# Linux/Mac
export REMOTE_API_ENDPOINT="https://api.openai.com"
export REMOTE_API_KEY="your-api-key-here"
export DEFAULT_SCOPE="enhanced"

# Windows
set REMOTE_API_ENDPOINT=https://api.openai.com
set REMOTE_API_KEY=your-api-key-here
set DEFAULT_SCOPE=enhanced
```

## API端点

### Web界面

- `/` - 主页，文本脱敏Web界面
- `/demo` - 演示页面，展示脱敏处理过程

### API接口

- `POST /api/desensitize` - 文本脱敏API
  
  请求体：
  ```json
  {
    "text": "张三的电话是13800138000",
    "replacement": "[保密]",
    "scope": "basic"
  }
  ```
  
  响应：
  ```json
  {
    "desensitized_text": "[保密]的电话是[保密]",
    "stats": {
      "PERSON": 1,
      "PHONE": 1
    }
  }
  ```

- `POST /v1/chat/completions` - OpenAI Chat Completions API代理
  
  自动对messages中role为user的content进行脱敏处理，然后转发到远程API。
  
  **API Key配置**：通过请求头传递Authorization，例如：
  ```bash
  curl http://localhost:8000/v1/chat/completions \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer your-api-key" \
    -d '{...}'
  ```
  也可以通过环境变量`REMOTE_API_KEY`配置（作为fallback）。
  
  示例请求：
  ```json
  {
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "我的名字是张三，电话是13800138000，请介绍一下Python"
      }
    ]
  }
  ```
  
  代理会将用户消息脱敏后转发到远程API，远程API收到的是：
  ```json
  {
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "我的名字是[SECRET]，电话是[SECRET]，请介绍一下Python"
      }
    ]
  }
  ```
  
  你可以在请求中添加自定义脱敏配置：
  ```json
  {
    "model": "gpt-3.5-turbo",
    "messages": [...],
    "desensitize_replacement": "[保密]",
    "desensitize_scope": "enhanced"
  }
  ```

- `POST /v4/chat/completions` - OpenAI Chat Completions API代理（v4版本）
  
  功能与/v1/chat/completions相同，支持通过请求头传递Authorization。

- **其他所有OpenAI端点** - 自动转发到`REMOTE_API_ENDPOINT`
  
  除了`/v1/chat/completions`和`/v4/chat/completions`（这两个端点会进行脱敏处理），
  其他所有OpenAI API端点都会直接转发到`REMOTE_API_ENDPOINT`，不进行脱敏处理。
  
  例如：
  - `GET /v1/models` - 转发到`REMOTE_API_ENDPOINT/v1/models`
  - `POST /v1/embeddings` - 转发到`REMOTE_API_ENDPOINT/v1/embeddings`
  - `POST /v1/completions` - 转发到`REMOTE_API_ENDPOINT/v1/completions`
  
  所有请求头（除host、content-length等）都会转发到远程API，包括Authorization头。

- `GET /health` - 健康检查

## 使用OpenAI API代理

### 使用curl

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {
        "role": "user",
        "content": "张三的电话是13800138000，你好"
      }
    ]
  }'
```

### 使用Python

```python
import openai

# 配置本地代理
openai.api_base = "http://localhost:8000/v1"
openai.api_key = "any-key"  # 本地代理不需要真实的API key

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "user",
            "content": "张三的电话是13800138000，你好"
        }
    ]
)

print(response.choices[0].message.content)
```

### 使用其他兼容OpenAI的客户端

由于opaqAI实现了OpenAI API规范，你可以使用任何兼容OpenAI的客户端，只需将API base URL设置为 `http://localhost:8000/v1` 即可。

## 架构说明

项目采用模块化设计，实现了脱敏和代理功能的解耦：

- `config.py` - 配置管理
- `redactor.py` - 脱敏模块（封装HanLP模型和脱敏逻辑）
- `proxy.py` - 代理模块（OpenAI API代理和请求转发）
- `run.py` - 主应用（Flask应用和路由）

## 许可证

见 [LICENSE](LICENSE) 文件。
