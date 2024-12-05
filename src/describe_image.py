import base64
from io import BytesIO

from mlc_llm import MLCEngine
from mlc_llm.serve.config import EngineConfig
from PIL import Image

from src.constants import IMAGE_ANNOTATION_LIMIT, VISION_MODEL_URL


# -------------------
#  Helper Functions
# -------------------
def img_as_str(image_path: str) -> str:
    """Load img and convert it into a str

    Args:
        image_path (str): local filepath of image

    Returns:
        str: string as image
    """
    image = Image.open(image_path)
    image = image.resize((224, 224))
    buffered = BytesIO()
    image.save(buffered, format="JPEG")

    img_str = base64.b64encode(buffered.getvalue())
    return "data:image/jpeg;base64," + img_str.decode("ascii")


def clean_results(results: str) -> str:
    tags = ["<|im_start|>assistant", "<|im_end|>"]
    for tag in tags:
        results = results.replace(tag, "")
    return results


# -------------------
#  Main Function
# -------------------
def describe_image(image_path: str) -> str:
    """Use quantized llava one vision model to describe image

    Args:
        image_path (str): local filepath of image

    Returns:
        str: description of image contents
    """
    model = VISION_MODEL_URL
    engine = MLCEngine(
        model,
        mode="local",
        engine_config=EngineConfig(
            prefill_chunk_size=832,
        ),
    )

    # Run chat completion in OpenAI API
    counter, results = 0, ""
    for response in engine.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Annotate the image."},
                    {"type": "image_url", "image_url": img_as_str(image_path)},
                ],
            }
        ],
        model=model,
        stream=True,
    ):
        for choice in response.choices:
            results += choice.delta.content
        # Prevent chat bot from talking too much
        counter += 1
        if counter > IMAGE_ANNOTATION_LIMIT:
            break

    return clean_results(results)
