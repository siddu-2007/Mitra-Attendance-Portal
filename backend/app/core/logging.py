"""Structured Application Logging with Sensitive Data Masking."""

import logging
import re
import sys
from typing import Any

# Patterns to sanitize from log records
SENSITIVE_PATTERNS = [
    (re.compile(r"(Bearer\s+)[A-Za-z0-9\-_.]+", re.IGNORECASE), r"\1[REDACTED_TOKEN]"),
    (re.compile(r"(api[-_]?key\s*[:=]\s*['\"]?)[A-Za-z0-9\-_.]+(['\"]?)", re.IGNORECASE), r"\1[REDACTED_API_KEY]\2"),
    (re.compile(r"(password\s*[:=]\s*['\"]?)[^'\",\s]+(['\"]?)", re.IGNORECASE), r"\1[REDACTED_PASSWORD]\2"),
    (re.compile(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
]


class SensitiveDataFilter(logging.Filter):
    """Logging filter to mask tokens, passwords, and private keys."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        if record.args:
            sanitized_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    sanitized_args.append(self.sanitize(arg))
                else:
                    sanitized_args.append(arg)
            record.args = tuple(sanitized_args)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        for pattern, replacement in SENSITIVE_PATTERNS:
            text = pattern.sub(replacement, text)
        return text


def setup_logger(name: str = "mithra") -> logging.Logger:
    """Configure and return a structured, sanitized logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        logger.addHandler(handler)
        logger.propagate = False
    return logger


logger = setup_logger("mithra_backend")
