# Retrieval King

A production-ready RAG (Retrieval-Augmented Generation) application featuring advanced document processing with OCR, intelligent embeddings, and real-time query answering with citation tracking.

## Features

- **Advanced OCR Processing**: Uses DeepSeek-OCR (3B model) to extract text from PDFs, images, and scanned documents
- **Intelligent Embeddings**: IBM Granite 30M embedding model (384-dimensional vectors) with 512-token context window
- **Smart Reranking**: IBM Granite Reranker for improved retrieval relevance (8K token context)
- **Conditional Query Rewriting**: Automatically detects complex queries and rewrites them for better retrieval
- **Parallel Retrieval**: Supports multi-query retrieval for complex questions
- **Citation Tracking**: Inline citations with source attribution and confidence scores
- **Full-Stack**: FastAPI backend + React/Vite frontend with drag-and-drop UI
- **Docker Support**: Complete containerization with GPU acceleration

## Architecture

```
┌─────────────────────────────────────────────────────┐
│ Frontend (React + Vite + Tailwind CSS)              │
│ - File upload with drag-and-drop                    │
│ - Real-time chat interface                          │
│ - Document management                               │
│ - Citation popup for source details                 │
└────────────────┬────────────────────────────────────┘
                 │ HTTP/WebSocket
                 ▼
┌─────────────────────────────────────────────────────┐
│ Backend (FastAPI + Python 3.12)                     │
│ ┌──────────────────────────────────────────────┐   │
│ │ Services Layer                               │   │
│ │ - OCR Service (DeepSeek-OCR)                 │   │
│ │ - Embedding Service (Granite 30M)            │   │
│ │ - Reranker Service (Granite Reranker)        │   │
│ │ - Chunking Service (LangChain)               │   │
│ │ - LLM Service (GPT-4o-mini)                  │   │
│ │ - Vector Store (ChromaDB)                    │   │
│ └──────────────────────────────────────────────┘   │
│ ┌──────────────────────────────────────────────┐   │
│ │ LangGraph RAG Workflow                       │   │
│ │ - Query Classification                       │   │
│ │ - Optional Query Rewriting                   │   │
│ │ - Single/Parallel Retrieval                  │   │
│ │ - Reranking                                  │   │
│ │ - Response Generation                        │   │
│ └──────────────────────────────────────────────┘   │
└────────────────┬────────────────────────────────────┘
                 │
    ┌────────────┴──────────────┐
    ▼                           ▼
┌──────────────┐        ┌──────────────┐
│ ChromaDB     │        │ OpenAI API   │
│ (Vector DB)  │        │ (GPT-4o-mini)│
└──────────────┘        └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (optional)
- GPU with CUDA 11.8+ (for OCR, optional but recommended)
- OpenAI API Key

### Local Setup (without Docker)

1. **Clone the repository**
   ```bash
   git clone https://github.com/bdogellis/Retrieval_King.git
   cd Retrieval_King
   ```

2. **Create virtual environment**
   ```bash
   python3.12 -m venv retrieval_king
   source retrieval_king/bin/activate
   ```

3. **Install backend dependencies**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

5. **Install frontend dependencies**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

6. **Run backend**
   ```bash
   source retrieval_king/bin/activate
   cd backend
   uvicorn main:app --reload
   ```

7. **Run frontend** (in a new terminal)
   ```bash
   cd frontend
   npm run dev
   ```

Visit `http://localhost:5173` to access the application.

### Docker Setup

1. **Create .env file**
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

2. **Start services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: `http://localhost:3000`
   - Backend API: `http://localhost:8000`
   - API Docs: `http://localhost:8000/docs`

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | - | Your OpenAI API key (required) |
| `OPENAI_MODEL_QUERY_REWRITER` | `gpt-4o-mini` | Model for query rewriting |
| `OPENAI_MODEL_GENERATOR` | `gpt-4o-mini` | Model for response generation |
| `CHUNK_SIZE` | `450` | Max tokens per chunk (Granite max: 512) |
| `CHUNK_OVERLAP` | `75` | Token overlap between chunks |
| `RETRIEVAL_TOP_K` | `100` | Initial retrieval result count |
| `RERANK_TOP_K` | `10` | Final result count after reranking |
| `DEVICE` | `cuda` | Device for model inference (`cuda` or `cpu`) |
| `DATABASE_PATH` | `./data/chroma` | ChromaDB storage location |
| `UPLOADS_DIR` | `./data/uploads` | Uploaded files storage |
| `MODELS_CACHE_DIR` | `./data/models` | HuggingFace models cache |

## API Endpoints

### Documents

- **POST** `/api/upload` - Upload and process a document
- **GET** `/api/documents` - List all uploaded documents
- **DELETE** `/api/documents/{document_id}` - Delete a document

### Queries

- **POST** `/api/query` - Query the knowledge base
- **POST** `/api/query/stream` - Stream query results
- **GET** `/health` - Health check

### Example Usage

**Upload a document:**
```bash
curl -X POST -F "file=@document.pdf" http://localhost:8000/api/upload
```

**Query the knowledge base:**
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 10, "use_reranker": true}'
```

## Model Details

### DeepSeek-OCR
- **Purpose**: Document-to-text conversion
- **Type**: Vision-Language Model (3B parameters)
- **Capabilities**: PDF, image, and scanned document processing
- **Inference**: GPU required (CUDA)

### IBM Granite Embedding 30M
- **Dimension**: 384
- **Context Window**: 512 tokens (hard limit)
- **Performance**: BEIR score 49.1
- **Speed**: 2x faster than similar models
- **Use**: Document embedding and retrieval

### IBM Granite Reranker
- **Type**: Dense cross-encoder (ModernBERT)
- **Parameters**: 149M
- **Context Window**: 8,192 tokens
- **Performance**: BEIR score 55.8
- **Purpose**: Re-rank retrieval results for improved quality

### GPT-4o-mini
- **Type**: LLM for query rewriting and response generation
- **Query Rewriter**: Fast, optimized for query classification
- **Generator**: Full response generation with citations

## Chunking Strategy

The system uses intelligent chunking with these parameters:

- **Max Chunk Size**: 450 tokens (respects Granite 30M's 512-token limit with buffer)
- **Overlap**: 75 tokens (maintains context continuity)
- **Strategy**: Recursive sentence-aware splitting via LangChain
- **Tokenization**: Uses Granite tokenizer for accurate counting

## Retrieval Pipeline

1. **Query Classification**: Determine if query needs rewriting
2. **Query Rewriting** (optional): Generate query variants for complex questions
3. **Embedding**: Convert query to 384-dimensional vector
4. **Initial Retrieval**: Get top-100 similar documents via cosine similarity
5. **Reranking**: Re-score top-100 using cross-encoder (top-10 final)
6. **Response Generation**: LLM generates answer with inline citations
7. **Citation Tracking**: Link answers to source chunks with confidence scores

## Development

### Project Structure

```
Retrieval_King/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration
│   │   ├── models/         # Pydantic schemas
│   │   ├── services/       # Core RAG services
│   │   ├── graph/          # LangGraph workflow
│   │   └── api/            # FastAPI endpoints
│   ├── main.py             # FastAPI app entry
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── App.tsx         # Main app
│   ├── package.json        # JS dependencies
│   └── Dockerfile
├── docker-compose.yml      # Container orchestration
└── README.md              # This file
```

### Adding a New LLM

1. Update `backend/app/core/config.py` with new model settings
2. Modify `backend/app/services/llm_service.py` to support the new provider
3. Update `.env.example` with new configuration options
4. Update this README with model details

### Extending Components

The architecture supports easy extension:

- **New embedding models**: Swap in `EmbeddingService`
- **Different rerankers**: Replace `RerankerService`
- **Alternative LLMs**: Update `LLMService` with new provider
- **Custom chunking**: Modify `ChunkingService`
- **Different vector stores**: Replace `VectorStoreService`

## Performance Optimization

### Chunking
- Larger chunks = faster retrieval, potentially less precise
- Smaller chunks = slower retrieval, more precise
- Current (450 tokens): Balanced for most use cases

### Retrieval
- Increase `RETRIEVAL_TOP_K` for higher recall, slower reranking
- Decrease for faster but potentially less relevant results
- Reranking adds ~100-200ms but significantly improves quality

### Model Loading
- Models are loaded on first use and cached
- GPU memory: ~8-10GB with all models
- CPU inference slower but no GPU required

## Troubleshooting

### OCR Failures
- Ensure image quality is sufficient
- Check CUDA availability for GPU acceleration
- Verify file format is supported (PDF, PNG, JPG)

### Retrieval Quality
- Check that documents were processed (see Document Manager)
- Verify query is clear and specific
- Try enabling query rewriting for complex questions
- Increase `RETRIEVAL_TOP_K` for broader search

### Memory Issues
- Reduce batch sizes in embedding/reranking services
- Use CPU inference if GPU memory is limited
- Consider using smaller model variants

### API Connection Issues
- Verify backend is running (`http://localhost:8000/health`)
- Check CORS configuration in `backend/main.py`
- Ensure frontend is configured with correct API URL

## Performance Metrics

On typical hardware:

| Operation | Time |
|-----------|------|
| Document Upload (10MB PDF) | 5-30s |
| OCR Processing | 2-10s |
| Chunking & Embedding | 3-5s |
| Query (initial retrieval) | 100-300ms |
| Reranking (top-100) | 100-200ms |
| Response Generation | 1-3s |
| **Total Query Time** | **1.5-3.5s** |

## Future Enhancements

- [ ] Support for more OCR models
- [ ] Multi-language embedding models
- [ ] Hybrid retrieval (BM25 + semantic)
- [ ] Query expansion and decomposition
- [ ] Multi-document summarization
- [ ] Conversation history and context
- [ ] Fine-tuned embedding models
- [ ] GraphRAG for entity relationships
- [ ] Web search integration
- [ ] PDF table extraction

## License

MIT

## Contributing

Contributions are welcome! Please ensure:
- Code follows PEP 8 for Python
- Frontend uses React best practices
- All new services include logging
- Documentation is updated

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the API documentation at `/docs`
3. Check application logs for detailed errors
4. Open an issue on GitHub
