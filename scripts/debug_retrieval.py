from backend.app.services.retriever_service import RetrieverService


retriever = RetrieverService()

question = (
    "Tell me Abarnaa's remaining vacation "
    "and the rules for requesting leave."
)

results = retriever.vector_store.similarity_search_with_score(
    question,
    k=3,
)

for document, score in results:

    print("\nDistance:", score)

    print("Document:")
    print(document.metadata)

    print("Text:")
    print(document.page_content)

    print("\n---")