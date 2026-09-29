import os
import json

from dotenv import load_dotenv
from openai import OpenAI
from langfuse import observe


load_dotenv()


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


MODEL = os.getenv("OPENROUTER_MODEL")


@observe(name="llm_generate_response")
def generate_response(prompt: str) -> str:

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=450,
    )

    message = response.choices[0].message

    print("\nDEBUG LLM RESPONSE:")
    print("content:", repr(message.content))
    print(
        "finish_reason:",
        response.choices[0].finish_reason,
    )

    if message.content:
        return message.content.strip()

    return ""


@observe(name="llm_generate_structured_response")
def generate_structured_response(prompt: str, response_model):
    max_attempts = 3

    for attempt in range(1, max_attempts + 1):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content

        if not content:
            print(
                f"\nStructured LLM attempt {attempt}/{max_attempts}: "
                "empty response"
            )
            continue

        try:
            data = json.loads(content)

        except json.JSONDecodeError as error:
            print(
                f"\nStructured LLM attempt "
                f"{attempt}/{max_attempts}: invalid JSON"
            )
            print("Raw content:", repr(content))
            print("JSON error:", error)

            if attempt == max_attempts:
                raise ValueError(
                    "LLM returned invalid JSON for structured response "
                    "after multiple attempts."
                ) from error

            continue

        try:
            return response_model.model_validate(data)

        except Exception as error:
            print(
                f"\nStructured LLM attempt "
                f"{attempt}/{max_attempts}: schema validation failed"
            )
            print("Parsed data:", data)
            print("Validation error:", error)

            if attempt == max_attempts:
                raise ValueError(
                    "LLM structured response did not match the expected "
                    "schema after multiple attempts."
                ) from error

            continue

    raise ValueError(
        "LLM failed to produce a valid structured response."
    )