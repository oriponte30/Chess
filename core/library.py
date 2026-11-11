"""All the opening lessons, in the order they appear on the Lessons page. To add an opening: write core/lesson_data/<name>.py that builds a
LessonTree (see core/lessons.py for the line format) and add it to LIBRARY below. The Lessons page needs no change."""
from __future__ import annotations

from .lessons import CARO_KANN, LessonTree
from .lesson_data.anti_sicilian import ANTI_SICILIAN
from .lesson_data.italian import ITALIAN
from .lesson_data.london import LONDON
from .lesson_data.queens_gambit import QUEENS_GAMBIT
from .lesson_data.sicilian import SICILIAN
from .lesson_data.vienna import VIENNA

LIBRARY: list = [ITALIAN, VIENNA, LONDON, QUEENS_GAMBIT, CARO_KANN, SICILIAN, ANTI_SICILIAN]
BY_SLUG: dict = {t.slug: t for t in LIBRARY}


def get(slug: str | None) -> LessonTree:
    """The lesson with this slug (the first one when the slug is unknown)."""
    return BY_SLUG.get(slug or "", LIBRARY[0])
