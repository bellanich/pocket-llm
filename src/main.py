import logging

from pathlib import Path

from src.chat import chat
from src.describe_image import describe_image
from src.utils import get_image_match, splice_text


def simple_chatbot():
    # Disable MLC LLM logging
    logging.disable(logging.CRITICAL)
    MEMORY = ""

    print("Chatbot: Hello! I'm a multi-modal chatbot. Type something and I'll respond. Type 'exit' to leave the chat.")

    while True:
        user_input = input("\nYou: ")
        image_match = get_image_match(user_input)

        if user_input.lower() == "exit":
            print("\nChatbot: Goodbye! Have a great day!")
            break

        elif image_match:
            image_filepath = image_match.group(0)
            before_image_text, after_image_text = splice_text(user_input, image_match)

            # Edge case of image path doesn't exist
            if not Path(image_filepath).exists():
                response = f"\nChatbot: I couldn't find any image called '{image_filepath}'. Can you double check that it exists?"
                print(response)
                MEMORY += f"User: {user_input}\n\n You: {response}\n"
            else:
                image_description = describe_image(image_filepath)
                llm_prompt = f"{before_image_text} {image_description} {after_image_text}"
                response = chat(f"{MEMORY} {llm_prompt}")
                MEMORY += f"User: {llm_prompt}\n\n You: {response}\n"

        else:
            response = chat(f"{MEMORY} {user_input}")
            MEMORY += f"User: {user_input}\n\n You: {response}\n"


if __name__ == "__main__":
    # TODOs

    # Others items...
    # * Support extracting multiple images from filepath
    # * Center + crop image rather than resizing it

    # RUN
    # python src/main.py 2>/dev/null
    simple_chatbot()
