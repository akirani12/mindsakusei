"""Light validation – observe & log, don't block (except fatal)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def check_keywords_count(csv: str, *, request_id: str, max_expected: int = 10) -> None:
    """Log a warning if KW output exceeds *max_expected* items."""
    items = [k.strip() for k in csv.split(",") if k.strip()]
    if len(items) > max_expected:
        logger.warning(
            "KW returned %d keywords (expected <=%d)",
            len(items),
            max_expected,
            extra={"request_id": request_id},
        )


def check_min_items(text: str, *, min_expected: int, step_name: str, request_id: str) -> None:
    """Log a warning if a bullet-list output has fewer than *min_expected* lines."""
    lines = [ln for ln in text.splitlines() if ln.strip().startswith(("-", "・", "●", "【"))]
    if len(lines) < min_expected:
        logger.warning(
            "%s returned %d items (expected >=%d)",
            step_name,
            len(lines),
            min_expected,
            extra={"request_id": request_id},
        )


def check_not_empty(text: str, *, step_name: str, request_id: str) -> bool:
    """Return False and log error if output is empty."""
    if not text.strip():
        logger.error(
            "%s returned empty output",
            step_name,
            extra={"request_id": request_id},
        )
        return False
    return True
