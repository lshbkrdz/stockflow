import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]


class Settings:
    database_path: str = os.getenv("STOCKFLOW_DATABASE", str(BASE_DIR / "backend" / "stockflow.db"))
    demo_username: str = os.getenv("STOCKFLOW_DEMO_USERNAME", "demo@stockflow.dev")
    demo_password: str = os.getenv("STOCKFLOW_DEMO_PASSWORD", "demo1234")
    demo_token: str = os.getenv("STOCKFLOW_DEMO_TOKEN", "stockflow-demo-token")
    cors_origins: list[str] = [
        origin.strip()
        for origin in os.getenv(
            "STOCKFLOW_CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173",
        ).split(",")
        if origin.strip()
    ]


settings = Settings()
