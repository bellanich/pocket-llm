from __future__ import annotations

import os
import re
import sys
from typing import Match, Tuple

from src.constants import IMAGE_FILE_EXTENSIONS

PATTERN = r"\b\S+\.(?:" + "|".join(ext[1:] for ext in IMAGE_FILE_EXTENSIONS) + r")\b"


def get_image_match(user_input: str) -> Match[str] | None:
    return re.search(PATTERN, user_input)


def splice_text(user_input: str, match: Match[str] | None) -> Tuple[str, str]:
    if match:
        before_image = user_input[: match.start()].strip()
        after_image = user_input[match.end() :].strip()
        return before_image, after_image
    else:
        return user_input, None
