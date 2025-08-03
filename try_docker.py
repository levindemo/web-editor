import os

# Enable HyperV instead of running docker with WSL2 on Windows 10
docker_env = {k: v for k, v in os.environ.items() if k.startswith('DOCKER_')}
print("Docker env vars:", docker_env)

import docker
from docker.utils import utils

try:
    auto_detected_url = utils.parse_host(None)  # 模拟自动检测过程
    print(f"auto detected docker host address: {auto_detected_url}")
except Exception as e:
    print(f"auto detect docker host address error: {e}")

import docker

# recommend to use env var to config docker client
# client = docker.from_env()
# do not use the above when running in windows
# docker.errors.DockerException: Error while fetching server API version: Not supported URL scheme http+docker


base_url = 'tcp://localhost:2375'
# base_url = 'tcp://172.26.224.1:2375'
client = docker.DockerClient(base_url=base_url)
# test connection
try:
    print("docker version:")
    print(client.version())
except docker.errors.APIError as e:
    print(f"API Error: {e}")
except Exception as e:
    print(f"Connection Error: {e}")

print("show all containers:")
containers = client.containers.list()
for container in containers:
    print(container.name)

images = client.images.list()
# show all images
print("show all images:")
for image in images:
    print(image.tags)
