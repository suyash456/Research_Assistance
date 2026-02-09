"""FastAPI backend for Research Assistant."""
import os
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.agents.research_graph import ResearchGraph
from src.memory.memory_manager import MemoryManager
from src.rag.rag_system import RAGSystem
from src.graph.citation_graph import CitationGraph
from src.config import settings

# Initialize FastAPI app
app = FastAPI(
    title="Personal AI Research Assistant",
    description="AI-powered research assistant with RAG, citations, and memory",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
research_graph = ResearchGraph()
memory_manager = MemoryManager()
rag_system = RAGSystem()
citation_graph = CitationGraph()


# Pydantic models
class URLRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    query: str
    use_context: bool = True


class SearchRequest(BaseModel):
    keyword: str


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Personal AI Research Assistant API",
        "version": "1.0.0",
        "endpoints": [
            "/upload/pdf",
            "/process/url",
            "/query",
            "/memory/recent",
            "/memory/search",
            "/citations/influential"
        ]
    }


@app.post("/upload/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload and process a PDF file.

    Args:
        file: PDF file upload

    Returns:
        Processing results with summary, citations, and related papers
    """
    try:
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Save PDF
        file_path = Path(settings.pdf_upload_path) / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Process with LangGraph
        result = research_graph.process(str(file_path))

        # Check for errors
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])

        # Format response
        return {
            "status": "success",
            "filename": file.filename,
            "title": result.get('metadata', {}).get('title', 'Unknown'),
            "author": result.get('metadata', {}).get('author', 'Unknown'),
            "pages": result.get('metadata', {}).get('pages', 0),
            "summary": result.get('summary', {}),
            "citations": result.get('citations', []),
            "key_concepts": result.get('key_concepts', []),
            "related_papers": result.get('related_papers', []),
            "processing_messages": [msg.content for msg in result.get('messages', [])]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/process/url")
async def process_url(request: URLRequest):
    """
    Process content from a URL.

    Args:
        request: URL request with url field

    Returns:
        Processing results
    """
    try:
        # Process with LangGraph
        result = research_graph.process(request.url)

        # Check for errors
        if result.get('error'):
            raise HTTPException(status_code=500, detail=result['error'])

        return {
            "status": "success",
            "url": request.url,
            "title": result.get('metadata', {}).get('title', 'Unknown'),
            "author": result.get('metadata', {}).get('author', 'Unknown'),
            "summary": result.get('summary', {}),
            "citations": result.get('citations', []),
            "key_concepts": result.get('key_concepts', []),
            "related_papers": result.get('related_papers', []),
            "processing_messages": [msg.content for msg in result.get('messages', [])]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing URL: {str(e)}")


@app.post("/query")
async def query(request: QueryRequest):
    """
    Query the knowledge base.

    Args:
        request: Query request with query text

    Returns:
        Answer from RAG system
    """
    try:
        # Get context from memory if requested
        context = ""
        if request.use_context:
            context = memory_manager.get_context_for_query(request.query)

        # Process query
        result = research_graph.process(request.query)

        return {
            "status": "success",
            "query": request.query,
            "answer": result.get('summary', {}).get('answer', 'No answer found'),
            "context_used": context if request.use_context else None,
            "processing_messages": [msg.content for msg in result.get('messages', [])]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.get("/memory/recent")
async def get_recent_memory(n: int = 5):
    """
    Get recent memory entries.

    Args:
        n: Number of recent entries

    Returns:
        List of recent memory entries
    """
    try:
        recent = memory_manager.get_recent_interactions(n)
        return {
            "status": "success",
            "count": len(recent),
            "entries": recent
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving memory: {str(e)}")


@app.post("/memory/search")
async def search_memory(request: SearchRequest):
    """
    Search memory for keyword.

    Args:
        request: Search request with keyword

    Returns:
        Matching memory entries
    """
    try:
        results = memory_manager.search_memory(request.keyword)
        return {
            "status": "success",
            "keyword": request.keyword,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching memory: {str(e)}")


@app.get("/memory/documents")
async def get_document_history():
    """Get all processed documents."""
    try:
        documents = memory_manager.get_document_history()
        return {
            "status": "success",
            "count": len(documents),
            "documents": documents
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@app.get("/memory/stats")
async def get_memory_stats():
    """Get memory statistics."""
    try:
        stats = memory_manager.get_statistics()
        return {
            "status": "success",
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@app.get("/citations/influential")
async def get_influential_papers(limit: int = 10):
    """
    Get most influential papers from citation graph.

    Args:
        limit: Maximum number of papers

    Returns:
        List of influential papers
    """
    try:
        papers = citation_graph.find_influential_papers(limit)
        return {
            "status": "success",
            "count": len(papers),
            "papers": papers
        }
    except Exception as e:
        return {
            "status": "warning",
            "message": "Citation graph unavailable",
            "papers": []
        }


@app.get("/search/semantic")
async def semantic_search(query: str, k: int = 5):
    """
    Perform semantic search across all documents.

    Args:
        query: Search query
        k: Number of results

    Returns:
        Search results with similarity scores
    """
    try:
        results = rag_system.semantic_search(query, k)
        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in semantic search: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
