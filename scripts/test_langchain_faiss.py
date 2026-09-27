from backend.app.services.document_processor import (
    load_document,
    create_chunks,
)

from backend.app.services.embedding_service import (
    SentenceTransformerEmbeddings,
)

from langchain_community.vectorstores import FAISS


# 1. Load document
text = load_document(
    "data/documents/company_handbook.txt"
)


# 2. Create LangChain Documents
documents = create_chunks(
    text,
    chunk_size=300,
    chunk_overlap=50,
    document_name="company_handbook.txt",
)

print("Total documents:", len(documents))


# 3. Create embedding model
embedding_model = (
    SentenceTransformerEmbeddings()
)


# 4. Create LangChain FAISS vector store
vector_store = FAISS.from_documents(
    documents,
    embedding_model,
)

print("FAISS vector store created.")


# 5. Create retriever
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={
        "k": 2,
    },
)


# 6. User question
question = (
    "How many days of annual leave do employees get?"
)


# 7. Retrieve relevant documents
results = retriever.invoke(
    question
)


# 8. Display results
print("\nQuestion:")
print(question)

print("\nRetrieved documents:")

for index, document in enumerate(
    results,
    start=1,
):

    print(
        f"\n--- Result {index} ---"
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