"""RAG system with vector embeddings and retrieval."""
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from src.config import settings


class RAGSystem:
    """Retrieval Augmented Generation system for research papers."""

    def __init__(self, persist_directory: str = None):
        """
        Initialize RAG system.

        Args:
            persist_directory: Path to persist vector store
        """
        self.persist_directory = persist_directory or settings.vector_store_path

        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            model=settings.embedding_model
        )

        # Initialize or load vector store
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="research_papers"
        )

        # Initialize LLM
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            model_name=settings.model_name,
            temperature=settings.temperature
        )

    def add_documents(self, chunks: List[str], metadata: Dict[str, Any]) -> None:
        """
        Add document chunks to vector store.

        Args:
            chunks: List of text chunks
            metadata: Metadata for the document
        """
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    "chunk_id": i,
                    "chunk_total": len(chunks)
                }
            )
            for i, chunk in enumerate(chunks)
        ]

        self.vectorstore.add_documents(documents)

    def retrieve_relevant_chunks(self, query: str, k: int = 5) -> List[Document]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: Search query
            k: Number of chunks to retrieve

        Returns:
            List of relevant documents
        """
        retriever = self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )
        docs = retriever.get_relevant_documents(query)
        return docs

    def generate_summary(self, paper_text: str) -> Dict[str, Any]:
        """
        Generate comprehensive summary of a research paper.

        Args:
            paper_text: Full text or key excerpts from paper

        Returns:
            Dictionary with summary components
        """
        summary_prompt = PromptTemplate(
            input_variables=["text"],
            template="""
You are an expert research assistant. Analyze the following research paper and provide:

1. SUMMARY: A concise 3-4 sentence summary of the paper
2. KEY CONTRIBUTIONS: List 3-5 main contributions or findings
3. METHODOLOGY: Brief overview of the methods used
4. KEY CONCEPTS: Important terms and concepts (5-7 items)
5. LIMITATIONS: Any mentioned limitations or future work

Paper Text:
{text}

Provide your analysis in a structured format.
"""
        )

        prompt_text = summary_prompt.format(text=paper_text[:8000])  # Limit token size
        response = self.llm.predict(prompt_text)

        return {
            "full_summary": response,
            "generated": True
        }

    def generate_related_work_suggestions(self, paper_summary: str, citations: List[str]) -> List[str]:
        """
        Suggest related work based on paper content.

        Args:
            paper_summary: Summary of the paper
            citations: List of citations from the paper

        Returns:
            List of suggested research directions
        """
        prompt = PromptTemplate(
            input_variables=["summary", "citations"],
            template="""
Based on this research paper summary and its citations, suggest 5 related research areas or papers that would be valuable to explore:

Summary: {summary}

Citations: {citations}

Provide 5 specific suggestions for related work, each on a new line.
"""
        )

        citations_str = ", ".join(citations[:20])  # Limit citations
        prompt_text = prompt.format(summary=paper_summary, citations=citations_str)
        response = self.llm.predict(prompt_text)

        # Parse suggestions
        suggestions = [s.strip() for s in response.split('\n') if s.strip()]
        return suggestions[:5]

    def answer_question(self, question: str, context_filter: Dict = None) -> str:
        """
        Answer a question using RAG.

        Args:
            question: User question
            context_filter: Optional metadata filter for retrieval

        Returns:
            Answer string
        """
        # Retrieve relevant documents
        if context_filter:
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": 5, "filter": context_filter}
            )
        else:
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )

        result = qa_chain({"query": question})

        return result["result"]

    def semantic_search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search across all documents.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of search results with metadata
        """
        results = self.vectorstore.similarity_search_with_score(query, k=k)

        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": float(score)
            })

        return formatted_results

    def get_document_by_metadata(self, metadata_filter: Dict) -> List[Document]:
        """
        Retrieve documents by metadata filter.

        Args:
            metadata_filter: Dictionary of metadata to filter by

        Returns:
            List of matching documents
        """
        # Chroma doesn't directly support metadata filtering in all cases
        # This is a basic implementation
        all_docs = self.vectorstore.get()

        filtered_docs = []
        if all_docs and 'metadatas' in all_docs:
            for i, meta in enumerate(all_docs['metadatas']):
                match = all(meta.get(k) == v for k, v in metadata_filter.items())
                if match:
                    filtered_docs.append(Document(
                        page_content=all_docs['documents'][i],
                        metadata=meta
                    ))

        return filtered_docs

    def clear_collection(self):
        """Clear all documents from the vector store."""
        # Delete and recreate the collection
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embeddings,
            collection_name="research_papers"
        )
