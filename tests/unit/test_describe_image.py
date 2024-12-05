from src.describe_image import clean_results, describe_image, img_as_str


def test_image_as_str():
    # GIVEN
    image_filepath = "data/cat.jpg"

    # WHEN
    result = img_as_str(image_filepath)

    # THEN
    start_of_str = (
        "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDA"
        "AgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsI"
        "xwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhM"
        "jIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyM"
        "jIyMjIyMjL/wAARCADgAOADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAA"
        "AAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDA"
        "AQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJ"
        "icoKSo0NTY3"
    )
    assert result.startswith(start_of_str)

    end_of_str = (
        "+I1i31v5EpVoxluua6uWCPfJIjEMe4NYmrwrLB8rfMv51diTjLpQboNG"
        "duDyPeuuhu1uNMAI+dVxWCmnyT3ClV3YPJrplhRbdYyoXPoKSA/9k="
    )
    assert result.endswith(end_of_str)


def test_clean_results():
    # GIVEN
    mock_results = (
        "<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
        "Anime uniclit<|im_end|>"
        "<|im_start|>assistant"
    )

    # WHEN
    cleaned_results = clean_results(mock_results)

    # THEN
    assert "<|im_start|>assistant" not in cleaned_results
    assert "<|im_end|>" not in cleaned_results
