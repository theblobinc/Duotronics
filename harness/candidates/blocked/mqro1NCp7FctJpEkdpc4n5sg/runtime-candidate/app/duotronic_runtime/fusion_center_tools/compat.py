from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CompatibilitySettings:
    nasa_firms_api_key: str | None = os.environ.get("NASA_FIRMS_API_KEY") or None
    cloudflare_api_token: str | None = os.environ.get("CLOUDFLARE_API_TOKEN") or None
    telegram_api_id: int | None = int(os.environ["TELEGRAM_API_ID"]) if os.environ.get("TELEGRAM_API_ID", "").isdigit() else None
    telegram_api_hash: str | None = os.environ.get("TELEGRAM_API_HASH") or None
    otx_api_key: str | None = os.environ.get("OTX_API_KEY") or None
    gdelt_api_base_url: str = os.environ.get("GDELT_API_BASE_URL", "https://api.gdeltproject.org/api/v2")
    fusion_telegram_session_dir: Path = Path(os.environ.get("FUSION_TELEGRAM_SESSION_DIR", "/runtime/data/telegram"))

    @property
    def has_nasa_key(self) -> bool:
        return bool(self.nasa_firms_api_key)

    @property
    def has_telegram_credentials(self) -> bool:
        return bool(self.telegram_api_id and self.telegram_api_hash)

    @property
    def has_otx_key(self) -> bool:
        return bool(self.otx_api_key)


settings = CompatibilitySettings()


class FusionLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("xavi.fusion_center")

    def debug(self, message, *args, **kwargs): self._logger.debug(message, *args, **kwargs)
    def info(self, message, *args, **kwargs): self._logger.info(message, *args, **kwargs)
    def warning(self, message, *args, **kwargs): self._logger.warning(message, *args, **kwargs)
    def error(self, message, *args, **kwargs): self._logger.error(message, *args, **kwargs)
    def exception(self, message, *args, **kwargs): self._logger.exception(message, *args, **kwargs)
    def success(self, message, *args, **kwargs): self._logger.info(message, *args, **kwargs)
    def result_summary(self, **kwargs): self._logger.info("fusion result %s", kwargs)


def get_logger() -> FusionLogger:
    return FusionLogger()
