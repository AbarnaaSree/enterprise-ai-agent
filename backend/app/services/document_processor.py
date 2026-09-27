from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def load_document(file_path: str) -> str:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    return path.read_text(encoding="utf-8")


def create_chunks(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    document_name: str = "unknown",
) -> list[Document]:

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=[
            "\n\n",
            "\n",
            ". ",
            " ",
            "",
        ],
    )

    chunks = splitter.split_text(text)

    return [
        Document(
            page_content=chunk,
            metadata={
                "document": document_name,
                "chunk_id": index,
            },
        )
        for index, chunk in enumerate(chunks)
    ]