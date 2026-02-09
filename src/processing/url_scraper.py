"""URL scraping and content extraction."""
import re
from typing import Dict, Tuple
import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import RecursiveCharacterTextSplitter
from src.config import settings


class URLScraper:
    """Scrape and process web content."""

    def __init__(self):
        """Initialize URL scraper with text splitter."""
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def scrape_url(self, url: str) -> Tuple[str, Dict]:
        """
        Scrape content from URL.

        Args:
            url: URL to scrape

        Returns:
            Tuple of (text_content, metadata_dict)
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Extract metadata
            metadata = self._extract_metadata(soup, url)

            # Extract main content
            text = self._extract_text(soup)

            return text, metadata

        except Exception as e:
            raise Exception(f"Error scraping URL: {str(e)}")

    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Extract metadata from HTML.

        Args:
            soup: BeautifulSoup object
            url: Original URL

        Returns:
            Metadata dictionary
        """
        metadata = {'source': url, 'type': 'url'}

        # Try to get title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        else:
            # Try meta title
            meta_title = soup.find('meta', property='og:title')
            if meta_title:
                metadata['title'] = meta_title.get('content', 'Unknown')
            else:
                metadata['title'] = 'Unknown'

        # Try to get author
        author_meta = soup.find('meta', attrs={'name': 'author'})
        if author_meta:
            metadata['author'] = author_meta.get('content', 'Unknown')
        else:
            metadata['author'] = 'Unknown'

        # Try to get description
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta:
            metadata['description'] = desc_meta.get('content', '')

        # Try to get publication date
        date_meta = soup.find('meta', property='article:published_time')
        if date_meta:
            metadata['published_date'] = date_meta.get('content', '')

        return metadata

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text from HTML.

        Args:
            soup: BeautifulSoup object

        Returns:
            Clean text content
        """
        # Try to find main content area
        main_content = (
            soup.find('article') or
            soup.find('main') or
            soup.find('div', class_=re.compile(r'content|article|post')) or
            soup.find('body')
        )

        if main_content:
            # Get text from paragraphs
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'li'])
            text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
        else:
            text = soup.get_text()

        # Clean up text
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        text = text.strip()

        return text

    def chunk_content(self, text: str) -> list:
        """
        Split content into chunks.

        Args:
            text: Full text content

        Returns:
            List of text chunks
        """
        return self.text_splitter.split_text(text)

    def is_arxiv_url(self, url: str) -> bool:
        """Check if URL is from arXiv."""
        return 'arxiv.org' in url.lower()

    def extract_arxiv_id(self, url: str) -> str:
        """
        Extract arXiv paper ID from URL.

        Args:
            url: arXiv URL

        Returns:
            arXiv ID
        """
        match = re.search(r'arxiv\.org/(?:abs|pdf)/(\d+\.\d+)', url)
        if match:
            return match.group(1)
        return None

    def get_arxiv_pdf_url(self, arxiv_id: str) -> str:
        """
        Get PDF URL from arXiv ID.

        Args:
            arxiv_id: arXiv paper ID

        Returns:
            PDF URL
        """
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"
