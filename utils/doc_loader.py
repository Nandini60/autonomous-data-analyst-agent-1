"""
Document Loader -- PDF Parsing, Chunking, Embedding & ChromaDB
================================================================
Handles the full document ingestion pipeline:
  1. Parse PDFs using pdfplumber (extracts text page-by-page)
  2. Chunk text with configurable size and overlap
  3. Embed chunks using sentence-transformers (all-MiniLM-L6-v2)
  4. Store in ChromaDB with document metadata

Usage:
    from utils.doc_loader import DocumentLoader

    loader = DocumentLoader()
    loader.load_directory("data/docs")          # ingest all PDFs
    loader.load_pdf("path/to/report.pdf")       # ingest single PDF

    # Query (used internally by RAG tool)
    results = loader.query("What is the return policy?", n_results=5)
"""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import chromadb
import pdfplumber
from chromadb.config import Settings as ChromaSettings


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_CHUNK_SIZE: int = 500       # characters per chunk
DEFAULT_CHUNK_OVERLAP: int = 50     # overlap between consecutive chunks
DEFAULT_COLLECTION: str = "documents"
DEFAULT_PERSIST_DIR: str = "vectorstore"
DEFAULT_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
DEFAULT_N_RESULTS: int = 5
RELEVANCE_THRESHOLD: float = 0.7    # minimum similarity score


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class DocumentChunk:
    """A single chunk of text extracted from a document.

    Attributes:
        text:        The chunk text content.
        metadata:    Dict with source filename, page number, chunk index, etc.
        chunk_id:    Unique identifier for this chunk (hash-based).
    """
    text: str
    metadata: dict[str, Any]
    chunk_id: str = ""

    def __post_init__(self) -> None:
        if not self.chunk_id:
            # Deterministic ID based on content + source
            hash_input = f"{self.metadata.get('source', '')}__{self.text[:100]}"
            self.chunk_id = hashlib.md5(hash_input.encode()).hexdigest()


@dataclass
class RetrievalResult:
    """Result from a vector store query.

    Attributes:
        chunks:     List of retrieved DocumentChunks.
        scores:     Corresponding similarity scores (0-1, higher = more similar).
        query:      The original query string.
        n_results:  Number of results requested.
        n_relevant: Number of results passing the relevance threshold.
    """
    chunks: list[DocumentChunk] = field(default_factory=list)
    scores: list[float] = field(default_factory=list)
    query: str = ""
    n_results: int = 0
    n_relevant: int = 0


# ---------------------------------------------------------------------------
# PDF Parsing
# ---------------------------------------------------------------------------

def parse_pdf(filepath: str | Path) -> list[dict[str, Any]]:
    """Extract text from a PDF file page-by-page using pdfplumber.

    Args:
        filepath: Path to the PDF file.

    Returns:
        A list of dicts, each with keys:
          - ``text``: Extracted text from the page.
          - ``page``: 1-indexed page number.
          - ``source``: Filename of the PDF.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError:        If no text could be extracted.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"PDF not found: {filepath}")

    pages: list[dict[str, Any]] = []

    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if text and text.strip():
                # Clean up extracted text
                text = _clean_text(text)
                pages.append({
                    "text": text,
                    "page": i,
                    "source": filepath.name,
                    "source_path": str(filepath),
                })

    if not pages:
        raise ValueError(f"No text could be extracted from: {filepath}")

    return pages


def _clean_text(text: str) -> str:
    """Clean extracted PDF text.

    Removes excessive whitespace, fixes line-break artifacts,
    and normalizes Unicode characters.

    Args:
        text: Raw extracted text.

    Returns:
        Cleaned text string.
    """
    # Replace multiple spaces with single space
    text = re.sub(r" {2,}", " ", text)
    # Fix broken words across lines (hyphenated line breaks)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Replace single newlines within paragraphs with spaces
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    # Normalize multiple newlines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Text Chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    metadata: Optional[dict[str, Any]] = None,
) -> list[DocumentChunk]:
    """Split text into overlapping chunks.

    Uses a sentence-aware splitting strategy: tries to break at sentence
    boundaries (periods, question marks, exclamation marks) to avoid
    cutting mid-sentence.

    Args:
        text:          The text to chunk.
        chunk_size:    Maximum characters per chunk.
        chunk_overlap: Number of characters to overlap between chunks.
        metadata:      Base metadata to attach to each chunk.

    Returns:
        A list of DocumentChunk objects.
    """
    if not text or not text.strip():
        return []

    metadata = metadata or {}
    chunks: list[DocumentChunk] = []

    # Split into sentences first for cleaner chunk boundaries
    sentences = _split_sentences(text)

    current_chunk = ""
    chunk_idx = 0

    for sentence in sentences:
        # If adding this sentence would exceed chunk_size, finalize current chunk
        if current_chunk and len(current_chunk) + len(sentence) + 1 > chunk_size:
            chunk_meta = {
                **metadata,
                "chunk_index": chunk_idx,
                "chunk_size": len(current_chunk),
            }
            chunks.append(DocumentChunk(text=current_chunk.strip(), metadata=chunk_meta))
            chunk_idx += 1

            # Create overlap by keeping the end of the current chunk
            if chunk_overlap > 0 and len(current_chunk) > chunk_overlap:
                # Find a sentence boundary within the overlap region
                overlap_text = current_chunk[-chunk_overlap:]
                # Try to start at a sentence boundary
                period_pos = overlap_text.find(". ")
                if period_pos != -1:
                    current_chunk = overlap_text[period_pos + 2:]
                else:
                    current_chunk = overlap_text
            else:
                current_chunk = ""

        # Add sentence to current chunk
        if current_chunk:
            current_chunk += " " + sentence
        else:
            current_chunk = sentence

    # Don't forget the last chunk
    if current_chunk.strip():
        chunk_meta = {
            **metadata,
            "chunk_index": chunk_idx,
            "chunk_size": len(current_chunk),
        }
        chunks.append(DocumentChunk(text=current_chunk.strip(), metadata=chunk_meta))

    return chunks


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences using regex.

    Handles common abbreviations and decimal numbers to avoid
    false splits.

    Args:
        text: Input text.

    Returns:
        A list of sentence strings.
    """
    # Split on sentence-ending punctuation followed by space + capital letter
    # or end of string, but not on abbreviations like "Mr.", "Dr.", "vs.", etc.
    sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])'
    sentences = re.split(sentence_pattern, text)
    # Filter out empty sentences
    return [s.strip() for s in sentences if s.strip()]


# ---------------------------------------------------------------------------
# Document Loader (main class)
# ---------------------------------------------------------------------------

class DocumentLoader:
    """End-to-end document ingestion and retrieval pipeline.

    Handles PDF parsing, chunking, embedding, and ChromaDB storage.
    Uses sentence-transformers for embeddings and ChromaDB for vector
    storage with persistent disk-backed collections.

    Args:
        persist_dir:      Directory for ChromaDB persistent storage.
        collection_name:  Name of the ChromaDB collection.
        embedding_model:  Sentence-transformers model name.
        chunk_size:       Maximum characters per chunk.
        chunk_overlap:    Overlap between consecutive chunks.
        verbose:          If True, print progress messages.
    """

    def __init__(
        self,
        persist_dir: str | Path = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
        verbose: bool = True,
    ) -> None:
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.verbose = verbose

        # Initialize embedding model
        self._log("Loading embedding model ...")
        self._embedding_fn = self._create_embedding_function()
        self._log(f"  Model: {embedding_model}")

        # Initialize ChromaDB client
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self.persist_dir),
        )

        # Get or create collection
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )
        self._log(f"  Collection '{collection_name}': {self._collection.count()} chunks")

    # -- Private helpers -------------------------------------------------------

    def _log(self, msg: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [Doc Loader] {msg}")

    def _create_embedding_function(self) -> chromadb.EmbeddingFunction:
        """Create a ChromaDB-compatible embedding function.

        Tries sentence-transformers first. Falls back to ChromaDB's
        built-in ONNX-based default embedding function if there is
        a torch/torchvision version conflict.

        Returns:
            A chromadb embedding function instance.
        """
        # Strategy 1: sentence-transformers (preferred)
        try:
            from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
            ef = SentenceTransformerEmbeddingFunction(
                model_name=self.embedding_model_name,
            )
            # Quick smoke test to ensure it actually works
            ef(["test"])
            self._log("  Using SentenceTransformer embeddings")
            return ef
        except Exception as e:
            self._log(f"  SentenceTransformer unavailable ({type(e).__name__}), trying fallback...")

        # Strategy 2: ChromaDB default (ONNX runtime, all-MiniLM-L6-v2)
        try:
            from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
            ef = ONNXMiniLM_L6_V2()
            ef(["test"])
            self._log("  Using ONNX MiniLM-L6-V2 embeddings (fallback)")
            return ef
        except Exception:
            pass

        # Strategy 3: ChromaDB's own default
        try:
            ef = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()
            ef(["test"])
            self._log("  Using ChromaDB default embeddings (fallback)")
            return ef
        except Exception as e2:
            raise RuntimeError(
                f"Could not initialize any embedding function. "
                f"Try: pip install --upgrade torch torchvision sentence-transformers\n"
                f"Original error: {e2}"
            )

    # -- Public API: Ingestion -------------------------------------------------

    def load_pdf(self, filepath: str | Path) -> int:
        """Parse, chunk, embed, and store a single PDF.

        Args:
            filepath: Path to the PDF file.

        Returns:
            Number of chunks added to the vector store.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        filepath = Path(filepath)
        self._log(f"Processing: {filepath.name}")

        # Parse pages
        pages = parse_pdf(filepath)
        self._log(f"  Extracted {len(pages)} pages")

        # Chunk all pages
        all_chunks: list[DocumentChunk] = []
        for page_data in pages:
            page_meta = {
                "source": page_data["source"],
                "source_path": page_data["source_path"],
                "page": page_data["page"],
                "doc_type": "pdf",
            }
            page_chunks = chunk_text(
                page_data["text"],
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                metadata=page_meta,
            )
            all_chunks.extend(page_chunks)

        self._log(f"  Created {len(all_chunks)} chunks")

        if not all_chunks:
            self._log("  No chunks created - skipping")
            return 0

        # Remove existing chunks from same source to avoid duplicates
        self._remove_source(filepath.name)

        # Add to ChromaDB
        self._collection.add(
            ids=[c.chunk_id for c in all_chunks],
            documents=[c.text for c in all_chunks],
            metadatas=[c.metadata for c in all_chunks],
        )

        self._log(f"  Stored {len(all_chunks)} chunks in ChromaDB")
        return len(all_chunks)

    def load_directory(self, dirpath: str | Path) -> int:
        """Load all PDFs from a directory.

        Args:
            dirpath: Path to directory containing PDF files.

        Returns:
            Total number of chunks added across all PDFs.
        """
        dirpath = Path(dirpath)
        if not dirpath.exists():
            raise FileNotFoundError(f"Directory not found: {dirpath}")

        pdf_files = sorted(dirpath.glob("*.pdf"))
        if not pdf_files:
            self._log(f"No PDF files found in {dirpath}")
            return 0

        self._log(f"Found {len(pdf_files)} PDF files in {dirpath}")
        total_chunks = 0

        for pdf_path in pdf_files:
            try:
                n = self.load_pdf(pdf_path)
                total_chunks += n
            except Exception as e:
                self._log(f"  [FAIL] Error loading {pdf_path.name}: {e}")

        self._log(f"Total chunks in collection: {self._collection.count()}")
        return total_chunks

    # -- Public API: Retrieval -------------------------------------------------

    def query(
        self,
        query_text: str,
        n_results: int = DEFAULT_N_RESULTS,
        relevance_threshold: float = RELEVANCE_THRESHOLD,
        where: Optional[dict[str, Any]] = None,
    ) -> RetrievalResult:
        """Query the vector store for relevant document chunks.

        Uses cosine similarity for retrieval. Results below the
        relevance threshold are filtered out.

        ChromaDB returns distances (lower = more similar for cosine).
        We convert to similarity scores: score = 1 - distance.

        Args:
            query_text:          The search query string.
            n_results:           Number of results to retrieve.
            relevance_threshold: Minimum similarity score (0-1).
            where:               Optional ChromaDB where filter.

        Returns:
            A RetrievalResult with chunks, scores, and metadata.
        """
        if self._collection.count() == 0:
            self._log("Collection is empty -- no documents loaded")
            return RetrievalResult(query=query_text)

        # Query ChromaDB
        query_params: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": min(n_results, self._collection.count()),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_params["where"] = where

        results = self._collection.query(**query_params)

        # Parse results
        retrieval = RetrievalResult(query=query_text, n_results=n_results)

        if not results["documents"] or not results["documents"][0]:
            return retrieval

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            # Convert cosine distance to similarity score
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            similarity = 1.0 - (dist / 2.0)

            # Apply relevance threshold
            if similarity >= relevance_threshold:
                chunk = DocumentChunk(text=doc, metadata=meta)
                retrieval.chunks.append(chunk)
                retrieval.scores.append(round(similarity, 4))

        retrieval.n_relevant = len(retrieval.chunks)
        return retrieval

    def query_mmr(
        self,
        query_text: str,
        n_results: int = DEFAULT_N_RESULTS,
        relevance_threshold: float = RELEVANCE_THRESHOLD,
        diversity_factor: float = 0.3,
        where: Optional[dict[str, Any]] = None,
    ) -> RetrievalResult:
        """Query with Maximal Marginal Relevance (MMR) for diverse results.

        MMR balances relevance to the query with diversity among results,
        reducing redundancy in retrieved chunks.

        Algorithm:
          1. Retrieve 3x candidates from vector store.
          2. Greedily select results that maximize:
             MMR = lambda * sim(query, doc) - (1-lambda) * max(sim(doc, selected))

        Args:
          'query_text':          The search query.
          'n_results':           Number of final results to return.
          'relevance_threshold': Minimum similarity score.
          'diversity_factor':    Lambda for MMR (0 = max diversity, 1 = max relevance).
          'where':               Optional ChromaDB where filter dict.

        Returns:
            A RetrievalResult with diverse, relevant chunks.
        """
        # Fetch more candidates than needed for MMR selection
        candidates_n = min(n_results * 3, self._collection.count())
        if candidates_n == 0:
            return RetrievalResult(query=query_text)

        # Get candidate results
        query_params: dict[str, Any] = {
            "query_texts": [query_text],
            "n_results": candidates_n,
            "include": ["documents", "metadatas", "distances", "embeddings"],
        }
        if where:
            query_params["where"] = where

        results = self._collection.query(**query_params)

        if not results["documents"] or not results["documents"][0]:
            return RetrievalResult(query=query_text)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        embeddings = results["embeddings"][0] if results.get("embeddings") else None

        # Convert distances to similarities
        similarities = [1.0 - (d / 2.0) for d in distances]

        # If we don't have embeddings for MMR, fall back to standard retrieval
        if embeddings is None:
            self._log("  Embeddings not available -- falling back to standard retrieval")
            return self.query(query_text, n_results, relevance_threshold)

        # MMR selection
        selected_indices: list[int] = []
        candidate_indices = list(range(len(documents)))
        lam = 1.0 - diversity_factor  # higher lambda = more relevance

        while len(selected_indices) < n_results and candidate_indices:
            best_score = -float("inf")
            best_idx = -1

            for idx in candidate_indices:
                # Relevance component
                relevance = similarities[idx]

                # Diversity component: max similarity to already-selected docs
                if selected_indices:
                    max_sim_to_selected = max(
                        _cosine_similarity(embeddings[idx], embeddings[s])
                        for s in selected_indices
                    )
                else:
                    max_sim_to_selected = 0.0

                # MMR score
                mmr_score = lam * relevance - (1 - lam) * max_sim_to_selected

                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = idx

            if best_idx == -1:
                break

            selected_indices.append(best_idx)
            candidate_indices.remove(best_idx)

        # Build result with threshold filtering
        retrieval = RetrievalResult(query=query_text, n_results=n_results)

        for idx in selected_indices:
            sim = similarities[idx]
            if sim >= relevance_threshold:
                chunk = DocumentChunk(text=documents[idx], metadata=metadatas[idx])
                retrieval.chunks.append(chunk)
                retrieval.scores.append(round(sim, 4))

        retrieval.n_relevant = len(retrieval.chunks)
        return retrieval

    # -- Public API: Management ------------------------------------------------

    def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the current collection.

        Returns:
            Dict with chunk count, sources, and collection name.
        """
        count = self._collection.count()
        stats: dict[str, Any] = {
            "collection_name": self.collection_name,
            "total_chunks": count,
            "embedding_model": self.embedding_model_name,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap,
        }

        # Get unique sources
        if count > 0:
            all_data = self._collection.get(include=["metadatas"])
            sources = set()
            for meta in all_data["metadatas"]:
                if meta and "source" in meta:
                    sources.add(meta["source"])
            stats["sources"] = sorted(sources)
            stats["n_sources"] = len(sources)
        else:
            stats["sources"] = []
            stats["n_sources"] = 0

        return stats

    def clear_collection(self) -> None:
        """Delete all documents from the collection."""
        self._client.delete_collection(self.collection_name)
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        self._log("Collection cleared")

    def _remove_source(self, source_name: str) -> None:
        """Remove all chunks from a specific source document.

        Args:
            source_name: The filename to remove chunks for.
        """
        try:
            existing = self._collection.get(
                where={"source": source_name},
                include=[],
            )
            if existing["ids"]:
                self._collection.delete(ids=existing["ids"])
                self._log(f"  Removed {len(existing['ids'])} existing chunks for {source_name}")
        except Exception:
            # Collection might not support where filter yet
            pass

    @property
    def chunk_count(self) -> int:
        """Return the total number of chunks in the collection."""
        return self._collection.count()


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors.

    Args:
        vec_a: First vector.
        vec_b: Second vector.

    Returns:
        Cosine similarity score between -1 and 1.
    """
    import math
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
