import json
import os
import pathlib
import socket

import yaml


def load_project_config():
    cfg_path = os.environ.get("PROJECT_CONFIG_PATH", "/workspace/config/project.yaml")
    if not pathlib.Path(cfg_path).exists():
        cfg_path = "/home/mohamed/Desktop/Cognitive Project/emotion_robot/config/project.yaml"
    with open(cfg_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def resolve_gateway_target(cfg):
    transport = cfg["gateway"]["transport"]
    env_host = os.environ.get("ROBOT_GATEWAY_HOST")
    env_port = os.environ.get("ROBOT_GATEWAY_PORT")
    if env_host:
        return env_host, int(env_port or cfg["gateway"]["port"])
    if transport == "local_tcp":
        return cfg["gateway"]["local_host"], int(cfg["gateway"]["port"])
    host = os.environ.get("NGROK_HOST", "")
    port = os.environ.get("NGROK_PORT", "")
    if not (host and port):
        env_file = pathlib.Path(os.environ.get("NGROK_ENV_FILE", "/workspace/runtime/ngrok.env"))
        if not env_file.exists():
            env_file = pathlib.Path("/home/mohamed/Desktop/Cognitive Project/emotion_robot/runtime/ngrok.env")
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if line.startswith("NGROK_HOST="):
                    host = line.split("=", 1)[1].strip()
                if line.startswith("NGROK_PORT="):
                    port = line.split("=", 1)[1].strip()
    if host and port:
        return host, int(port)
    reserved = cfg["ngrok"]["reserved_tcp_addr"]
    if reserved:
        return reserved.split(":")[0], int(reserved.split(":")[1])
    raise RuntimeError("No ngrok endpoint available. Run scripts/ngrok-url.sh for ephemeral endpoint.")


def send_json_line(sock: socket.socket, payload: dict):
    sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
