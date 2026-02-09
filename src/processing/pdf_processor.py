"""PDF processing and text extraction."""
import re
from typing import Dict, List, Tuple
import pymupdf  # PyMuPDF
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import settings


class PDFProcessor:
    """Process PDF documents and extract information."""

    def __init__(self):
        """Initialize PDF processor with text splitter."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

    def extract_text(self, pdf_path: str) -> Tuple[str, Dict]:
        """
        Extract text and metadata from PDF.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Tuple of (full_text, metadata_dict)
        """
        try:
            doc = pymupdf.open(pdf_path)
            text = ""
            metadata = {}

            # Extract text from all pages
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                text += f"\n--- Page {page_num + 1} ---\n{page_text}"

            # Extract metadata
            metadata['title'] = doc.metadata.get('title', 'Unknown')
            metadata['author'] = doc.metadata.get('author', 'Unknown')
            metadata['subject'] = doc.metadata.get('subject', '')
            metadata['pages'] = len(doc)
            metadata['source'] = pdf_path

            doc.close()

            return text, metadata

        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

    def extract_citations(self, text: str) -> List[str]:
        """
        Extract citations from text using regex patterns.

        Args:
            text: Full text of document

        Returns:
            List of unique citations
        """
        citations = []

        # Pattern 1: [1], [2], etc.
        pattern1 = r'\[(\d+)\]'
        matches1 = re.findall(pattern1, text)
        citations.extend([f"[{m}]" for m in matches1])

        # Pattern 2: (Author et al., Year)
        pattern2 = r'\(([A-Z][a-z]+\s+et\s+al\.?,?\s+\d{4})\)'
        matches2 = re.findall(pattern2, text)
        citations.extend(matches2)

        # Pattern 3: (Author & Author, Year)
        pattern3 = r'\(([A-Z][a-z]+\s+&\s+[A-Z][a-z]+,?\s+\d{4})\)'
        matches3 = re.findall(pattern3, text)
        citations.extend(matches3)

        # Pattern 4: (Author, Year)
        pattern4 = r'\(([A-Z][a-z]+,?\s+\d{4})\)'
        matches4 = re.findall(pattern4, text)
        citations.extend(matches4)

        # Remove duplicates and return
        return list(set(citations))

    def extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract potential key concepts/keywords from text.

        Args:
            text: Full text of document

        Returns:
            List of key concepts
        """
        # Look for common patterns in academic papers
        concepts = []

        # Extract from abstract section
        abstract_match = re.search(
            r'abstract[:\s]+(.+?)(?:introduction|keywords)',
            text.lower(),
            re.DOTALL
        )
        if abstract_match:
            abstract_text = abstract_match.group(1)
            # Simple extraction of capitalized phrases
            capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', abstract_text)
            concepts.extend(capitalized)

        # Extract from keywords section
        keywords_match = re.search(
            r'keywords?[:\s]+(.+?)(?:\n\n|\d+\.?\s+introduction)',
            text.lower(),
            re.DOTALL
        )
        if keywords_match:
            keywords_text = keywords_match.group(1)
            # Split by common delimiters
            keywords = re.split(r'[,;·•]', keywords_text)
            concepts.extend([k.strip() for k in keywords])

        return list(set([c for c in concepts if len(c) > 3]))[:20]

    def chunk_document(self, text: str) -> List[str]:
        """
        Split document into chunks for embedding.

        Args:
            text: Full text of document

        Returns:
            List of text chunks
        """
        chunks = self.text_splitter.split_text(text)
        return chunks

    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        Extract common paper sections (abstract, introduction, etc.).

        Args:
            text: Full text of document

        Returns:
            Dictionary with section names as keys
        """
        sections = {}

        # Common section patterns
        section_patterns = {
            'abstract': r'abstract[:\s]+(.*?)(?:introduction|\d+\.?\s+introduction)',
            'introduction': r'(?:introduction|\d+\.?\s+introduction)(.*?)(?:related work|methodology|background)',
            'methodology': r'(?:methodology|methods|\d+\.?\s+methods?)(.*?)(?:results|experiments|evaluation)',
            'results': r'(?:results|\d+\.?\s+results)(.*?)(?:discussion|conclusion)',
            'conclusion': r'(?:conclusion|\d+\.?\s+conclusion)(.*?)(?:references|acknowledgment)',
        }

        for section_name, pattern in section_patterns.items():
            match = re.search(pattern, text.lower(), re.DOTALL)
            if match:
                sections[section_name] = match.group(1).strip()[:2000]  # Limit size

        return sections
