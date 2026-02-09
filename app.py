"""Streamlit UI for Research Assistant."""
import streamlit as st
import requests
from pathlib import Path
import json

# Page config
st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide"
)

# API base URL
API_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .citation-item {
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-left: 3px solid #007bff;
        background-color: #f8f9fa;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🔬 Personal AI Research Assistant</div>', unsafe_allow_html=True)
st.markdown("**Feed PDFs or URLs → AI generates summaries, citations, and related work suggestions**")

# Sidebar
with st.sidebar:
    st.header("📚 About")
    st.write("""
    This AI Research Assistant helps you:
    - 📄 Process research papers (PDF)
    - 🌐 Extract content from URLs
    - 🔍 Query your knowledge base
    - 📊 Build citation networks
    - 🧠 Remember past interactions
    """)

    st.divider()

    st.header("⚙️ Settings")
    api_status = st.empty()

    # Check API status
    try:
        response = requests.get(f"{API_URL}/")
        if response.status_code == 200:
            api_status.success("✅ API Connected")
        else:
            api_status.error("❌ API Error")
    except:
        api_status.error("❌ API Not Running")
        st.warning("Please start the API server:\n```python main.py```")

    st.divider()

    # Memory stats
    st.header("📊 Statistics")
    try:
        stats_response = requests.get(f"{API_URL}/memory/stats")
        if stats_response.status_code == 200:
            stats = stats_response.json()['statistics']
            st.metric("Total Entries", stats['total_entries'])
            st.metric("Documents", stats['document_entries'])
            st.metric("Queries", stats['query_entries'])
    except:
        st.info("Stats unavailable")

# Main content tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📄 Upload PDF",
    "🌐 Process URL",
    "💬 Query",
    "🧠 Memory",
    "📊 Citations"
])

# Tab 1: Upload PDF
with tab1:
    st.header("Upload Research Paper (PDF)")

    uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

    if uploaded_file and st.button("Process PDF", key="process_pdf"):
        with st.spinner("Processing PDF... This may take a moment."):
            try:
                files = {"file": uploaded_file}
                response = requests.post(f"{API_URL}/upload/pdf", files=files)

                if response.status_code == 200:
                    result = response.json()

                    st.success("✅ PDF processed successfully!")

                    # Display results
                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📋 Metadata")
                        st.write(f"**Title:** {result['title']}")
                        st.write(f"**Author:** {result['author']}")
                        st.write(f"**Pages:** {result['pages']}")

                    with col2:
                        st.subheader("🔑 Key Concepts")
                        concepts = result.get('key_concepts', [])[:10]
                        for concept in concepts:
                            st.write(f"• {concept}")

                    st.divider()

                    st.subheader("📝 Summary")
                    summary = result.get('summary', {}).get('full_summary', 'No summary available')
                    st.write(summary)

                    st.divider()

                    col3, col4 = st.columns(2)

                    with col3:
                        st.subheader("📚 Citations Found")
                        citations = result.get('citations', [])
                        st.write(f"Found {len(citations)} citations")
                        for citation in citations[:10]:
                            st.markdown(f'<div class="citation-item">{citation}</div>', unsafe_allow_html=True)

                    with col4:
                        st.subheader("🔗 Related Papers")
                        related = result.get('related_papers', [])
                        if related:
                            for paper in related:
                                st.write(f"• {paper.get('title', paper.get('id', 'Unknown'))}")
                        else:
                            st.info("No related papers found in citation graph")

                    # Processing messages
                    with st.expander("🔍 Processing Details"):
                        for msg in result.get('processing_messages', []):
                            st.write(msg)
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 2: Process URL
with tab2:
    st.header("Process URL Content")

    url = st.text_input("Enter URL (research paper, article, etc.)")

    if st.button("Process URL", key="process_url") and url:
        with st.spinner("Scraping and processing URL..."):
            try:
                response = requests.post(
                    f"{API_URL}/process/url",
                    json={"url": url}
                )

                if response.status_code == 200:
                    result = response.json()

                    st.success("✅ URL processed successfully!")

                    col1, col2 = st.columns(2)

                    with col1:
                        st.subheader("📋 Metadata")
                        st.write(f"**Title:** {result['title']}")
                        st.write(f"**Author:** {result['author']}")

                    with col2:
                        st.subheader("🔑 Key Concepts")
                        concepts = result.get('key_concepts', [])[:10]
                        for concept in concepts:
                            st.write(f"• {concept}")

                    st.divider()

                    st.subheader("📝 Summary")
                    summary = result.get('summary', {}).get('full_summary', 'No summary available')
                    st.write(summary)

                    st.divider()

                    st.subheader("📚 Citations Found")
                    citations = result.get('citations', [])
                    st.write(f"Found {len(citations)} citations")
                    for citation in citations[:10]:
                        st.markdown(f'<div class="citation-item">{citation}</div>', unsafe_allow_html=True)
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 3: Query
with tab3:
    st.header("Query Your Knowledge Base")

    query = st.text_area("Ask a question about your documents")
    use_context = st.checkbox("Use memory context", value=True)

    if st.button("Search", key="query_search") and query:
        with st.spinner("Searching..."):
            try:
                response = requests.post(
                    f"{API_URL}/query",
                    json={"query": query, "use_context": use_context}
                )

                if response.status_code == 200:
                    result = response.json()

                    st.subheader("💡 Answer")
                    st.write(result['answer'])

                    if use_context and result.get('context_used'):
                        with st.expander("📖 Context Used"):
                            st.write(result['context_used'])
                else:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.divider()

    st.subheader("🔍 Semantic Search")
    semantic_query = st.text_input("Search across all documents")

    if st.button("Semantic Search", key="semantic_search") and semantic_query:
        with st.spinner("Searching..."):
            try:
                response = requests.get(
                    f"{API_URL}/search/semantic",
                    params={"query": semantic_query, "k": 5}
                )

                if response.status_code == 200:
                    result = response.json()
                    st.write(f"Found {result['count']} results")

                    for i, res in enumerate(result['results'], 1):
                        with st.expander(f"Result {i} (Score: {res['similarity_score']:.3f})"):
                            st.write(res['content'])
                            st.json(res['metadata'])
                else:
                    st.error("Search failed")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Tab 4: Memory
with tab4:
    st.header("🧠 Memory & History")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📜 Recent Interactions")
        n_recent = st.slider("Number of entries", 1, 20, 5)

        if st.button("Load Recent", key="load_recent"):
            try:
                response = requests.get(f"{API_URL}/memory/recent", params={"n": n_recent})
                if response.status_code == 200:
                    entries = response.json()['entries']
                    for entry in reversed(entries):
                        with st.expander(f"{entry.get('timestamp', 'Unknown')} - {entry.get('type', 'interaction')}"):
                            st.json(entry)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    with col2:
        st.subheader("🔍 Search Memory")
        keyword = st.text_input("Search keyword")

        if st.button("Search Memory", key="search_memory") and keyword:
            try:
                response = requests.post(
                    f"{API_URL}/memory/search",
                    json={"keyword": keyword}
                )
                if response.status_code == 200:
                    results = response.json()['results']
                    st.write(f"Found {len(results)} matches")
                    for result in results:
                        with st.expander(f"{result.get('timestamp', 'Unknown')}"):
                            st.json(result)
            except Exception as e:
                st.error(f"Error: {str(e)}")

    st.divider()

    st.subheader("📚 Document History")
    if st.button("Load Documents", key="load_docs"):
        try:
            response = requests.get(f"{API_URL}/memory/documents")
            if response.status_code == 200:
                documents = response.json()['documents']
                st.write(f"Total documents: {len(documents)}")

                for doc in documents:
                    with st.expander(f"📄 {doc.get('title', 'Unknown')}"):
                        st.write(f"**ID:** {doc.get('document_id', 'N/A')}")
                        st.write(f"**Time:** {doc.get('timestamp', 'N/A')}")
                        st.write(f"**Summary:** {doc.get('summary', 'N/A')[:200]}...")
                        st.write(f"**Concepts:** {', '.join(doc.get('key_concepts', [])[:5])}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Tab 5: Citations
with tab5:
    st.header("📊 Citation Graph & Analysis")

    st.subheader("🌟 Most Influential Papers")
    limit = st.slider("Number of papers", 5, 20, 10)

    if st.button("Load Influential Papers", key="load_influential"):
        try:
            response = requests.get(f"{API_URL}/citations/influential", params={"limit": limit})
            if response.status_code == 200:
                result = response.json()
                papers = result.get('papers', [])

                if papers:
                    st.write(f"Found {len(papers)} papers")

                    for i, paper in enumerate(papers, 1):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{i}. {paper.get('title', paper.get('id', 'Unknown'))}**")
                            if paper.get('year'):
                                st.write(f"Year: {paper['year']}")
                        with col2:
                            st.metric("Citations", paper.get('citation_count', 0))
                        st.divider()
                else:
                    st.info("No papers in citation graph yet. Process some papers first!")
            else:
                st.warning("Citation graph unavailable. Make sure Neo4j is running.")
        except Exception as e:
            st.error(f"Error: {str(e)}")

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: gray;">
    <p>Built with LangChain, LangGraph, ChromaDB, Neo4j, FastAPI, and Streamlit</p>
    <p>🔬 Personal AI Research Assistant v1.0</p>
</div>
""", unsafe_allow_html=True)
