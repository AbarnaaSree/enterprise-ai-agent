from langchain_core.prompts import ChatPromptTemplate

from backend.app.services.retriever_service import (
    RetrieverService,
)

from backend.app.services.llm_service import (
    generate_response,
)


class RAGService:

    def __init__(self):

        # 1. Create retriever
        self.retriever_service = (
            RetrieverService()
        )

        # 2. Create RAG prompt
        self.prompt = ChatPromptTemplate.from_template(
            """
You are an enterprise knowledge assistant.

Answer the user's question using ONLY
the provided context.

If the answer cannot be found in the
context, say:

"The information is not available
in the provided documents."

Do not use outside knowledge.

Context:
{context}

Question:
{question}

Answer:
"""
        )

    def answer_question(
        self,
        question: str,
        top_k: int = 3,
    ) -> dict:

        results = self.retriever_service.retrieve(
            question
        )

        if not results:
            return {
                "answer": (
                    "The information is not available "
                    "in the provided documents."
                ),
                "sources": [],
            }

        results = results[:top_k]

        context = "\n\n".join(
            result["document"].page_content
            for result in results
        )

        formatted_prompt = self.prompt.format(
            context=context,
            question=question,
        )

        answer = generate_response(
            formatted_prompt
        )

        return {
            "answer": answer,
            "sources": results,
        }