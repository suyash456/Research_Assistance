# 🔬 Personal AI Research Assistant

A sophisticated AI-powered research assistant that processes research papers (PDFs), extracts content from URLs, generates summaries, builds citation networks, and maintains memory of past interactions.

## ✨ Features

### Core Capabilities
- 📄 **PDF Processing**: Extract text, metadata, citations, and key concepts from research papers
- 🌐 **URL Scraping**: Process content from web pages and research repositories (arXiv support)
- 🤖 **AI Summaries**: Generate comprehensive summaries with key findings and methodology
- 📚 **Citation Extraction**: Automatically identify and extract citations
- 🔗 **Citation Graph**: Build and query citation networks using Neo4j
- 💾 **RAG System**: Retrieval Augmented Generation with vector embeddings
- 🧠 **Memory Management**: Persistent memory of all interactions and documents
- 🔍 **Semantic Search**: Find relevant content across all processed documents

### Advanced Features
- ✅ **LangGraph Orchestration**: Multi-step workflow management
- ✅ **Vector Embeddings**: ChromaDB for efficient similarity search
- ✅ **Knowledge Graph**: Neo4j-based citation network analysis
- ✅ **RESTful API**: FastAPI backend with comprehensive endpoints
- ✅ **Modern UI**: Streamlit-based web interface

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Input                        │
│              (PDF/URL/Query)                        │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────▼─────────┐
         │  LangGraph Router │
         │  (Orchestration)  │
         └─────────┬─────────┘
                   │
        ┌──────────┼──────────┬──────────────┐
        │          │          │              │
   ┌────▼───┐ ┌───▼────┐ ┌───▼────┐    ┌───▼────┐
   │ PDF    │ │ URL    │ │ RAG    │    │ Memory │
   │Process │ │Scraper │ │Search  │    │ Node   │
   └────┬───┘ └───┬────┘ └───┬────┘    └───┬────┘
        │         │          │              │
        └─────────┼──────────┼──────────────┘
                  │          │
         ┌────────▼──────────▼────────┐
         │   Vector Store (ChromaDB)  │
         │   Graph DB (Neo4j)         │
         └────────────┬────────────────┘
                      │
         ┌────────────▼────────────────┐
         │   LLM (Generate Response)   │
         └─────────────────────────────┘
```

## 📁 Project Structure

```
research-assistant/
├── src/
│   ├── agents/              # LangGraph workflow orchestration
│   │   └── research_graph.py
│   ├── processing/          # PDF and URL processing
│   │   ├── pdf_processor.py
│   │   └── url_scraper.py
│   ├── rag/                # RAG system with embeddings
│   │   └── rag_system.py
│   ├── graph/              # Citation graph management
│   │   └── citation_graph.py
│   ├── memory/             # Memory management
│   │   └── memory_manager.py
│   ├── api/                # API utilities
│   └── config.py           # Configuration
├── data/
│   ├── pdfs/               # Uploaded PDFs
│   ├── vectorstore/        # ChromaDB storage
│   ├── graphs/             # Graph data
│   └── memory.json         # Interaction memory
├── main.py                 # FastAPI server
├── app.py                  # Streamlit UI
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## 🚀 Installation

### Prerequisites
- Python 3.9+
- OpenAI API key
- Neo4j (optional, for citation graph features)

### Step 1: Clone and Setup

```bash
# Clone or download the project
cd Research_Assistant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (for citation graph)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### Step 3: Install Neo4j (Optional)

**For full citation graph features, install Neo4j:**

#### Using Docker (Recommended):
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password_here \
  neo4j:latest
```

#### Or download from: https://neo4j.com/download/

Access Neo4j Browser at: http://localhost:7474

## 🎯 Usage

### Starting the Application

#### Terminal 1: Start API Server
```bash
python main.py
```

API will be available at: http://localhost:8000

#### Terminal 2: Start Streamlit UI
```bash
streamlit run app.py
```

UI will open at: http://localhost:8501

### Using the Application

#### 1. Upload PDF
- Go to "Upload PDF" tab
- Select a research paper PDF
- Click "Process PDF"
- View summary, citations, and related papers

#### 2. Process URL
- Go to "Process URL" tab
- Enter URL (works great with arXiv papers)
- Click "Process URL"
- View extracted content and analysis

#### 3. Query Knowledge Base
- Go to "Query" tab
- Ask questions about processed documents
- Enable "Use memory context" for better results
- Get AI-generated answers

#### 4. View Memory
- Go to "Memory" tab
- Browse recent interactions
- Search past documents
- View processing history

#### 5. Citation Analysis
- Go to "Citations" tab
- View most influential papers
- Explore citation networks

## 🔧 API Endpoints

### Document Processing
- `POST /upload/pdf` - Upload and process PDF
- `POST /process/url` - Process content from URL

### Query & Search
- `POST /query` - Query knowledge base
- `GET /search/semantic` - Semantic search across documents

### Memory
- `GET /memory/recent` - Get recent interactions
- `POST /memory/search` - Search memory by keyword
- `GET /memory/documents` - Get all processed documents
- `GET /memory/stats` - Get memory statistics

### Citations
- `GET /citations/influential` - Get most cited papers

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation (Swagger UI)

## 💡 Example Use Cases

### Research Paper Analysis
```python
# Upload a PDF and get:
# - Structured summary
# - Key contributions and methodology
# - Extracted citations
# - Related work suggestions
# - Key concepts
```

### Literature Review
```python
# Process multiple papers and:
# - Build citation network
# - Find influential papers
# - Discover related research
# - Track reading history
```

### Question Answering
```python
# Query your knowledge base:
# "What methods did the authors use?"
# "What are the main findings?"
# "How does this compare to previous work?"
```

## 🛠️ Technology Stack

### AI/ML
- **LangChain**: LLM orchestration and chains
- **LangGraph**: Multi-agent workflow management
- **OpenAI GPT-4**: Text generation and analysis
- **Sentence Transformers**: Text embeddings

### Databases
- **ChromaDB**: Vector database for embeddings
- **Neo4j**: Graph database for citations
- **JSON**: Memory persistence

### Backend
- **FastAPI**: Modern Python web framework
- **Uvicorn**: ASGI server
- **Pydantic**: Data validation

### Frontend
- **Streamlit**: Interactive web UI
- **Requests**: API communication

### Document Processing
- **PyMuPDF**: PDF text extraction
- **BeautifulSoup4**: Web scraping
- **Regex**: Citation extraction

## 📊 Advanced Configuration

### Customizing Chunk Size

Edit `src/config.py`:
```python
chunk_size: int = 1000  # Adjust for your needs
chunk_overlap: int = 200
```

### Using Different Models

Edit `src/config.py`:
```python
model_name: str = "gpt-4"  # or "gpt-3.5-turbo"
embedding_model: str = "text-embedding-ada-002"
```

### Adding Anthropic Claude

Install anthropic and set in `.env`:
```env
ANTHROPIC_API_KEY=your_key_here
```

## 🐛 Troubleshooting

### Issue: API not connecting
**Solution**: Ensure the FastAPI server is running on port 8000
```bash
python main.py
```

### Issue: Neo4j connection failed
**Solution**: Citation graph features will be disabled automatically. App still works without Neo4j.

### Issue: OpenAI API errors
**Solution**: Check your API key in `.env` and ensure you have credits

### Issue: PDF processing fails
**Solution**: Ensure PDF is not encrypted or corrupted

### Issue: Out of memory
**Solution**: Reduce chunk_size or process smaller documents

## 🔒 Security Notes

- Never commit `.env` file
- Keep API keys secure
- Use environment variables for secrets
- Consider rate limiting for production
- Validate all file uploads

## 🚀 Future Enhancements

- [ ] Multi-language support
- [ ] PDF annotation and highlighting
- [ ] Export to Markdown/LaTeX
- [ ] Batch processing
- [ ] Paper recommendation system
- [ ] Collaborative features
- [ ] Mobile app
- [ ] Local LLM support (Llama, Mistral)

## 📄 License

This project is provided as-is for educational and research purposes.

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Better citation extraction
- Enhanced graph visualizations
- More document formats
- Improved summarization
- Performance optimizations

## 📞 Support

For issues and questions:
1. Check troubleshooting section
2. Review API documentation
3. Check logs for errors

## 🎓 Learn More

- **LangChain**: https://python.langchain.com/
- **LangGraph**: https://langchain-ai.github.io/langgraph/
- **ChromaDB**: https://www.trychroma.com/
- **Neo4j**: https://neo4j.com/docs/
- **FastAPI**: https://fastapi.tiangolo.com/

---

**Built with ❤️ using LangChain, LangGraph, ChromaDB, Neo4j, FastAPI, and Streamlit**
"# Research_Assistance" 
