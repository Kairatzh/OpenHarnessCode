"""Structured logging, metrics, and session replay."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


class HarnessLogger:
    """Structured logger for KAIROS Code."""

    def __init__(
        self,
        name: str = "kairos",
        level: str = "info",
        log_dir: str | Path | None = None,
        console_output: bool = True,
    ) -> None:
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(getattr(logging, level.upper(), logging.INFO))
        self._logger.handlers.clear()

        if console_output:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S",
            ))
            self._logger.addHandler(handler)

        if log_dir:
            log_path = Path(log_dir)
            log_path.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(
                log_path / f"kairos_{datetime.now().strftime('%Y%m%d')}.log",
                encoding="utf-8",
            )
            file_handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(file_handler)

    def _log(self, level: str, message: str, **kwargs: Any) -> None:
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **kwargs,
        }
        getattr(self._logger, level)(json.dumps(extra, default=str))

    def info(self, message: str, **kwargs: Any) -> None:
        self._log("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._log("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._log("error", message, **kwargs)
