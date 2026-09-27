from backend.app.services.retriever_service import (
    RetrieverService,
)


retriever_service = RetrieverService()


question = (
    "How many days of annual leave do employees get?"
)


results = retriever_service.retrieve(
    question
)


print("\nQuestion:")
print(question)

print("\nRetrieved documents:")

for index, result in enumerate(
    results,
    start=1,
):

    document = result["document"]
    score = result["score"]

    print(
        f"\n--- Result {index} ---"
    )

    print(
        "Distance:",
        round(score, 4),
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