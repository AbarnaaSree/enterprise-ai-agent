from backend.app.services.embedding_service import (
    SentenceTransformerEmbeddings,
)


embedding_model = SentenceTransformerEmbeddings()


texts = [
    "Employees are eligible for 18 days of annual leave.",
    "Employees can work from home up to 2 days per week.",
    "Company credentials must never be stored in plain text.",
]


# Embed documents
document_embeddings = (
    embedding_model.embed_documents(texts)
)

print(
    "Number of texts:",
    len(texts),
)

print(
    "Embedding dimensions:",
    len(document_embeddings[0]),
)


for index, embedding in enumerate(
    document_embeddings,
    start=1,
):

    print(f"\nText {index}:")
    print(texts[index - 1])

    print(
        "First 10 values:",
        embedding[:10],
    )


# Embed query
query = (
    "How many days of annual leave do employees get?"
)

query_embedding = (
    embedding_model.embed_query(query)
)

print("\nQuery:")
print(query)

print(
    "Query embedding dimensions:",
    len(query_embedding),
)