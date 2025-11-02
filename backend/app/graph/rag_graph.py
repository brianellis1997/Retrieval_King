import logging
import time
from typing import Any, Dict, List
from langgraph.graph import StateGraph, END
from app.services import (
    llm_service,
    embedding_service,
    reranker_service,
    vector_store_service,
)
from app.models import Citation
from app.core import settings

logger = logging.getLogger(__name__)


class RAGState(Dict[str, Any]):
    pass


class RAGGraph:
    def __init__(self):
        self.graph = self._build_graph()
        self.compiled_graph = self.graph.compile()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(RAGState)

        workflow.add_node("classify_query", self.classify_query)
        workflow.add_node("classify_and_rewrite", self.classify_and_rewrite)
        workflow.add_node("rewrite_query", self.rewrite_query)
        workflow.add_node("retrieve_single", self.retrieve_single)
        workflow.add_node("retrieve_parallel", self.retrieve_parallel)
        workflow.add_node("rerank", self.rerank)
        workflow.add_node("generate", self.generate)

        workflow.set_entry_point("classify_query")

        workflow.add_edge("classify_query", "classify_and_rewrite")

        workflow.add_conditional_edges(
            "classify_and_rewrite",
            self.should_rewrite,
            {
                "rewrite": "rewrite_query",
                "direct": "retrieve_single",
            }
        )

        workflow.add_conditional_edges(
            "rewrite_query",
            self.should_use_parallel,
            {
                "parallel": "retrieve_parallel",
                "single": "retrieve_single",
            }
        )

        workflow.add_edge("retrieve_single", "rerank")
        workflow.add_edge("retrieve_parallel", "rerank")
        workflow.add_edge("rerank", "generate")
        workflow.add_edge("generate", END)

        return workflow

    def classify_query(self, state: RAGState) -> RAGState:
        logger.info("Classifying query...")
        state["classification_start_time"] = time.time()
        return state

    def classify_and_rewrite(self, state: RAGState) -> RAGState:
        query = state.get("query", "")
        logger.debug(f"Deciding if query needs rewriting: '{query}'")

        try:
            rewrite_result = llm_service.rewrite_query(query)
            if rewrite_result is None:
                rewrite_result = {}
        except Exception as e:
            logger.warning(f"Query rewriting failed: {e}")
            rewrite_result = {"should_rewrite": False}

        if rewrite_result.get("should_rewrite", False):
            state["should_rewrite"] = True
            state["original_query"] = query
            logger.info("Query marked for rewriting")
        else:
            state["should_rewrite"] = False
            logger.info("Query will be used directly")

        return state

    def should_rewrite(self, state: RAGState) -> str:
        if state.get("should_rewrite", False):
            return "rewrite"
        else:
            return "direct"

    def rewrite_query(self, state: RAGState) -> RAGState:
        logger.info("Rewriting query...")
        query = state.get("original_query", state.get("query", ""))

        rewrite_result = llm_service.rewrite_query(query)
        rewritten_queries = rewrite_result.get("rewritten_queries", [])

        if rewritten_queries:
            state["query_variants"] = rewritten_queries
            state["num_query_variants"] = len(rewritten_queries)
            logger.info(f"Generated {len(rewritten_queries)} query variants")
        else:
            state["query_variants"] = [query]
            state["num_query_variants"] = 1

        return state

    def should_use_parallel(self, state: RAGState) -> str:
        num_variants = state.get("num_query_variants", 1)

        if num_variants > 1:
            logger.info("Using parallel retrieval for multiple query variants")
            return "parallel"
        else:
            logger.info("Using single retrieval")
            return "single"

    def retrieve_single(self, state: RAGState) -> RAGState:
        logger.info("Performing single retrieval...")
        query = state.get("query", "")

        try:
            query_embedding = embedding_service.embed_query(query)
            if query_embedding is None:
                raise ValueError("Query embedding returned None")

            retrieved_docs = vector_store_service.search(
                query_embedding.tolist(),
                top_k=settings.RETRIEVAL_TOP_K
            )

            if retrieved_docs is None:
                retrieved_docs = []

            state["all_retrieved_documents"] = retrieved_docs if isinstance(retrieved_docs, list) else []
            state["num_contexts_retrieved"] = len(state["all_retrieved_documents"])

            logger.info(f"Retrieved {len(state['all_retrieved_documents'])} documents")
        except Exception as e:
            logger.warning(f"Retrieval failed: {e}, continuing with empty results")
            state["all_retrieved_documents"] = []
            state["num_contexts_retrieved"] = 0

        return state

    def retrieve_parallel(self, state: RAGState) -> RAGState:
        logger.info("Performing parallel retrieval...")
        query_variants = state.get("query_variants", [])

        all_docs = []
        seen_ids = set()

        try:
            for variant in query_variants:
                logger.debug(f"Retrieving for variant: '{variant}'")
                query_embedding = embedding_service.embed_query(variant)
                if query_embedding is None:
                    logger.warning(f"Query embedding returned None for variant: '{variant}'")
                    continue

                retrieved_docs = vector_store_service.search(
                    query_embedding.tolist(),
                    top_k=settings.RETRIEVAL_TOP_K
                )

                if retrieved_docs is None:
                    retrieved_docs = []

                for doc in retrieved_docs:
                    doc_id = doc.get("metadata", {}).get("chunk_id")
                    if doc_id not in seen_ids:
                        all_docs.append(doc)
                        seen_ids.add(doc_id)
        except Exception as e:
            logger.warning(f"Parallel retrieval failed: {e}, using retrieved documents so far")

        logger.info(f"Retrieved {len(all_docs)} unique documents from parallel retrieval")
        state["all_retrieved_documents"] = all_docs
        state["num_contexts_retrieved"] = len(all_docs)

        return state

    def rerank(self, state: RAGState) -> RAGState:
        logger.info("Reranking retrieved documents...")
        documents = state.get("all_retrieved_documents", [])
        query = state.get("query", "")
        use_reranker = state.get("use_reranker", True)

        if not use_reranker or len(documents) == 0:
            state["final_documents"] = documents[:settings.RERANK_TOP_K]
            state["num_contexts_used"] = len(state["final_documents"])
            logger.info(f"Using top {len(state['final_documents'])} documents without reranking")
            return state

        try:
            docs_with_metadata = [
                {
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "similarity_score": doc["similarity_score"]
                }
                for doc in documents
            ]

            reranked = reranker_service.rerank_with_metadata(
                query,
                docs_with_metadata,
                top_k=settings.RERANK_TOP_K
            )

            final_documents = [
                {
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "rerank_score": score,
                    "similarity_score": doc.get("similarity_score", 0)
                }
                for doc, score in reranked
            ]

            state["final_documents"] = final_documents
            state["num_contexts_used"] = len(final_documents)
            logger.info(f"Reranked to {len(final_documents)} final documents")

        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
            state["final_documents"] = documents[:settings.RERANK_TOP_K]
            state["num_contexts_used"] = len(state["final_documents"])

        return state

    def generate(self, state: RAGState) -> RAGState:
        logger.info("Generating response...")
        query = state.get("query", "")
        final_documents = state.get("final_documents", [])

        if not final_documents:
            state["response"] = "I couldn't find any relevant documents to answer your question."
            state["citations"] = []
            return state

        contexts = [doc["text"] for doc in final_documents]

        try:
            response = llm_service.generate_response(
                query,
                contexts,
                use_inline_citations=True
            )

            citations = []
            for idx, doc in enumerate(final_documents):
                citations.append(
                    Citation(
                        citation_id=idx + 1,
                        document_id=doc["metadata"].get("document_id", ""),
                        filename=doc["metadata"].get("filename", ""),
                        chunk_id=doc["metadata"].get("chunk_id", ""),
                        text=doc["text"],
                        page_number=doc["metadata"].get("page_number"),
                        confidence_score=doc.get("rerank_score", doc.get("similarity_score", 0.0))
                    )
                )

            state["response"] = response
            state["citations"] = citations
            logger.info(f"Generated response with {len(citations)} citations")

        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            state["response"] = f"Error generating response: {str(e)}"
            state["citations"] = []

        return state

    def invoke(self, state: RAGState) -> RAGState:
        logger.info(f"Starting RAG pipeline for query: {state.get('query', '')}")
        start_time = time.time()

        result = self.compiled_graph.invoke(state)

        elapsed_time = time.time() - start_time
        result["processing_time_ms"] = elapsed_time * 1000

        logger.info(f"RAG pipeline completed in {elapsed_time:.2f}s")
        return result


rag_graph = RAGGraph()
