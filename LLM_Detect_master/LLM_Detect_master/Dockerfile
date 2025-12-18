# 设置基础镜像
FROM python:3.14

# 设置工作目录
WORKDIR /app

# 设置Python不缓冲输出(重要!确保print输出能实时显示在docker logs中)
ENV PYTHONUNBUFFERED=1

# 复制应用程序文件到容器中，"."表示当前路径(Dockerfile文件所在路径)
COPY ./requirements.txt /app

# 安装系统级依赖(poppler-utils用于PDF处理,fonts-wqy-microhei用于中文字体支持)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        poppler-utils \
        fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple && \
    pip config set install.trusted-host mirrors.aliyun.com && \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
# 容器启动时执行的命令
CMD ["python", "LLM_Detection_System/app.py"]
