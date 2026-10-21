"""The list of pages. To add a feature: write app_pages/<name>.py (it's an ordinary Streamlit script that can use ui.state, core.store
and core.service) and add one line here. Nothing else needs to change."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    title: str
    icon: str
    path: str                 # relative to app.py
    url: str                  # the page's address, e.g. /training
    default: bool = False


FEATURES = [
    Feature("Game review", "♟️", "app_pages/review.py", "review", default=True),
    Feature("Training", "🎯", "app_pages/training.py", "training"),
    Feature("Insights", "📈", "app_pages/insights.py", "insights"),
]
