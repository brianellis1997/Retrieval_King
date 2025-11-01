from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings
from app.api import upload, query

app = FastAPI(
    title=settings.API_TITLE,
    description="RAG Application with DeepSeek OCR and Granite Embeddings",
    version=settings.API_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.include_router(upload.router, prefix="/api", tags=["documents"])
app.include_router(query.router, prefix="/api", tags=["queries"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
