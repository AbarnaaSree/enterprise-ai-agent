import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel


load_dotenv()


client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = os.getenv("OPENROUTER_MODEL")


class GroundednessResult(BaseModel):
    grounded: bool
    reason: str
class AnswerabilityResult(BaseModel):
    appropriate: bool
    reason: str

def evaluate_answerability(
    question: str,
    answer: str,
) -> AnswerabilityResult:

    prompt = f"""
You are evaluating whether an AI-generated answer
appropriately handles a question that cannot be answered
using the available authoritative enterprise sources.

Do not use outside knowledge.

Question:
{question}

Generated Answer:
{answer}

Determine whether the response appropriately handles
the question.

A response is appropriate when it correctly recognizes
that the available information is insufficient to answer
the question, or when it asks for information that is
necessary to answer the question.

A response is inappropriate when it:
- invents information,
- provides an unsupported factual answer,
- pretends to have access to information that is not
  available,
- or gives a confident answer without sufficient
  authoritative information.

The response does not need to use any particular phrase.
Evaluate the meaning and behavior of the response.

Return ONLY valid JSON:

{{
    "appropriate": true,
    "reason": "brief explanation"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=300,
        response_format={
            "type": "json_object"
        },
    )

    content = (
        response.choices[0]
        .message
        .content
    )

    if not content:
        raise ValueError(
            "LLM answerability judge returned an empty response."
        )

    try:
        data = json.loads(content)
    except json.JSONDecodeError as error:
        print("\nDEBUG ANSWERABILITY JUDGE RESPONSE:")
        print("Raw content:", repr(content))
        print("JSON error:", error)

        raise ValueError(
            "LLM answerability judge returned invalid JSON."
        ) from error

    try:
        return AnswerabilityResult.model_validate(data)
    except Exception as error:
        print("\nDEBUG ANSWERABILITY JUDGE VALIDATION:")
        print("Parsed data:", data)
        print("Validation error:", error)

        raise ValueError(
            "LLM answerability judge returned an invalid schema."
        ) from error
def evaluate_groundedness(
    question: str,
    answer: str,
    source: str,
) -> GroundednessResult:

    prompt = f"""
You are evaluating whether an AI-generated answer
is supported by an authoritative source.

Do not use outside knowledge.

Question:
{question}

Authoritative Source:
{source}

Generated Answer:
{answer}

Determine whether the generated answer is fully
supported by the authoritative source.

Rules:

1. If the answer is directly supported by the source,
   grounded should be true.

2. Valid paraphrasing is allowed.

3. Rewording or changing sentence structure is allowed.

4. If the answer adds information that is not supported
   by the source, grounded should be false.

5. If the answer contradicts the source, grounded should
   be false.

6. If the source does not contain enough information to
   answer the question, grounded should be false.

Return ONLY valid JSON:

{{
    "grounded": true,
    "reason": "brief explanation"
}}
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        max_tokens=300,
        response_format={
            "type": "json_object"
        },
    )

    content = (
        response.choices[0]
        .message
        .content
    )

    if not content:
        raise ValueError(
            "LLM judge returned an empty response."
        )

    data = json.loads(content)

    return GroundednessResult.model_validate(
        data
    )