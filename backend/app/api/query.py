import logging
from typing import AsyncGenerator
import uuid
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models import QueryRequest, QueryResponse
from app.graph import rag_graph

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        logger.info(f"Processing query: {request.query}")

        rag_state = {
            "query": request.query,
            "top_k": request.top_k,
            "use_reranker": request.use_reranker,
        }

        result = rag_graph.invoke(rag_state)

        response = QueryResponse(
            query_id=str(uuid.uuid4()),
            query=request.query,
            response=result.get("response", ""),
            citations=result.get("citations", []),
            num_contexts_retrieved=result.get("num_contexts_retrieved", 0),
            num_contexts_used=result.get("num_contexts_used", 0),
            processing_time_ms=result.get("processing_time_ms", 0.0)
        )

        logger.info(f"Query processed successfully in {response.processing_time_ms:.2f}ms")
        return response

    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.post("/query/stream")
async def query_documents_stream(request: QueryRequest):
    try:
        logger.info(f"Processing streaming query: {request.query}")

        async def generate() -> AsyncGenerator[str, None]:
            rag_state = {
                "query": request.query,
                "top_k": request.top_k,
                "use_reranker": request.use_reranker,
            }

            result = rag_graph.invoke(rag_state)

            yield f"data: {{'query_id': '{result.get('query_id', '')}', 'citations': {result.get('citations', [])}}}\n\n"

            for chunk in result.get("response", "").split(" "):
                yield f"data: {{'content': '{chunk} '}}\n\n"

            yield f"data: {{'done': true, 'processing_time_ms': {result.get('processing_time_ms', 0.0)}}}\n\n"

        return StreamingResponse(generate(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Streaming query processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "rag-api"
    }
