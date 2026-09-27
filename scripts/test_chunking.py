from backend.app.services.document_processor import (
    load_document,
    create_chunks,
)


file_path = "data/documents/company_handbook.txt"

text = load_document(file_path)

chunks = create_chunks(
    text,
    chunk_size=300,
    chunk_overlap=50,
    document_name="company_handbook.txt",
)

print(f"Total characters: {len(text)}")
print(f"Total chunks: {len(chunks)}")

for chunk in chunks:

    print(f"\n--- Chunk {chunk.metadata['chunk_id']} ---")

    print(
        "Document:",
        chunk.metadata["document"],
    )

    print("Type:", type(chunk))

    print("Text:")
    print(chunk.page_content)