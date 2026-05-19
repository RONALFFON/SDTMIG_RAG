import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib import error, request


PROJECT_ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_PORT = 5173
BACKEND_PORT = 5000
BACKEND_URL = f"http://127.0.0.1:{BACKEND_PORT}/"
FRONTEND_URL = f"http://127.0.0.1:{FRONTEND_PORT}/"
BACKEND_LOG_FILE = PROJECT_ROOT / "backend_wsl.log"


def ensure_utf8_stdio() -> None:
    if os.name != "nt":
        return
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


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


def check_http_ok(url: str, timeout: float = 3.0) -> bool:
    try:
        with request.urlopen(url, timeout=timeout) as resp:
            return 200 <= resp.status < 500
    except error.URLError:
        return False


def windows_to_wsl_path(path: Path) -> str:
    drive = path.drive.rstrip(":").lower()
    tail = path.as_posix().split(":/", 1)[1]
    return f"/mnt/{drive}/{tail}"


def run_wsl_bash(command: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["wsl", "-e", "bash", "-lc", command],
        capture_output=True,
        text=True,
        shell=False,
    )


def is_wsl_port_open(port: int) -> bool:
    check_cmd = f"ss -ltn | awk '{{print $4}}' | grep -E ':{port}$' -q"
    result = run_wsl_bash(check_cmd)
    return result.returncode == 0


def start_backend() -> None:
    if is_port_open("127.0.0.1", BACKEND_PORT):
        print(f"[Backend] Port {BACKEND_PORT} already listening, skip start.")
        return

    if is_wsl_port_open(BACKEND_PORT):
        print(f"[Backend] WSL port {BACKEND_PORT} already listening, skip start.")
        return

    wsl_project_dir = windows_to_wsl_path(PROJECT_ROOT)
    start_cmd = (
        f"cd '{wsl_project_dir}' && "
        f"env FLASK_HOST=0.0.0.0 FLASK_PORT={BACKEND_PORT} python3 -m backend.run"
    )

    print("[Backend] Starting backend.run in WSL ...")
    creation_flags = 0
    if os.name == "nt":
        creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    backend_log = open(BACKEND_LOG_FILE, "a", encoding="utf-8")
    subprocess.Popen(
        ["wsl", "-e", "bash", "-lc", start_cmd],
        stdout=backend_log,
        stderr=subprocess.STDOUT,
        shell=False,
        creationflags=creation_flags,
    )

    # 先确认 WSL 内部已经监听，便于区分“启动失败”和“Windows 未映射”。
    if not wait_wsl_port(BACKEND_PORT, seconds=20):
        log_tail = ""
        if BACKEND_LOG_FILE.exists():
            log_tail = "\n".join(BACKEND_LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()[-80:])
        raise RuntimeError(
            "Backend did not listen on WSL port 5000."
            f"\nBackend log:\n{log_tail or '(empty)'}"
        )


def wait_wsl_port(port: int, seconds: int) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if is_wsl_port_open(port):
            return True
        time.sleep(0.5)
    return False


def ensure_frontend_deps(node_exe: str, npm_cmd: str) -> None:
    vite_bin = FRONTEND_DIR / "node_modules" / "vite" / "bin" / "vite.js"
    if vite_bin.exists():
        return

    if os.name != "nt":
        raise RuntimeError(
            "Frontend dependencies are missing and npm.cmd is unavailable in WSL. "
            "Run npm install once in Windows first."
        )

    print("[Frontend] Vite not found, running npm install ...")
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
            "Frontend dependency install failed:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def start_frontend() -> None:
    if is_port_open("127.0.0.1", FRONTEND_PORT):
        print(f"[Frontend] Port {FRONTEND_PORT} already listening, skip start.")
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
        raise RuntimeError(f"Vite startup script not found: {vite_script}")

    print("[Frontend] Starting Vite dev server ...")
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
    ensure_utf8_stdio()
    print("== SDTMIG_RAG One-Click Start ==")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Backend dir: {BACKEND_DIR}")
    print(f"Frontend dir: {FRONTEND_DIR}")

    try:
        start_backend()
        start_frontend()
    except Exception as exc:
        print(f"[Error] Startup failed: {exc}")
        return 1

    backend_port_ok = wait_port("127.0.0.1", BACKEND_PORT, seconds=25)
    frontend_port_ok = wait_port("127.0.0.1", FRONTEND_PORT, seconds=25)
    backend_http_ok = check_http_ok(BACKEND_URL) if backend_port_ok else False
    frontend_http_ok = check_http_ok(FRONTEND_URL) if frontend_port_ok else False
    link_ok = backend_http_ok and frontend_http_ok

    print("\n== Startup Result ==")
    print(f"Backend port: {'OK' if backend_port_ok else 'FAILED'}  {BACKEND_URL}")
    print(f"Frontend port: {'OK' if frontend_port_ok else 'FAILED'}  http://localhost:{FRONTEND_PORT}/")
    print(f"Backend HTTP: {'OK' if backend_http_ok else 'FAILED'}  {BACKEND_URL}")
    print(f"Frontend HTTP: {'OK' if frontend_http_ok else 'FAILED'}  {FRONTEND_URL}")
    print(f"End-to-end link: {'OK' if link_ok else 'FAILED'}")

    if not backend_port_ok:
        print(f"Backend log: {BACKEND_LOG_FILE}")
        if wait_wsl_port(BACKEND_PORT, seconds=1):
            print("Hint: Backend is listening in WSL, but Windows localhost cannot reach it (WSL port forwarding issue).")
    if not frontend_port_ok:
        print(f"Frontend log: {FRONTEND_DIR / 'vite.log'}")

    if not link_ok:
        print("Hint: Verify backend route and frontend page are both reachable.")

    return 0 if link_ok else 2


if __name__ == "__main__":
    sys.exit(main())
