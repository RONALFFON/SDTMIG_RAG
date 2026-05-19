import os

from backend.app import create_app
from backend.app.config import load_environment


load_environment()

app = create_app()


def main() -> None:
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print("启动 RAG 后端服务...")
    print(f"API 地址: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/api/vector/")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
