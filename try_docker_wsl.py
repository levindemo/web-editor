import os

# 打印所有Docker相关的环境变量
docker_env = {k: v for k, v in os.environ.items() if k.startswith('DOCKER_')}
print("Docker相关环境变量:", docker_env)


# 强制清除可能存在的DOCKER_HOST环境变量
if 'DOCKER_HOST' in os.environ:
    del os.environ['DOCKER_HOST']
    print("已强制删除DOCKER_HOST环境变量")

import docker
from docker.utils import utils

# # 查看自动检测的连接地址
try:
    auto_detected_url = utils.parse_host(None)  # 模拟自动检测过程
    print(f"自动检测的Docker连接地址: {auto_detected_url}")
except Exception as e:
    print(f"自动检测过程出错: {e}")

import docker

# 推荐使用环境变量自动配置
# client = docker.from_env()
base_url = 'unix:///var/run/docker.sock'
base_url = 'npipe:////./pipe/docker_engine'
base_url = 'tcp://localhost:2375'
# base_url = 'tcp://172.26.224.1:2375'
client = docker.DockerClient(base_url=base_url)

# 测试连接
try:
    print(client.version())  # 打印Docker版本信息
except docker.errors.APIError as e:
    print(f"API错误: {e}")
except Exception as e:
    print(f"连接错误: {e}")
# 测试连接
print(client.containers.list())