"""
RAG Tool -- Retrieval Augmented Generation for Document Q&A
=============================================================
Answers natural language questions by retrieving relevant context
from uploaded PDF documents and generating grounded responses.

Pipeline:
  1. User asks a question
  2. DocumentLoader retrieves top-k relevant chunks via MMR
  3. Chunks are formatted as context with source citations
  4. LLM generates an answer grounded in the retrieved context
  5. Returns structured RAGResult with answer, sources, and confidence

Key features:
  * MMR (Maximal Marginal Relevance) for diverse, non-redundant retrieval
  * Relevance threshold filtering (only uses chunks with score > 0.7)
  * Source citation in every answer
  * Confidence scoring based on retrieval quality
  * Hallucination guard: refuses to answer if no relevant context found

Usage:
    from agent.tools.rag_tool import RAGTool

    tool = RAGTool(docs_dir="data/docs")
    result = tool.run("What is the return policy for laptops?")
    print(result.answer)
    print(result.sources)
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from utils.doc_loader import DocumentLoader, RetrievalResult

# Load environment variables
load_dotenv()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_MODEL: str = "llama-3.3-70b-versatile"
DEFAULT_TEMPERATURE: float = 0.1
DEFAULT_N_RESULTS: int = 5
RELEVANCE_THRESHOLD: float = 0.7
MMR_DIVERSITY: float = 0.3


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class RAGResult:
    """Structured result from the RAG tool.

    Attributes:
        success:          Whether the query was answered successfully.
        question:         The original question.
        answer:           The generated answer.
        sources:          List of source citations (filename + page).
        retrieved_chunks: The raw chunk texts that were used as context.
        chunk_scores:     Similarity scores for each retrieved chunk.
        confidence:       Confidence score (0-100) based on retrieval quality.
        execution_time:   Wall-clock time for the full pipeline.
        error:            Error message if something failed.
        n_chunks_used:    Number of chunks that passed relevance threshold.
    """
    success: bool = False
    question: str = ""
    answer: str = ""
    sources: list[str] = field(default_factory=list)
    retrieved_chunks: list[str] = field(default_factory=list)
    chunk_scores: list[float] = field(default_factory=list)
    confidence: int = 0
    execution_time: float = 0.0
    error: str = ""
    n_chunks_used: int = 0


# ---------------------------------------------------------------------------
# System Prompts
# ---------------------------------------------------------------------------

RAG_SYSTEM_PROMPT = """You are a precise and helpful analyst. Answer the user's
question using ONLY the context provided below. Follow these rules strictly:

1. Base your answer ENTIRELY on the provided context. Do not use outside knowledge.
2. If the context contains the answer, provide a clear, detailed response.
3. If the context does NOT contain enough information to answer the question,
   say: "I don't have enough data to answer this confidently based on the
   available documents."
4. Always cite your sources by mentioning which document and section the
   information came from.
5. Use specific numbers, dates, and facts from the context when available.
6. Structure your answer clearly with key points.
7. If different parts of the context contain conflicting information, mention
   both perspectives and note the discrepancy.

CONTEXT:
{context}

SOURCE DOCUMENTS:
{sources}
"""

CONFIDENCE_PROMPT = """Based on the retrieved context quality, rate your confidence
in the answer on a scale of 0-100:
- 90-100: Context directly and completely answers the question with specific data
- 70-89: Context mostly answers the question with good supporting evidence
- 50-69: Context partially answers the question, some inference needed
- 30-49: Context is tangentially related, significant gaps
- 0-29: Context is barely relevant, answer is mostly uncertain

Question: {question}
Number of relevant chunks: {n_chunks}
Average similarity score: {avg_score:.2f}
Best similarity score: {best_score:.2f}

Respond with ONLY a single integer (0-100), nothing else."""


# ---------------------------------------------------------------------------
# RAG Tool class
# ---------------------------------------------------------------------------

class RAGTool:
    """Retrieval-Augmented Generation tool for document-based Q&A.

    Combines vector search (ChromaDB + sentence-transformers) with
    LLM generation (Groq) to answer questions grounded in uploaded
    documents.

    Args:
        docs_dir:             Directory containing PDF documents.
        vectorstore_dir:      Directory for ChromaDB persistent storage.
        model:                Groq LLM model identifier.
        temperature:          LLM temperature for generation.
        n_results:            Number of chunks to retrieve.
        relevance_threshold:  Minimum similarity score for chunks.
        mmr_diversity:        MMR diversity factor (0=max diversity, 1=max relevance).
        auto_load:            If True, automatically load PDFs on init.
        verbose:              If True, print progress messages.
    """

    def __init__(
        self,
        docs_dir: str | Path = "data/docs",
        vectorstore_dir: str | Path = "vectorstore",
        model: str = DEFAULT_MODEL,
        temperature: float = DEFAULT_TEMPERATURE,
        n_results: int = DEFAULT_N_RESULTS,
        relevance_threshold: float = RELEVANCE_THRESHOLD,
        mmr_diversity: float = MMR_DIVERSITY,
        auto_load: bool = True,
        verbose: bool = True,
    ) -> None:
        self.docs_dir = Path(docs_dir)
        self.model = model
        self.temperature = temperature
        self.n_results = n_results
        self.relevance_threshold = relevance_threshold
        self.mmr_diversity = mmr_diversity
        self.verbose = verbose

        # Initialize LLM
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key.startswith("gsk_your"):
            raise ValueError(
                "GROQ_API_KEY is not set. "
                "Get a free key at https://console.groq.com/keys"
            )

        self._llm = ChatGroq(
            model=model,
            temperature=temperature,
            api_key=api_key,
            max_tokens=2048,
        )

        # Initialize document loader
        self._loader = DocumentLoader(
            persist_dir=str(vectorstore_dir),
            collection_name="documents",
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=500,
            chunk_overlap=50,
            verbose=verbose,
        )

        # Auto-load documents if directory exists
        if auto_load and self.docs_dir.exists():
            pdf_files = list(self.docs_dir.glob("*.pdf"))
            if pdf_files and self._loader.chunk_count == 0:
                self._log("Auto-loading PDF documents ...")
                self._loader.load_directory(self.docs_dir)

    # -- Private helpers -------------------------------------------------------

    def _log(self, msg: str) -> None:
        """Print a message if verbose mode is enabled."""
        if self.verbose:
            print(f"  [RAG Tool] {msg}")

    def _format_context(self, retrieval: RetrievalResult) -> tuple[str, str]:
        """Format retrieved chunks into context and source strings.

        Args:
            retrieval: The retrieval result from DocumentLoader.

        Returns:
            A tuple of (context_string, sources_string).
        """
        context_parts: list[str] = []
        source_set: set[str] = set()

        for i, (chunk, score) in enumerate(
            zip(retrieval.chunks, retrieval.scores), start=1
        ):
            source = chunk.metadata.get("source", "Unknown")
            page = chunk.metadata.get("page", "?")
            source_label = f"{source} (p.{page})"
            source_set.add(source_label)

            context_parts.append(
                f"[Chunk {i}] (Source: {source_label}, Relevance: {score:.2f})\n"
                f"{chunk.text}"
            )

        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."
        sources = "\n".join(f"  - {s}" for s in sorted(source_set)) if source_set else "None"

        return context, sources

    def _compute_confidence(
        self,
        question: str,
        retrieval: RetrievalResult,
    ) -> int:
        """Compute a confidence score for the answer.

        Uses a heuristic based on retrieval quality metrics,
        with LLM-based refinement.

        Args:
            question:  The user's question.
            retrieval: The retrieval results.

        Returns:
            Confidence score from 0 to 100.
        """
        if not retrieval.scores:
            return 0

        avg_score = sum(retrieval.scores) / len(retrieval.scores)
        best_score = max(retrieval.scores)
        n_chunks = len(retrieval.chunks)

        # Heuristic confidence calculation
        # Base: average similarity * 100
        base_confidence = avg_score * 100

        # Bonus for having multiple relevant chunks
        chunk_bonus = min(n_chunks * 5, 20)  # up to +20

        # Bonus for high best score
        best_bonus = (best_score - 0.7) * 50 if best_score > 0.7 else 0

        confidence = int(min(100, base_confidence + chunk_bonus + best_bonus))

        # Try LLM-based refinement for more nuanced scoring
        try:
            prompt = CONFIDENCE_PROMPT.format(
                question=question,
                n_chunks=n_chunks,
                avg_score=avg_score,
                best_score=best_score,
            )
            response = self._llm.invoke([HumanMessage(content=prompt)])
            llm_confidence = int(response.content.strip())
            # Average heuristic and LLM scores
            confidence = (confidence + llm_confidence) // 2
        except (ValueError, Exception):
            pass  # Fall back to heuristic

        return max(0, min(100, confidence))

    # -- Public API ------------------------------------------------------------

    def run(self, question: str) -> RAGResult:
        """Answer a question using RAG pipeline.

        Pipeline:
          1. Retrieve relevant chunks via MMR from ChromaDB
          2. Filter by relevance threshold
          3. Generate answer using LLM with retrieved context
          4. Compute confidence score
          5. Return structured result with citations

        Args:
            question: A natural language question about the documents.

        Returns:
            A RAGResult with answer, sources, confidence, and metadata.
        """
        start = time.time()
        result = RAGResult(question=question)

        self._log(f"Question: {question}")

        # -- Step 1: Retrieve relevant chunks --
        try:
            retrieval = self._loader.query_mmr(
                query_text=question,
                n_results=self.n_results,
                relevance_threshold=self.relevance_threshold,
                diversity_factor=self.mmr_diversity,
            )
        except Exception as e:
            result.error = f"Retrieval failed: {e}"
            result.execution_time = time.time() - start
            self._log(f"[FAIL] Retrieval error: {e}")
            return result

        self._log(f"Retrieved {retrieval.n_relevant} relevant chunks "
                   f"(of {self.n_results} requested)")

        # -- Step 2: Hallucination guard --
        if retrieval.n_relevant == 0:
            result.success = True
            result.answer = (
                "I don't have enough data to answer this confidently. "
                "The uploaded documents don't appear to contain information "
                "relevant to your question. Please try rephrasing or check "
                "if the relevant document has been uploaded."
            )
            result.confidence = 0
            result.execution_time = time.time() - start
            self._log("No relevant chunks found -- hallucination guard triggered")
            return result

        # Store retrieval info
        result.retrieved_chunks = [c.text for c in retrieval.chunks]
        result.chunk_scores = retrieval.scores
        result.n_chunks_used = retrieval.n_relevant

        # Build source citations
        for chunk in retrieval.chunks:
            source = chunk.metadata.get("source", "Unknown")
            page = chunk.metadata.get("page", "?")
            citation = f"{source} (page {page})"
            if citation not in result.sources:
                result.sources.append(citation)

        # -- Step 3: Generate answer --
        try:
            context, sources = self._format_context(retrieval)
            system_prompt = RAG_SYSTEM_PROMPT.format(
                context=context,
                sources=sources,
            )

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=question),
            ]

            response = self._llm.invoke(messages)
            result.answer = response.content
            result.success = True
            self._log("[OK] Answer generated")

        except Exception as e:
            result.error = f"Generation failed: {e}"
            result.execution_time = time.time() - start
            self._log(f"[FAIL] Generation error: {e}")
            return result

        # -- Step 4: Compute confidence --
        try:
            result.confidence = self._compute_confidence(question, retrieval)
            self._log(f"Confidence: {result.confidence}%")
        except Exception as e:
            result.confidence = 50  # default if confidence calc fails
            self._log(f"[!] Confidence calculation failed: {e}")

        result.execution_time = time.time() - start
        self._log(f"Total time: {result.execution_time:.2f}s")
        return result

    def load_pdf(self, filepath: str | Path) -> int:
        """Load a new PDF document into the vector store.

        Args:
            filepath: Path to the PDF file.

        Returns:
            Number of chunks added.
        """
        return self._loader.load_pdf(filepath)

    def load_directory(self, dirpath: str | Path) -> int:
        """Load all PDFs from a directory into the vector store.

        Args:
            dirpath: Path to directory with PDF files.

        Returns:
            Total number of chunks added.
        """
        return self._loader.load_directory(dirpath)

    def get_stats(self) -> dict[str, Any]:
        """Get vector store statistics.

        Returns:
            Dict with collection stats.
        """
        return self._loader.get_collection_stats()

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self._loader.clear_collection()
        self._log("Vector store cleared")
