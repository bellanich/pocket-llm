import re
import sys
from io import StringIO

from src.utils import PATTERN, get_image_match, splice_text


def test_get_image_match():
    # Contains image filepath
    assert get_image_match("This is an image: cat.png")
    assert get_image_match("images/test.gif ... what does it look like?")

    # Doesn't contain image filepath
    assert not get_image_match("Hello, World!")
    assert not get_image_match("")


def test_splice_text():
    # GIVEN
    user_input = "Can you describe this image for me 'data/cat.jpg'? I think that it's a cat..."
    match = re.search(PATTERN, user_input)

    # WHEN
    before_image_text, after_image_text = splice_text(user_input=user_input, match=match)

    # THEN
    assert before_image_text == "Can you describe this image for me '"
    assert after_image_text == "'? I think that it's a cat..."
