from mlc_llm import MLCEngine
from mlc_llm.serve.config import EngineConfig

from src.constants import LLM_MODEL_URL


def chat(prompt: str) -> str:
    """Use quantized llava one vision model to describe image

    Args:
        image_path (str): local filepath of image

    Returns:
        str: description of image contents
    """

    model = LLM_MODEL_URL
    engine = MLCEngine(
        model,
        mode="local",
        engine_config=EngineConfig(
            prefill_chunk_size=128,
        ),
    )

    # Run chat completion in OpenAI API
    results = ""
    print("\nChatbot: ", end="")
    for response in engine.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        model=model,
        stream=True,
    ):
        for choice in response.choices:
            print(choice.delta.content, end="", flush=True)
            results += choice.delta.content

    print("")
    return results


if __name__ == "__main__":
    # How to generate description of image given its filepath
    llm_prompt = "Can you give me some ideas for last minute Christmas gifts?"
    response = chat(llm_prompt)
    print(response)
