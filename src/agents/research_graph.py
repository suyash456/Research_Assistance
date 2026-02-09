"""LangGraph orchestration for research assistant workflow."""
from typing import TypedDict, List, Dict, Any, Annotated
from datetime import datetime
import operator

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage

from src.processing.pdf_processor import PDFProcessor
from src.processing.url_scraper import URLScraper
from src.rag.rag_system import RAGSystem
from src.graph.citation_graph import CitationGraph
from src.memory.memory_manager import MemoryManager


class ResearchState(TypedDict):
    """State for research workflow."""
    input: str
    input_type: str  # 'pdf', 'url', 'query'
    text: str
    metadata: Dict[str, Any]
    chunks: List[str]
    citations: List[str]
    key_concepts: List[str]
    summary: Dict[str, Any]
    related_papers: List[Dict]
    messages: Annotated[List, operator.add]
    memory_context: str
    error: str


class ResearchGraph:
    """LangGraph orchestration for research assistant."""

    def __init__(self):
        """Initialize research graph with all components."""
        self.pdf_processor = PDFProcessor()
        self.url_scraper = URLScraper()
        self.rag_system = RAGSystem()
        self.citation_graph = CitationGraph()
        self.memory_manager = MemoryManager()

        # Build the graph
        self.graph = self._build_graph()

    def _process_input_node(self, state: ResearchState) -> ResearchState:
        """Determine input type and route accordingly."""
        input_data = state['input']

        # Determine type
        if input_data.endswith('.pdf') or 'pdf' in input_data.lower():
            state['input_type'] = 'pdf'
        elif input_data.startswith('http'):
            state['input_type'] = 'url'
        else:
            state['input_type'] = 'query'

        # Get memory context
        state['memory_context'] = self.memory_manager.get_context_for_query(input_data)

        state['messages'] = [HumanMessage(content=f"Processing: {input_data}")]

        return state

    def _pdf_processing_node(self, state: ResearchState) -> ResearchState:
        """Process PDF documents."""
        try:
            text, metadata = self.pdf_processor.extract_text(state['input'])
            citations = self.pdf_processor.extract_citations(text)
            key_concepts = self.pdf_processor.extract_key_concepts(text)
            chunks = self.pdf_processor.chunk_document(text)

            state['text'] = text
            state['metadata'] = metadata
            state['citations'] = citations
            state['key_concepts'] = key_concepts
            state['chunks'] = chunks

            state['messages'] = [
                AIMessage(content=f"✓ Extracted text from PDF: {metadata.get('title', 'Unknown')}")
            ]

        except Exception as e:
            state['error'] = f"PDF processing error: {str(e)}"
            state['messages'] = [AIMessage(content=f"✗ Error: {str(e)}")]

        return state

    def _url_processing_node(self, state: ResearchState) -> ResearchState:
        """Scrape and process URLs."""
        try:
            text, metadata = self.url_scraper.scrape_url(state['input'])
            chunks = self.url_scraper.chunk_content(text)

            # Extract citations from scraped content
            citations = self.pdf_processor.extract_citations(text)
            key_concepts = self.pdf_processor.extract_key_concepts(text)

            state['text'] = text
            state['metadata'] = metadata
            state['citations'] = citations
            state['key_concepts'] = key_concepts
            state['chunks'] = chunks

            state['messages'] = [
                AIMessage(content=f"✓ Scraped content from URL: {metadata.get('title', 'Unknown')}")
            ]

        except Exception as e:
            state['error'] = f"URL scraping error: {str(e)}"
            state['messages'] = [AIMessage(content=f"✗ Error: {str(e)}")]

        return state

    def _rag_processing_node(self, state: ResearchState) -> ResearchState:
        """Process with RAG system."""
        try:
            # Add documents to vector store if we have chunks
            if state.get('chunks'):
                self.rag_system.add_documents(
                    state['chunks'],
                    state.get('metadata', {})
                )

            # Generate summary
            if state.get('text'):
                summary = self.rag_system.generate_summary(state['text'][:8000])
                state['summary'] = summary

                # Generate related work suggestions
                related_suggestions = self.rag_system.generate_related_work_suggestions(
                    summary.get('full_summary', ''),
                    state.get('citations', [])
                )

                state['messages'] = [
                    AIMessage(content=f"✓ Generated summary and extracted {len(state.get('citations', []))} citations")
                ]
            else:
                # Query mode - answer question
                answer = self.rag_system.answer_question(state['input'])
                state['summary'] = {"answer": answer}

                state['messages'] = [
                    AIMessage(content=f"✓ Retrieved answer from knowledge base")
                ]

        except Exception as e:
            state['error'] = f"RAG processing error: {str(e)}"
            state['messages'] = [AIMessage(content=f"✗ Error: {str(e)}")]

        return state

    def _citation_graph_node(self, state: ResearchState) -> ResearchState:
        """Build and query citation graph."""
        try:
            paper_id = state.get('metadata', {}).get('source', state['input'])
            title = state.get('metadata', {}).get('title', 'Unknown')

            # Add paper to graph
            self.citation_graph.add_paper(
                paper_id=paper_id,
                title=title,
                authors=[state.get('metadata', {}).get('author', 'Unknown')],
                abstract=state.get('summary', {}).get('full_summary', '')[:500]
            )

            # Add citations
            if state.get('citations'):
                self.citation_graph.add_citations_from_list(
                    paper_id,
                    state['citations'][:10]  # Limit to avoid too many
                )

            # Find related papers
            related = self.citation_graph.find_related_papers(paper_id, limit=5)
            state['related_papers'] = related

            state['messages'] = [
                AIMessage(content=f"✓ Added to citation graph, found {len(related)} related papers")
            ]

        except Exception as e:
            # Citation graph is optional, don't fail the whole pipeline
            state['messages'] = [
                AIMessage(content=f"⚠ Citation graph unavailable: {str(e)}")
            ]
            state['related_papers'] = []

        return state

    def _memory_node(self, state: ResearchState) -> ResearchState:
        """Store interaction in memory."""
        try:
            if state.get('metadata', {}).get('title'):
                # Document processing
                self.memory_manager.add_document_memory(
                    document_id=state.get('metadata', {}).get('source', state['input']),
                    title=state.get('metadata', {}).get('title', 'Unknown'),
                    summary=state.get('summary', {}).get('full_summary', ''),
                    key_concepts=state.get('key_concepts', []),
                    citations=state.get('citations', [])
                )
            else:
                # Query interaction
                self.memory_manager.add_interaction(
                    query=state['input'],
                    response=state.get('summary', {}).get('answer', ''),
                    metadata=state.get('metadata', {})
                )

            state['messages'] = [
                AIMessage(content="✓ Saved to memory")
            ]

        except Exception as e:
            state['messages'] = [
                AIMessage(content=f"⚠ Memory save failed: {str(e)}")
            ]

        return state

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("process_input", self._process_input_node)
        workflow.add_node("pdf_processing", self._pdf_processing_node)
        workflow.add_node("url_processing", self._url_processing_node)
        workflow.add_node("rag_processing", self._rag_processing_node)
        workflow.add_node("citation_graph", self._citation_graph_node)
        workflow.add_node("memory", self._memory_node)

        # Define routing logic
        def route_input(state: ResearchState):
            """Route based on input type."""
            input_type = state.get('input_type', 'query')

            if input_type == 'pdf':
                return "pdf_processing"
            elif input_type == 'url':
                return "url_processing"
            else:
                return "rag_processing"

        # Set entry point
        workflow.set_entry_point("process_input")

        # Add conditional edges from process_input
        workflow.add_conditional_edges(
            "process_input",
            route_input,
            {
                "pdf_processing": "pdf_processing",
                "url_processing": "url_processing",
                "rag_processing": "rag_processing"
            }
        )

        # Add sequential edges
        workflow.add_edge("pdf_processing", "rag_processing")
        workflow.add_edge("url_processing", "rag_processing")
        workflow.add_edge("rag_processing", "citation_graph")
        workflow.add_edge("citation_graph", "memory")
        workflow.add_edge("memory", END)

        return workflow.compile()

    def process(self, input_data: str) -> Dict[str, Any]:
        """
        Process input through the graph.

        Args:
            input_data: PDF path, URL, or query

        Returns:
            Final state dictionary
        """
        initial_state = {
            "input": input_data,
            "input_type": "",
            "text": "",
            "metadata": {},
            "chunks": [],
            "citations": [],
            "key_concepts": [],
            "summary": {},
            "related_papers": [],
            "messages": [],
            "memory_context": "",
            "error": ""
        }

        result = self.graph.invoke(initial_state)

        return result
