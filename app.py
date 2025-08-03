import os
import json
import time
import docker
from flask import Flask, render_template, request, jsonify
# load .env
from dotenv import load_dotenv
from util import decode_bytes_recursively

load_dotenv()
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)

# create logger
logger = logging.getLogger(__name__)

app = Flask(__name__)

try:
    # base_url = 'npipe:////./pipe/docker_engine'
    base_url = "tcp://localhost:2375"
    client = docker.DockerClient(base_url=base_url)

    # client = docker.from_env()
except Exception as e:
    logger.error(f"Fail to start docker client2, error is: {str(e)}")
    client = None
# 容器超时时间（秒）
CONTAINER_TIMEOUT = 300  # 5分钟
# 代码执行超时时间（秒）
EXECUTION_TIMEOUT = 10

# 跟踪活跃容器
active_containers = {}


def create_container():
    try:
        base_image = os.getenv("CODE_EXEC_DOCKER_IMAGE", "ubuntu:latest")
        client.images.pull(base_image)
        logger.info(f"Successfully pulled {base_image} image")
        # format current date time as ISO format
        iso_date_str = time.strftime("%Y%m%d%H%M%S", time.localtime())
        random_name_id_with_day_str = (os.getenv("CODE_EXEC_CONTAINER_PREFIX",
                                                 "python-container")
                                       + "-" + iso_date_str
                                       + "-" + str(int(time.time()))
                                       )
        logger.info(f"Start to create container {random_name_id_with_day_str}")
        container = client.containers.create(
            base_image,
            command="/bin/bash",
            tty=True,
            detach=True,
            name=random_name_id_with_day_str,
            network_mode="none",  # 禁用网络以提高安全性
            mem_limit="256m",  # 限制内存使用
            cpu_period=100000,
            cpu_quota=50000  # 限制CPU使用率为50%
        )
        container.start()
        logger.info("Successfully created and started container")
        # 在容器中安装Python3和必要工具
        # install_commands = [
        #     "apt-get update",
        #     "apt-get install -y python3 python3-pip",
        #     "pip3 install --upgrade pip"
        # ]
        install_commands_file = os.getenv("CODE_EXEC_INSTALL_CMD_FILE", os.getcwd() + "/code_exec_container_init.sh")
        if not os.path.exists(install_commands_file):
            raise Exception(f"install commands file {install_commands_file} not exists")
        with open(install_commands_file, "r") as f:
            install_commands = f.readlines()
        # filter out empty line
        install_commands = [cmd.strip() for cmd in install_commands if cmd.strip()]
        # filter out comment line
        install_commands = [cmd for cmd in install_commands if not cmd.startswith("#")]
        logger.info("Start to init container")
        for cmd in install_commands:
            exec_result = container.exec_run(
                cmd,
                detach=False,
                tty=True
            )
            if exec_result.exit_code != 0:
                container.stop()
                container.remove()
                logger.error(f"Failed to install dependencies: {exec_result.output}")
                raise Exception(f"Failed to install dependencies: {exec_result.output}")

        # 记录容器创建时间
        active_containers[container.id] = {
            "container": container,
            "created_at": time.time()
        }
        logger.info(f"add active container {container.id}")
        return container.id

    except Exception as e:
        app.logger.error(f"Error creating container: {str(e)}")
        raise


def clean_up_containers():
    """清理超时的容器"""
    current_time = time.time()
    to_remove = []
    logger.info(f"start to clean up containers, current active containers: {active_containers}")
    for container_id, info in active_containers.items():
        if current_time - info["created_at"] > CONTAINER_TIMEOUT:
            to_remove.append(container_id)

    for container_id in to_remove:
        try:
            container = active_containers[container_id]["container"]
            container.stop()
            container.remove()
            del active_containers[container_id]
            app.logger.info(f"Removed expired container: {container_id}")
        except Exception as e:
            app.logger.error(f"Error removing container {container_id}: {str(e)}")
            if container_id in active_containers:
                del active_containers[container_id]


def get_or_create_container():
    """获取一个现有容器或创建新容器"""
    # 先清理超时容器
    clean_up_containers()

    # 如果有活跃容器，返回第一个
    if active_containers:
        return next(iter(active_containers.keys()))

    # 否则创建新容器
    return create_container()


def execute_code(container_id, code):
    logger.info(f"start to execute code in container {container_id}")
    if container_id not in active_containers:
        raise Exception("Container not found")

    container = active_containers[container_id]["container"]

    escaped_code = code.replace("'", "'\\''")
    write_cmd = f"touch /tmp/code.py"
    exec_result = container.exec_run(
        write_cmd,
        detach=False,
        tty=True
    )
    logger.info(f"create code file, result {exec_result}")
    write_cmd = f"echo '{escaped_code}' > /tmp/code.py"
    # use cat to write code in to code.py
    # write_cmd = f"cat > /tmp/code.py <<EOF\n{escaped_code}\nEOF"
    exec_result = container.exec_run(
        write_cmd,
        detach=False,
        tty=True
    )
    logger.info(f"write code to file result is {exec_result}")
    if exec_result.exit_code != 0:
        return {
            "success": False,
            "output": f"Error writing code to file: {exec_result.output}"
        }

    try:
        logger.info("start to execute code")
        exec_result = container.exec_run(
            "python3 /tmp/code.py",
            detach=False,
            tty=True
        )

        return {
            "success": exec_result.exit_code == 0,
            "output": exec_result.output,
            "exit_code": exec_result.exit_code
        }
    except docker.errors.ContainerError as e:
        return {
            "success": False,
            "output": f"Container error: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "output": f"Error executing code: {str(e)}"
        }


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/execute', methods=['POST'])
def execute():
    """for code execution on active container"""
    try:
        data = request.json
        code = data.get('code', '')

        if not code:
            return jsonify({
                "success": False,
                "output": "No code provided"
            })

        container_id = get_or_create_container()
        logger.info(f"pickup container_id: {container_id}")
        result = execute_code(container_id, code)
        logger.info(f"result is {result}")
        result = decode_bytes_recursively(result)
        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Error in execute endpoint: {str(e)}")
        return jsonify({
            "success": False,
            "output": f"Server error: {str(e)}"
        })


@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({"status": "healthy", "containers": len(active_containers)})


if __name__ == '__main__':
    import atexit


    def cleanup_on_exit():
        for container_id, info in active_containers.items():
            try:
                info["container"].stop()
                info["container"].remove()
            except:
                pass


    # make sure the containers are all stop and remove when app exit
    atexit.register(cleanup_on_exit)

    # only enable debug on local development
    app.run(host='0.0.0.0', port=5000, debug=False)
