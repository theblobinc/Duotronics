from __future__ import annotations

import uvicorn

from .api import create_app
from .config import get_settings

app = create_app()


def main() -> None:
    settings = get_settings()
    # Keep a single worker by default because runtime-side services such as
    # TurboQuantSidecar maintain in-process state. When those indexes move to
    # shared storage, RUNTIME_WORKERS can safely be raised.
    import os
    workers = int(os.environ.get("RUNTIME_WORKERS", "1"))
    uvicorn.run("duotronic_runtime.main:app", host=settings.app_host, port=settings.app_port, log_level=settings.log_level, workers=workers)


if __name__ == "__main__":
    main()
