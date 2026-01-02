FROM python:3.8

# 设置工作目录
WORKDIR /opaqAI/

# 复制依赖文件
COPY requirements.txt .

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.mirrors.ustc.edu.cn/simple

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 使用gunicorn运行应用
CMD ["gunicorn", "run:app", "-c", "gunicorn.conf.py"]
