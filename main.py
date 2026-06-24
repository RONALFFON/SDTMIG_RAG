#!/usr/bin/env python3
"""
SDTMIG_RAG 一键启动脚本
同时启动前后端开发环境
"""

import os
import socket
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_PORT = 5173
BACKEND_PORT = 5000


def ensure_utf8_stdio() -> None:
    """确保 Windows 下使用 UTF-8 编码"""
    if os.name != "nt":
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    """检查端口是否已被占用"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def wait_port(host: str, port: int, seconds: int) -> bool:
    """等待端口就绪"""
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.5)
    return False


def start_backend() -> None:
    """启动后端服务"""
    if is_port_open("127.0.0.1", BACKEND_PORT):
        print(f"[Backend] 端口 {BACKEND_PORT} 已被占用，跳过启动")
        return

    print("[Backend] 启动 Flask 后端服务...")

    env = os.environ.copy()
    env["FLASK_HOST"] = "0.0.0.0"
    env["FLASK_PORT"] = str(BACKEND_PORT)
    env["FLASK_DEBUG"] = "True"

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    log_file = open(BACKEND_DIR / "backend.log", "a", encoding="utf-8")
    subprocess.Popen(
        [sys.executable, "-m", "backend.run"],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        shell=False,
        creationflags=creation_flags,
    )

    print(f"[Backend] 等待后端启动 (最多 15 秒)...")
    if wait_port("127.0.0.1", BACKEND_PORT, seconds=15):
        print(f"[Backend] ✓ 后端已启动: http://127.0.0.1:{BACKEND_PORT}")
    else:
        print(f"[Backend] ⚠ 后端启动超时，请检查日志: {BACKEND_DIR / 'backend.log'}")


def start_frontend() -> None:
    """启动前端服务"""
    if is_port_open("127.0.0.1", FRONTEND_PORT):
        print(f"[Frontend] 端口 {FRONTEND_PORT} 已被占用，跳过启动")
        return

    # 检查 node_modules
    if not (FRONTEND_DIR / "node_modules").exists():
        print("[Frontend] 安装前端依赖...")
        result = subprocess.run(
            ["npm", "install"],
            cwd=str(FRONTEND_DIR),
            shell=(os.name == "nt"),
        )
        if result.returncode != 0:
            print("[Frontend] ⚠ 依赖安装失败，请手动运行: cd frontend && npm install")
            return

    print("[Frontend] 启动 Vite 开发服务器...")

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    log_file = open(FRONTEND_DIR / "vite.log", "a", encoding="utf-8")
    subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        shell=(os.name == "nt"),
        creationflags=creation_flags,
    )

    print(f"[Frontend] 等待前端启动 (最多 10 秒)...")
    if wait_port("127.0.0.1", FRONTEND_PORT, seconds=10):
        print(f"[Frontend] ✓ 前端已启动: http://127.0.0.1:{FRONTEND_PORT}")
    else:
        print(f"[Frontend] ⚠ 前端启动超时，请检查日志: {FRONTEND_DIR / 'vite.log'}")


def main() -> int:
    ensure_utf8_stdio()
    print("=" * 50)
    print("  SDTMIG_RAG 一键启动")
    print("=" * 50)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"后端目录:   {BACKEND_DIR}")
    print(f"前端目录:   {FRONTEND_DIR}")
    print()

    try:
        start_backend()
        start_frontend()
    except Exception as exc:
        print(f"\n[Error] 启动失败: {exc}")
        return 1

    print()
    print("=" * 50)
    print("  启动完成")
    print("=" * 50)
    print(f"后端 API:  http://127.0.0.1:{BACKEND_PORT}")
    print(f"前端页面:  http://127.0.0.1:{FRONTEND_PORT}")
    print()
    print("按 Ctrl+C 停止所有服务")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止服务...")

    return 0


if __name__ == "__main__":
    sys.exit(main())
