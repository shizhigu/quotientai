# Creator OS 部署指南

## 环境要求

- Python 3.11+
- Node.js 18+ (用于MCP工具)
- 环境变量配置

## 快速部署到 Render

### 1. 准备环境变量

在Render控制台中设置以下环境变量：

```bash
# 必需的API密钥
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
PERPLEXITY_API_KEY=your_perplexity_api_key
TAVILY_API_KEY=your_tavily_api_key

# 可选的Google API密钥
GOOGLE_API_KEY=your_google_api_key

# 运行时配置
PORT=8000
PYTHONPATH=/opt/render/project/src
```

### 2. 部署方式

#### 方式A: 使用Render.yaml (推荐)

1. 将代码推送到GitHub仓库
2. 在Render控制台创建新Web Service
3. 连接GitHub仓库
4. Render会自动检测`render.yaml`配置文件
5. 在Environment页面设置上述环境变量
6. 部署！

#### 方式B: 手动配置

1. 创建新Web Service
2. 连接GitHub仓库
3. 设置构建和启动命令：
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn creatoros.main:app --host 0.0.0.0 --port $PORT`
4. 设置环境变量
5. 部署

### 3. 验证部署

部署成功后，访问以下端点验证：

- `https://your-app.onrender.com/health` - 健康检查
- `https://your-app.onrender.com/docs` - API文档
- `https://your-app.onrender.com/` - 根路径

## 本地开发

### 启动开发服务器

```bash
# 安装依赖
pip install -r requirements.txt

# 安装MCP工具
npm install -g perplexity-mcp

# 设置环境变量
export OPENROUTER_API_KEY=your_key
export PERPLEXITY_API_KEY=your_key
export TAVILY_API_KEY=your_key

# 启动服务器
uvicorn creatoros.main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker部署

### 构建和运行

```bash
# 构建镜像
docker build -t creatoros .

# 运行容器
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key \
  -e PERPLEXITY_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  creatoros
```

### 使用Docker Compose

```yaml
version: '3.8'
services:
  creatoros:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OPENROUTER_BASE_URL=${OPENROUTER_BASE_URL}
      - PERPLEXITY_API_KEY=${PERPLEXITY_API_KEY}
      - TAVILY_API_KEY=${TAVILY_API_KEY}
    restart: unless-stopped
```

## 其他平台部署

### Railway

1. 连接GitHub仓库
2. 设置环境变量
3. Railway会自动检测Python应用并部署

### Fly.io

1. 安装Fly CLI
2. `fly auth login`
3. `fly launch` (会检测Dockerfile)
4. 设置环境变量: `fly secrets set OPENROUTER_API_KEY=your_key`
5. `fly deploy`

### Heroku

1. 创建`runtime.txt`: `python-3.11.0`
2. 创建`Procfile`: `web: uvicorn creatoros.main:app --host 0.0.0.0 --port $PORT`
3. 设置环境变量
4. `git push heroku main`

## 监控和日志

### 健康检查

- `/health` - 服务状态
- `/` - 基本信息

### 日志查看

```bash
# Render
通过Render控制台查看日志

# Docker
docker logs container_name

# 本地
uvicorn日志会输出到控制台
```

## 故障排除

### 常见问题

1. **MCP工具错误**
   - 确保Node.js已安装
   - 确保全局安装了perplexity-mcp: `npm install -g perplexity-mcp`

2. **API密钥错误**
   - 检查环境变量是否正确设置
   - 验证API密钥有效性

3. **数据库连接问题**
   - 检查SQLite文件权限
   - 确保数据目录可写

4. **端口冲突**
   - 默认端口8000，可通过PORT环境变量修改

### 性能优化

- 使用Render Standard计划获得更好性能
- 考虑使用Redis进行session缓存
- 监控内存使用，必要时升级计划

## 安全考虑

- 所有API密钥都通过环境变量配置
- 不要在代码中硬编码敏感信息
- 定期轮换API密钥
- 考虑设置CORS策略
- 生产环境建议使用HTTPS

## 支持

如有问题，请检查：
1. 环境变量配置
2. 依赖项安装
3. 日志输出
4. API端点响应 