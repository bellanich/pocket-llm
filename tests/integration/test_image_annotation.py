from unittest.mock import MagicMock

import pytest
from mlc_llm.serve.engine import ChatCompletion

from src.describe_image import describe_image


@pytest.fixture
def mock_chat_completions(monkeypatch):
    # Create a MagicMock for the response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(delta=MagicMock(content="I see a beautiful, blue-eyed cat.")),
        MagicMock(delta=MagicMock(content=" She has white and gray fur.")),
    ]

    # Return the mocked response in the loop
    def mock_create(*args, **kwargs):
        yield mock_response

    # Patch the `engine.chat.completions.create` with response mock
    monkeypatch.setattr(ChatCompletion, "create", mock_create)


def test_image_description(mock_chat_completions):
    # GIVEN
    image_path = "data/cat.jpg"

    # WHEN
    image_description = describe_image(image_path)

    # THEN
    assert image_description == "I see a beautiful, blue-eyed cat. She has white and gray fur."
