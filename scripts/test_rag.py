from backend.app.services.rag_service import (
    RAGService,
)


rag_service = RAGService()


question = (
    "How many days of annual leave "
    "do employees get?"
)


result = rag_service.answer_question(
    question
)


print("\nQuestion:")
print(question)

print("\nAnswer:")
print(result["answer"])

print("\nSources:")

for index, source in enumerate(
    result["sources"],
    start=1,
):

    document = source["document"]
    score = source["score"]

    print(
        f"\n--- Source {index} ---"
    )

    print(
        "Document:",
        document.metadata["document"],
    )

    print(
        "Chunk ID:",
        document.metadata["chunk_id"],
    )

    print("Text:")
    print(document.page_content)