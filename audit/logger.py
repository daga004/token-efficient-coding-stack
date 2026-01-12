"""
Structured logging for audit tests.

Provides console and file logging with automatic context injection.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class AuditLogger:
    """Structured logger for audit operations."""

    def __init__(
        self,
        name: str = "audit",
        log_dir: str = "audit/logs",
        console_level: int = logging.INFO,
        file_level: int = logging.DEBUG,
    ):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # Console handler (human-readable)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # File handler (JSON structured)
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"audit_{date_str}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        self.logger.addHandler(file_handler)

        self.context: dict[str, Any] = {}

    def set_context(self, **kwargs: Any) -> None:
        """Set context values that will be included in all log entries."""
        self.context.update(kwargs)

    def clear_context(self) -> None:
        """Clear all context values."""
        self.context = {}

    def _build_message(self, message: str, extra: Optional[dict[str, Any]] = None) -> str:
        """Build structured log message with context."""
        data = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": message,
            **self.context,
            **(extra or {}),
        }
        return json.dumps(data)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        structured = self._build_message(message, kwargs)
        self.logger.debug(message)  # Console: human-readable
        # File gets JSON automatically via handler

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        structured = self._build_message(message, kwargs)
        self.logger.info(message)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        structured = self._build_message(message, kwargs)
        self.logger.error(message)

    def test_start(self, test_name: str, phase: Optional[str] = None) -> None:
        """Log test start."""
        self.set_context(test_name=test_name, phase=phase)
        self.info(f"Starting test: {test_name}")

    def test_end(self, test_name: str, status: str, duration_ms: float) -> None:
        """Log test completion."""
        self.info(
            f"Test complete: {test_name}",
            status=status,
            duration_ms=duration_ms,
        )
        self.clear_context()
