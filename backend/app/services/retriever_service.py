from langchain_community.vectorstores import FAISS
from langfuse import observe

from backend.app.services.document_processor import (
    load_document,
    create_chunks,
)

from backend.app.services.embedding_service import (
    SentenceTransformerEmbeddings,
)


class RetrieverService:

    def __init__(self):

        text = load_document(
            "data/documents/company_handbook.txt"
        )

        documents = create_chunks(
            text,
            chunk_size=500,
            chunk_overlap=50,
            document_name="company_handbook.txt",
        )

        embedding_model = (
            SentenceTransformerEmbeddings()
        )

        self.vector_store = FAISS.from_documents(
            documents,
            embedding_model,
        )

    @observe(name="rag_retrieval", as_type="retriever")
    def retrieve(
        self,
        question: str,
        top_k: int = 5,
        distance_threshold: float = 1.4,
    ):
        results = self.vector_store.similarity_search_with_score(
            question,
            k=top_k,
        )

        filtered_results = []

        print("\nDEBUG RAG RETRIEVAL:")
        print("Question:", question)
        print("Top K:", top_k)
        print("Distance threshold:", distance_threshold)
        print("All retrieved chunks:", len(results))

        for document, score in results:
            print(
                "Chunk:",
                document.metadata.get("chunk_id"),
                "Distance:",
                float(score),
            )
            print(
                "Content:",
                document.page_content[:300],
            )
            print("---")

            if score <= distance_threshold:
                filtered_results.append(
                    {
                        "document": document,
                        "score": float(score),
                    }
                )

        print("Filtered chunks:", len(filtered_results))

        return {
            "documents": filtered_results,
            "total_retrieved": len(results),
            "filtered_count": len(filtered_results),
            "top_k": top_k,
            "distance_threshold": distance_threshold,
            "embedding_model": "all-MiniLM-L6-v2",
            "vector_store": "FAISS",
        }