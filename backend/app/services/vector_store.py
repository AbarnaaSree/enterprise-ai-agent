import faiss
import numpy as np


class VectorStore:

    def __init__(
        self,
        dimension: int,
    ):

        self.index = faiss.IndexFlatIP(
            dimension
        )

        self.documents = []

    def add(
        self,
        embeddings,
        documents,
    ):

        embeddings = np.asarray(
            embeddings,
            dtype="float32",
        )

        self.index.add(
            embeddings
        )

        self.documents.extend(
            documents
        )

    def search(
        self,
        query_embedding,
        top_k: int = 3,
        score_threshold: float = 0.4,
    ):

        query_embedding = np.asarray(
            query_embedding,
            dtype="float32",
        )

        # FAISS expects shape:
        # (number_of_queries, dimensions)
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(
                1,
                -1,
            )

        scores, indices = self.index.search(
            query_embedding,
            top_k,
        )

        results = []

        for score, index in zip(
            scores[0],
            indices[0],
        ):

            if index == -1:
                continue

            if score < score_threshold:
                continue

            results.append(
                {
                    "document": self.documents[index],
                    "score": float(score),
                }
            )

        return results