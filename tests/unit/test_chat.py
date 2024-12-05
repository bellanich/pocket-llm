from unittest.mock import MagicMock

import pytest
from mlc_llm.serve.engine import ChatCompletion

from src.chat import chat


@pytest.fixture
def mock_chat_completions(monkeypatch):
    # Create a MagicMock for the response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(delta=MagicMock(content="I have no idea what you're talking about.")),
        MagicMock(delta=MagicMock(content=" Maybe we can discuss what your next vacation plans are?")),
    ]

    # Return the mocked response in the loop
    def mock_create(*args, **kwargs):
        yield mock_response

    # Patch the `engine.chat.completions.create` with response mock
    monkeypatch.setattr(ChatCompletion, "create", mock_create)


def test_image_description(mock_chat_completions):
    # GIVEN

    # WHEN
    response = chat("Do you believe that general artificial intelligence or knowledge explosion is more likely?")

    # THEN
    assert (
        response == "I have no idea what you're talking about. Maybe we can discuss what your next vacation plans are?"
    )
