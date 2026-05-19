from __future__ import annotations

import os
import shutil
import stat
import subprocess
from pathlib import Path

import yaml


def _write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _prepare_env(tmp_path: Path, mode: str, transport: str, use_ephemeral=True, token_var: str = "NGROK_AUTHTOKEN"):
    root = tmp_path / "emotion_robot"
    (root / "scripts").mkdir(parents=True)
    (root / "config").mkdir(parents=True)
    (root / "runtime").mkdir(parents=True)
    (root / "docker").mkdir(parents=True)
    (root / "bin").mkdir(parents=True)

    src_root = Path(__file__).resolve().parents[1]
    shutil.copy2(src_root / "scripts" / "up.sh", root / "scripts" / "up.sh")
    shutil.copy2(src_root / "scripts" / "lib_config.py", root / "scripts" / "lib_config.py")

    cfg = {
        "deployment": {"mode": mode},
        "gateway": {"transport": transport, "port": 8765, "local_host": "127.0.0.1"},
        "ngrok": {
            "enabled": False,
            "authtoken_env": token_var,
            "reserved_tcp_addr": "",
            "use_ephemeral_tcp": use_ephemeral,
        },
        "inference": {"backend": "auto", "device": "auto"},
    }
    with open(root / "config" / "project.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)

    docker_stub = """#!/usr/bin/env bash
set -euo pipefail
echo "$*" >> "${DOCKER_LOG:?}"
exit 0
"""
    _write_executable(root / "bin" / "docker", docker_stub)

    ngrok_stub = """#!/usr/bin/env bash
set -euo pipefail
echo "called" >> "${NGROK_LOG:?}"
exit 0
"""
    _write_executable(root / "scripts" / "ngrok-url.sh", ngrok_stub)

    env = os.environ.copy()
    env["PATH"] = f"{root / 'bin'}:{env['PATH']}"
    env["DOCKER_LOG"] = str(root / "runtime" / "docker.log")
    env["NGROK_LOG"] = str(root / "runtime" / "ngrok.log")
    return root, env


def _run_up(root: Path, env: dict[str, str]):
    return subprocess.run(
        ["bash", "scripts/up.sh"],
        cwd=root,
        env=env,
        check=False,
        text=True,
        capture_output=True,
    )


def test_up_robot_only_starts_robot_profile(tmp_path: Path):
    root, env = _prepare_env(tmp_path, mode="robot_only", transport="local_tcp")
    result = _run_up(root, env)

    assert result.returncode == 0
    assert "Started robot_only path" in result.stdout
    log = (root / "runtime" / "docker.log").read_text(encoding="utf-8")
    assert "stop laptop ngrok" in log
    assert "--profile robot up -d robot" in log


def test_up_laptop_offload_local_tcp_prints_target(tmp_path: Path):
    root, env = _prepare_env(tmp_path, mode="laptop_offload", transport="local_tcp")
    result = _run_up(root, env)

    assert result.returncode == 0
    assert "Laptop offload local tcp target: 127.0.0.1:8765" in result.stdout
    assert "Set ROBOT_GATEWAY_HOST=127.0.0.1" in result.stdout
    log = (root / "runtime" / "docker.log").read_text(encoding="utf-8")
    assert "--profile robot --profile laptop up -d robot laptop" in log
    assert "stop ngrok" in log


def test_up_laptop_offload_ngrok_requires_token(tmp_path: Path):
    root, env = _prepare_env(tmp_path, mode="laptop_offload", transport="ngrok_tcp", token_var="CUSTOM_TOKEN")
    result = _run_up(root, env)

    assert result.returncode == 1
    assert "Missing required ngrok token env var: CUSTOM_TOKEN" in result.stderr


def test_up_laptop_offload_ngrok_runs_profile_and_ngrok_url(tmp_path: Path):
    root, env = _prepare_env(tmp_path, mode="laptop_offload", transport="ngrok_tcp", use_ephemeral="true", token_var="CUSTOM_TOKEN")
    env["CUSTOM_TOKEN"] = "token-123"

    result = _run_up(root, env)

    assert result.returncode == 0
    assert "Laptop offload ngrok ready" in result.stdout
    docker_log = (root / "runtime" / "docker.log").read_text(encoding="utf-8")
    assert "--profile ngrok up -d ngrok" in docker_log
    ngrok_log = (root / "runtime" / "ngrok.log").read_text(encoding="utf-8")
    assert "called" in ngrok_log
