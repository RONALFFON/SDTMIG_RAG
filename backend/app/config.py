from pathlib import Path

from dotenv import load_dotenv


APP_ROOT = Path(__file__).resolve().parent
BACKEND_ROOT = APP_ROOT.parent
PROJECT_ROOT = BACKEND_ROOT.parent
DATA_ROOT = BACKEND_ROOT / "data"
UPLOAD_ROOT = DATA_ROOT / "uploads"


def load_environment() -> None:
    """Load environment variables from backend-local or project-root .env."""
    for env_path in (BACKEND_ROOT / ".env", PROJECT_ROOT / ".env"):
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=False)


DATA_ROOT.mkdir(parents=True, exist_ok=True)
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
