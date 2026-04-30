from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

try:
    from .config import PipelineConfig
except ImportError:
    from config import PipelineConfig


def extract_text(pdf_path: str, config: PipelineConfig) -> list[dict]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    loader = PyPDFLoader(str(path))
    pages = loader.load()

    raw_pages = []
    for page in pages:
        raw_pages.append(
            {
                "page_number": page.metadata.get("page", 0),
                "content": page.page_content,
            }
        )

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.pdf_chunk_size,
        chunk_overlap=config.pdf_chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )

    chunks = []
    for page in raw_pages:
        page_chunks = splitter.split_text(page["content"])
        for chunk in page_chunks:
            chunks.append(
                {
                    "page_number": page["page_number"],
                    "content": chunk.strip(),
                }
            )

    return chunks


def load_full_text(pdf_path: str) -> str:
    path = Path(pdf_path)
    loader = PyPDFLoader(str(path))
    pages = loader.load()
    return "\n\n".join(p.page_content for p in pages)
