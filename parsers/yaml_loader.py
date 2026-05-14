# subtrace/parsers/yaml_loader.py

from __future__ import annotations

import json

from typing import Any

import yaml


def load_structured_data(
    content: str,
) -> Any:
    """
    Safely load JSON or YAML.
    """

    try:
        return json.loads(content)

    except Exception:
        pass

    try:
        return yaml.safe_load(content)

    except Exception:
        return None
