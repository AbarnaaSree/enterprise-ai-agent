from backend.app.services.document_processor import (
    load_document,
    create_chunks,
)

from backend.app.services.embedding_service import (
    SentenceTransformerEmbeddings,
)

from backend.app.services.vector_store import (
    VectorStore,
)


# 1. Load document
text = load_document(
    "data/documents/company_handbook.txt"
)


# 2. Create LangChain Documents
chunks = create_chunks(
    text,
    chunk_size=300,
    chunk_overlap=50,
    document_name="company_handbook.txt",
)

print("Total chunks:", len(chunks))


# 3. Create embedding model
embedding_model = (
    SentenceTransformerEmbeddings()
)


# 4. Extract text from Documents
chunk_texts = [
    chunk.page_content
    for chunk in chunks
]


# 5. Embed documents
embeddings = (
    embedding_model.embed_documents(
        chunk_texts
    )
)

print(
    "Embedding dimensions:",
    len(embeddings[0]),
)


# 6. Create vector store
vector_store = VectorStore(
    dimension=len(embeddings[0])
)


# 7. Store vectors + Documents
vector_store.add(
    embeddings,
    chunks,
)


# 8. Create user query
question = (
    "How many days of annual leave do employees get?"
)


# 9. Embed query
query_embedding = (
    embedding_model.embed_query(
        question
    )
)


# 10. Search FAISS
results = vector_store.search(
    query_embedding,
    top_k=2,
)


# 11. Display results
print("\nQuestion:")
print(question)

print("\nRetrieved chunks:")

for index, result in enumerate(
    results,
    start=1,
):

    print(
        f"\n--- Result {index} ---"
    )

    print(
        "Similarity:",
        result["score"],
    )

    document = result["document"]

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