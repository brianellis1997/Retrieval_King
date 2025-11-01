import logging
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from app.models import UploadResponse, DocumentListResponse, DocumentMetadata, DocumentDeleteResponse
from app.services import (
    ocr_service,
    chunking_service,
    embedding_service,
    vector_store_service,
)
from app.core import settings

logger = logging.getLogger(__name__)
router = APIRouter()

document_registry = {}


def process_document(file_path: str, document_id: str, filename: str):
    try:
        logger.info(f"Processing document: {filename}")

        ocr_result = ocr_service.process_document(file_path)
        if not ocr_result["success"]:
            logger.error(f"OCR failed for {filename}: {ocr_result.get('error')}")
            return

        text = ocr_result["text"]

        chunks = chunking_service.chunk_text(text, document_id)

        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = embedding_service.embed_texts(chunk_texts)

        metadata_list = []
        chunk_ids = []
        for chunk in chunks:
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            metadata_list.append({
                "chunk_id": chunk_id,
                "document_id": document_id,
                "filename": filename,
                "chunk_index": chunk["chunk_index"],
                "page_number": chunk.get("page_number"),
                "token_count": chunk["token_count"]
            })

        vector_store_service.add_documents(
            chunk_texts=chunk_texts,
            embeddings=embeddings.tolist(),
            metadatas=metadata_list,
            ids=chunk_ids
        )

        document_registry[document_id] = {
            "filename": filename,
            "file_type": Path(filename).suffix,
            "file_size": Path(file_path).stat().st_size,
            "num_chunks": len(chunks)
        }

        logger.info(f"Successfully processed {filename}, created {len(chunks)} chunks")
        Path(file_path).unlink()

    except Exception as e:
        logger.error(f"Failed to process document {filename}: {e}")
        if Path(file_path).exists():
            Path(file_path).unlink()


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    try:
        document_id = str(uuid.uuid4())
        filename = file.filename

        settings.UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        file_path = settings.UPLOADS_DIR / document_id

        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)

        if background_tasks:
            background_tasks.add_task(process_document, str(file_path), document_id, filename)

        return UploadResponse(
            document_id=document_id,
            filename=filename,
            status="processing",
            num_chunks=0,
            message=f"Document '{filename}' uploaded and is being processed"
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    try:
        documents = []
        for doc_id, doc_info in document_registry.items():
            documents.append(
                DocumentMetadata(
                    id=doc_id,
                    filename=doc_info["filename"],
                    file_type=doc_info["file_type"],
                    file_size=doc_info["file_size"],
                    num_chunks=doc_info["num_chunks"]
                )
            )

        return DocumentListResponse(
            documents=documents,
            total_count=len(documents)
        )
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.delete("/documents/{document_id}", response_model=DocumentDeleteResponse)
async def delete_document(document_id: str):
    try:
        if document_id not in document_registry:
            raise HTTPException(status_code=404, detail=f"Document {document_id} not found")

        vector_store_service.delete_document(document_id)

        del document_registry[document_id]

        return DocumentDeleteResponse(
            document_id=document_id,
            deleted=True,
            message=f"Document {document_id} deleted successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
