# Retrieval King - Complete Setup Guide

This guide provides step-by-step instructions for getting Retrieval King up and running.

## System Requirements

### Minimum Requirements
- Python 3.12+
- Node.js 18+
- 8GB RAM
- 20GB disk space (for models)

### Recommended (for OCR with GPU)
- NVIDIA GPU with CUDA 11.8+ support
- 16GB+ RAM
- 50GB+ SSD space
- 24GB+ VRAM (A10, A40, L40, or better)

## Step 1: Clone Repository

```bash
git clone https://github.com/bdogellis/Retrieval_King.git
cd Retrieval_King
```

## Step 2: Get OpenAI API Key

1. Go to https://platform.openai.com/account/api-keys
2. Create a new API key
3. Save it securely

## Step 3: Choose Deployment Method

### Option A: Local Development (Recommended for Testing)

#### 3a. Create Python Virtual Environment

```bash
# Create venv with Python 3.12
python3.12 -m venv retrieval_king

# Activate it
source retrieval_king/bin/activate  # On Windows: retrieval_king\Scripts\activate
```

#### 3b. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

**Note**: The first time you run the backend, it will download models (~15-20GB). This may take 10-30 minutes depending on internet speed.

#### 3c. Set Up Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your favorite editor
nano .env  # or use your preferred editor
```

Add your OpenAI API key:
```
OPENAI_API_KEY=sk-your-api-key-here
DEVICE=cuda  # or cpu if no GPU
```

#### 3d. Install Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

#### 3e. Start Backend Server

In one terminal:
```bash
source retrieval_king/bin/activate  # Activate venv
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### 3f. Start Frontend Server

In another terminal:
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.0.0  ready in 234 ms

  ➜  Local:   http://localhost:5173/
```

#### 3g. Access Application

Open http://localhost:5173 in your browser.

---

### Option B: Docker (Recommended for Production)

#### 3b. Set Up Environment Variables

```bash
cp .env.example .env
# Edit .env with your OpenAI API key
nano .env
```

#### 3c. Start with Docker Compose

```bash
docker-compose up --build
```

First run will take time downloading base images and models.

#### 3d. Access Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ChromaDB: http://localhost:8001

#### 3e. Stop Services

```bash
docker-compose down

# Or to also remove data volumes:
docker-compose down -v
```

---

## Step 4: Test the Application

### 4a. Upload a Test Document

1. Go to http://localhost:5173 (or 3000 for Docker)
2. In the "Upload Documents" section, drag and drop or click to select a PDF or image
3. Wait for processing (check "Documents" panel on the right)

### 4b. Ask a Question

1. In the chat interface, type a question about your document
2. Example: "What is the main topic of this document?"
3. Wait for response (1-3 seconds typically)
4. Click on citation numbers to see source chunks

### 4c. Verify Features

- [ ] File upload works
- [ ] Document appears in Documents list
- [ ] Query returns results
- [ ] Citations show correct sources
- [ ] Citation popups display chunk text

---

## Troubleshooting

### Problem: "ModuleNotFoundError"

**Solution**: Ensure venv is activated and all dependencies installed:
```bash
source retrieval_king/bin/activate
pip install -r backend/requirements.txt
```

### Problem: "CUDA out of memory"

**Solution**:
1. Use CPU inference: `DEVICE=cpu` in .env
2. Reduce batch sizes in service files
3. Use GPU with more memory (24GB+ recommended)

### Problem: "Connection refused" when frontend tries to reach backend

**Solution**:
1. Ensure backend is running on correct port
2. Check CORS configuration in `backend/main.py`
3. For Docker: services communicate via `http://backend:8000`
4. For local: services communicate via `http://localhost:8000`

### Problem: Models not downloading

**Solution**:
1. Check internet connection
2. Increase timeout if behind proxy
3. Manually download models:
```python
from sentence_transformers import SentenceTransformer
SentenceTransformer("ibm-granite/granite-embedding-30m-english")
```

### Problem: OCR taking very long

**Solution**:
1. Ensure GPU is available: `nvidia-smi`
2. For CPU-only: Expected 5-10 seconds per page
3. Reduce PDF page count for testing

---

## Configuration Tuning

### For Better Retrieval Quality

Edit `.env`:
```
CHUNK_SIZE=400        # Smaller chunks = more precise
CHUNK_OVERLAP=100     # More overlap = better context
RETRIEVAL_TOP_K=200   # Get more candidates
RERANK_TOP_K=20       # Return more results
```

### For Faster Responses

```
CHUNK_SIZE=500        # Larger chunks = fewer embeddings
CHUNK_OVERLAP=50      # Less overlap
RETRIEVAL_TOP_K=50    # Fewer candidates to rerank
RERANK_TOP_K=5        # Fewer final results
```

### For CPU-Only Systems

```
DEVICE=cpu            # Disable GPU
CHUNK_SIZE=350        # Smaller chunks = faster processing
```

---

## Development Workflow

### Adding a New Embedding Model

1. Update `backend/app/core/config.py`:
```python
EMBEDDING_MODEL: str = "your-new-model"
```

2. Restart backend (models are cached after first load)

### Viewing API Documentation

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Checking Logs

**Backend**:
```bash
# In terminal where backend is running
# All logs appear directly
```

**Frontend**:
```bash
# Browser console (F12 or Cmd+Option+I)
# All API calls logged
```

---

## Data Management

### Viewing Uploaded Documents

Documents are stored in:
```
./data/uploads/          # Raw uploaded files
./data/chroma/           # Vector embeddings
./data/models/           # Downloaded models
```

### Clearing Data

```bash
# Remove all documents and embeddings
rm -rf data/chroma/*

# Remove uploaded files
rm -rf data/uploads/*

# Keep models for faster restart
```

### Backing Up Data

```bash
# Backup chromadb
cp -r data/chroma data/chroma.backup

# Restore
cp -r data/chroma.backup data/chroma
```

---

## Performance Testing

### Test Query Speed

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Your test question here",
    "top_k": 10,
    "use_reranker": true,
    "stream": false
  }'
```

Response includes `processing_time_ms` showing total time.

### Monitor Memory Usage

```bash
# On Linux
watch -n 1 nvidia-smi    # GPU memory
free -h                  # System RAM

# On macOS
top                      # System stats
```

---

## Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Kubernetes deployment
- Load balancing
- SSL/TLS setup
- Database persistence
- Monitoring and logging

---

## Getting Help

1. Check the main [README.md](README.md)
2. Review API docs at `/docs` endpoint
3. Check service logs for detailed errors
4. Verify .env configuration
5. Ensure all dependencies installed with `pip list` and `npm list`

---

## Next Steps

After successful setup:

1. **Experiment with Documents**: Test with different file types
2. **Tune Parameters**: Adjust chunk sizes and retrieval settings
3. **Explore API**: Use the `/docs` endpoint
4. **Customize Frontend**: Modify components in `frontend/src`
5. **Extend Features**: Add new services or models

Enjoy using Retrieval King!
