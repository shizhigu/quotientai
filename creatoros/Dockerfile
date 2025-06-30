# 使用官方Python运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据目录（用于SQLite数据库）
RUN mkdir -p /app/data

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PYTHONPATH=/app
ENV PORT=8080

# 启动命令
CMD ["python", "main.py"] 