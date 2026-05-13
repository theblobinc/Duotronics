from __future__ import annotations

import uvicorn

from .api import create_app
from .config import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    import multiprocessing
    workers = max(2, multiprocessing.cpu_count())
    uvicorn.run("duotronic_runtime.main:app", host=settings.app_host, port=settings.app_port, log_level=settings.log_level, workers=workers)


if __name__ == "__main__":
    main()
