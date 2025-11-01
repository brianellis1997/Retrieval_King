from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import upload, query

app = FastAPI(
    title="Retrieval King",
    description="RAG Application with DeepSeek OCR and Granite Embeddings",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
