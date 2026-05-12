from __future__ import annotations

import uvicorn

from .api import create_app
from .config import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    uvicorn.run("duotronic_runtime.main:app", host=settings.app_host, port=settings.app_port, log_level=settings.log_level)


if __name__ == "__main__":
    main()
