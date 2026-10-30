"""Load and validate the metric catalogue."""
from pathlib import Path

import yaml

CATALOGUE = Path(__file__).resolve().parent.parent / "metrics.yml"


def load_catalogue(path: Path = CATALOGUE) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))["metrics"]


def get_metric(name: str, catalogue: dict | None = None) -> dict:
    catalogue = catalogue or load_catalogue()
    if name not in catalogue:
        raise KeyError(f"Unknown metric '{name}'. Available: {sorted(catalogue)}")
    return catalogue[name]
