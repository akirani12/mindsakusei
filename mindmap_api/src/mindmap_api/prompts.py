"""Load and render prompt templates from prompts/ directory."""

from __future__ import annotations

import functools
from pathlib import Path


@functools.lru_cache(maxsize=64)
def _read_template(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_prompt(prompts_dir: Path, name: str, **kwargs: str) -> str:
    """Load ``prompts/{name}.txt`` and format with *kwargs*.

    Template placeholders use Python ``str.format_map`` syntax, e.g. ``{reqcons}``.
    Missing keys are left as-is so partial rendering is safe.
    """
    path = prompts_dir / f"{name}.txt"
    template = _read_template(path)

    class SafeDict(dict):
        def __missing__(self, key: str) -> str:
            return f"{{{key}}}"

    return template.format_map(SafeDict(**kwargs))
