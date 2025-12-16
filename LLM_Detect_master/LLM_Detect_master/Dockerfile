# 设置基础镜像
FROM python:3.14

# 设置工作目录
WORKDIR /app

# 复制应用程序文件到容器中，"."表示当前路径(Dockerfile文件所在路径)
COPY ./requirements.txt /app

# 安装依赖
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple && pip config set install.trusted-host mirrors.aliyun.com && \
    pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com -r requirements.txt
# 容器启动时执行的命令
CMD ["python", "LLM_Detection_System/app.py"]
