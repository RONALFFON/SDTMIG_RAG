import os
import socket
import subprocess
import sys
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "rag_front"
FRONTEND_PORT = 5173
BACKEND_PORT = 5000


def is_port_open(host: str, port: int, timeout: float = 0.5) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def wait_port(host: str, port: int, seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_port_open(host, port):
            return True
        time.sleep(0.5)
    return False


def windows_to_wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    tail = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{tail}"


def start_backend() -> None:
    if is_port_open("127.0.0.1", BACKEND_PORT):
        print(f"[后端] 端口 {BACKEND_PORT} 已在监听，跳过启动。")
        return

    wsl_project_dir = windows_to_wsl_path(PROJECT_ROOT)
    cmd = (
        f"cd {wsl_project_dir} && "
        "nohup python3 server.py > /tmp/sdtmig_backend.log 2>&1 &"
    )

    print("[后端] 正在通过 WSL 启动 server.py ...")
    result = subprocess.run(
        ["wsl", "-e", "bash", "-lc", cmd],
        capture_output=True,
        text=True,
        shell=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "后端启动命令执行失败：\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def ensure_frontend_deps(node_exe: str, npm_cmd: str) -> None:
    vite_bin = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    if vite_bin.exists():
        return

    if os.name != "nt":
        raise RuntimeError(
            "当前环境未检测到前端依赖，且在 WSL 下无法直接执行 npm.cmd 安装。"
            "请先在 Windows 中执行一次 npm install。"
        )

    print("[前端] 未检测到 vite，正在执行 npm install ...")
    env = os.environ.copy()
    env["PATH"] = str(Path(node_exe).parent) + os.pathsep + env.get("PATH", "")
    result = subprocess.run(
        [npm_cmd, "install"],
        cwd=str(FRONTEND_DIR),
        env=env,
        capture_output=True,
        text=True,
        shell=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            "前端依赖安装失败：\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def start_frontend() -> None:
    if is_port_open("127.0.0.1", FRONTEND_PORT):
        print(f"[前端] 端口 {FRONTEND_PORT} 已在监听，跳过启动。")
        return

    if os.name == "nt":
        node_exe = r"C:\Program Files\nodejs\node.exe"
        npm_cmd = r"C:\Program Files\nodejs\npm.cmd"
        if not Path(node_exe).exists():
            node_exe = "node"
        if not Path(npm_cmd).exists():
            npm_cmd = "npm"
    else:
        # WSL 下优先使用 Windows Node 可执行文件
        wsl_node = Path("/mnt/c/Program Files/nodejs/node.exe")
        node_exe = str(wsl_node) if wsl_node.exists() else "node"
        npm_cmd = "npm"

    ensure_frontend_deps(node_exe, npm_cmd)

    vite_script = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    if not vite_script.exists():
        raise RuntimeError(f"找不到 Vite 启动脚本: {vite_script}")

    print("[前端] 正在启动 Vite 开发服务器 ...")
    env = os.environ.copy()
    env["PATH"] = str(Path(node_exe).parent) + os.pathsep + env.get("PATH", "")

    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS

    log_file = open(FRONTEND_DIR / "vite.log", "a", encoding="utf-8")
    subprocess.Popen(
        [node_exe, str(vite_script), "--host", "0.0.0.0", "--port", str(FRONTEND_PORT)],
        cwd=str(FRONTEND_DIR),
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        shell=False,
        creationflags=creation_flags,
    )


def main() -> int:
    print("== SDTMIG_RAG 一键启动 ==")
    print(f"项目目录: {PROJECT_ROOT}")

    try:
        start_backend()
        start_frontend()
    except Exception as exc:
        print(f"[错误] 启动失败: {exc}")
        return 1

    backend_ok = wait_port("127.0.0.1", BACKEND_PORT, seconds=20)
    frontend_ok = wait_port("127.0.0.1", FRONTEND_PORT, seconds=20)

    print("\n== 启动结果 ==")
    print(f"后端: {'OK' if backend_ok else 'FAILED'}  http://127.0.0.1:{BACKEND_PORT}/")
    print(f"前端: {'OK' if frontend_ok else 'FAILED'}  http://localhost:{FRONTEND_PORT}/")

    if not backend_ok:
        print("后端日志（WSL）: /tmp/sdtmig_backend.log")
    if not frontend_ok:
        print(f"前端日志: {FRONTEND_DIR / 'vite.log'}")

    return 0 if backend_ok and frontend_ok else 2


if __name__ == "__main__":
    sys.exit(main())
