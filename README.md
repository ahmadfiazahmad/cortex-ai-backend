# Cortex AI Backend — Week 3-4

Zyro Internship Program — Document Processing & Semantic Search.

This project builds on the Week 1-2 Python/FastAPI backend and adds:

**document upload → text extraction → overlapping chunking → embeddings → pgvector storage → semantic search**

## Stack

- Python
- FastAPI
- PostgreSQL + pgvector
- Psycopg
- bcrypt + PyJWT (existing Week 2 authentication)
- pypdf
- python-docx
- OpenAI Embeddings API

## Project Structure

```text
cortex-ai-backend/
├── config/
│   ├── database.py
│   └── migrate.py
├── controllers/
│   ├── auth_controller.py
│   ├── document_controller.py
│   └── search_controller.py
├── middleware/
│   ├── auth_middleware.py
│   ├── error_handler.py
│   ├── request_logger.py
│   └── upload.py
├── models/
│   ├── user.py
│   ├── document.py
│   ├── chunk.py
│   └── search.py
├── routes/
│   ├── auth.py
│   ├── health.py
│   ├── document_routes.py
│   └── search_routes.py
├── services/
│   ├── extraction_service.py
│   ├── chunking_service.py
│   ├── embedding_service.py
│   └── processing_service.py
├── utils/
│   └── retry.py
├── migrations/
│   └── 001_documents.sql
├── uploads/
├── .env.example
├── .gitignore
├── main.py
├── requirements.txt
└── README.md
```

## Setup

Create and activate the existing project virtual environment, then install dependencies:

```bash
pip install -r requirements.txt
```

Copy the example environment file:

```bash
cp .env.example .env
```

Set your PostgreSQL and JWT values in `.env`, then add your OpenAI API key:

```env
OPENAI_API_KEY=your_key_here
```

The real `.env` file must not be committed.

## PostgreSQL / pgvector

The Week 3-4 migration expects the `vector` extension to be available in PostgreSQL.

Run the migration using the PostgreSQL account that has permission to create the extension and tables:

```bash
sudo -u postgres psql -d cortex_ai -f migrations/001_documents.sql
```

The migration creates the `documents` and `chunks` tables, enables pgvector, and creates the cosine similarity index.

## Run

From the project root:

```bash
uvicorn main:app --reload
```

Server:

```text
http://127.0.0.1:8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### `POST /api/documents`

Protected upload endpoint.

Multipart form field:

```text
file
```

Accepted types:

- PDF
- DOCX
- TXT

Maximum file size: 20 MB.

Returns `202 Accepted` with `status: "processing"`. Processing runs in the background.

### `GET /api/documents`

Lists the authenticated user's documents and their current status.

### `GET /api/documents/{id}`

Returns document details and chunk/embedding status.

### `DELETE /api/documents/{id}`

Deletes the document. Its chunks are cascade-deleted by PostgreSQL.

### `POST /api/search`

Semantic search request:

```json
{
  "query": "what are the refund terms?",
  "topK": 5
}
```

Optional document scope:

```json
{
  "query": "refund terms",
  "topK": 5,
  "documentId": "DOCUMENT_UUID"
}
```

The query is embedded and compared against stored chunk vectors using cosine similarity.

All Week 3-4 document and search endpoints use the Week 2 JWT in the `Authorization` header:

```text
Authorization: Bearer YOUR_JWT_TOKEN
```

## Processing Pipeline

```text
Upload
  ↓
Store file on local disk
  ↓
Create Document record (processing)
  ↓
Extract text
  ↓
Split into ~500-token chunks with ~50-token overlap
  ↓
Save Chunk records
  ↓
Generate embeddings in batches
  ↓
Store vectors in pgvector
  ↓
Document becomes ready
```

If embedding batches keep failing, the affected chunks are marked `failed` and the document stays `processing` so they can be reprocessed later.

## Chunking

The chunking implementation approximates tokens using whitespace-separated words. This keeps the project dependency-light while implementing the required ~500-token chunks and ~50-token overlap.

## Testing Flow

1. Log in through `POST /api/auth/login` and copy the JWT.
2. Click **Authorize** in Swagger and provide the JWT.
3. Upload a PDF, DOCX, and TXT file through `POST /api/documents`.
4. Check `GET /api/documents` and `GET /api/documents/{id}` until the document becomes `ready`.
5. Run `POST /api/search` with a natural-language query.
6. Optionally provide `documentId` to scope the search to one document.
7. Delete a document using `DELETE /api/documents/{id}`.

## Week 3-4 Requirements Covered

- Document and Chunk models
- PDF/DOCX/TXT upload validation
- Local file storage
- Text extraction
- Overlapping chunking
- Document status tracking
- Document CRUD
- Cascade deletion of chunks
- Batch embedding generation
- pgvector storage and cosine similarity index
- Scoped and unscoped semantic search
- Retry/backoff for embedding failures
- Failed chunks retained for later reprocessing
