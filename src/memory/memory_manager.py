"""Memory management for storing user interactions and context."""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class MemoryManager:
    """Manage persistent memory of user interactions and queries."""

    def __init__(self, memory_file: str = "./data/memory.json"):
        """
        Initialize memory manager.

        Args:
            memory_file: Path to memory storage file
        """
        self.memory_file = memory_file
        self.memory: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self) -> None:
        """Load memory from file."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    self.memory = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load memory: {e}")
                self.memory = []
        else:
            # Create directory if it doesn't exist
            Path(self.memory_file).parent.mkdir(parents=True, exist_ok=True)
            self.memory = []

    def _save_memory(self) -> None:
        """Save memory to file."""
        try:
            with open(self.memory_file, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save memory: {e}")

    def add_interaction(
        self,
        query: str,
        response: str,
        metadata: Dict[str, Any] = None
    ) -> None:
        """
        Add an interaction to memory.

        Args:
            query: User query
            response: System response
            metadata: Additional metadata
        """
        interaction = {
            "id": len(self.memory) + 1,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "response": response,
            "metadata": metadata or {}
        }

        self.memory.append(interaction)
        self._save_memory()

    def add_document_memory(
        self,
        document_id: str,
        title: str,
        summary: str,
        key_concepts: List[str],
        citations: List[str]
    ) -> None:
        """
        Add document processing to memory.

        Args:
            document_id: Unique document identifier
            title: Document title
            summary: Generated summary
            key_concepts: Extracted key concepts
            citations: Found citations
        """
        memory_entry = {
            "id": len(self.memory) + 1,
            "timestamp": datetime.now().isoformat(),
            "type": "document",
            "document_id": document_id,
            "title": title,
            "summary": summary,
            "key_concepts": key_concepts,
            "citations": citations
        }

        self.memory.append(memory_entry)
        self._save_memory()

    def get_recent_interactions(self, n: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent interactions.

        Args:
            n: Number of recent interactions

        Returns:
            List of recent interactions
        """
        return self.memory[-n:] if self.memory else []

    def search_memory(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search memory for keyword.

        Args:
            keyword: Search keyword

        Returns:
            List of matching memory entries
        """
        keyword_lower = keyword.lower()
        results = []

        for entry in self.memory:
            # Search in query
            if 'query' in entry and keyword_lower in entry['query'].lower():
                results.append(entry)
            # Search in title
            elif 'title' in entry and keyword_lower in entry['title'].lower():
                results.append(entry)
            # Search in summary
            elif 'summary' in entry and keyword_lower in entry['summary'].lower():
                results.append(entry)

        return results

    def get_document_history(self) -> List[Dict[str, Any]]:
        """
        Get all processed documents from memory.

        Returns:
            List of document memory entries
        """
        return [entry for entry in self.memory if entry.get('type') == 'document']

    def get_interaction_by_id(self, interaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get specific interaction by ID.

        Args:
            interaction_id: Interaction ID

        Returns:
            Interaction dictionary or None
        """
        for entry in self.memory:
            if entry.get('id') == interaction_id:
                return entry
        return None

    def get_context_for_query(self, query: str, n: int = 3) -> str:
        """
        Get relevant context from memory for a query.

        Args:
            query: User query
            n: Number of relevant entries to include

        Returns:
            Context string
        """
        # Simple keyword-based relevance
        query_words = set(query.lower().split())
        scored_entries = []

        for entry in self.memory:
            score = 0
            entry_text = ""

            if 'query' in entry:
                entry_text += entry['query'] + " "
            if 'summary' in entry:
                entry_text += entry['summary'] + " "
            if 'title' in entry:
                entry_text += entry['title'] + " "

            entry_words = set(entry_text.lower().split())
            score = len(query_words & entry_words)

            if score > 0:
                scored_entries.append((score, entry))

        # Sort by score and get top n
        scored_entries.sort(reverse=True, key=lambda x: x[0])
        top_entries = scored_entries[:n]

        # Format context
        context_parts = []
        for score, entry in top_entries:
            if 'title' in entry:
                context_parts.append(f"Document: {entry['title']}")
                if 'summary' in entry:
                    context_parts.append(f"Summary: {entry['summary'][:200]}...")
            elif 'query' in entry:
                context_parts.append(f"Previous query: {entry['query']}")
                if 'response' in entry:
                    context_parts.append(f"Response: {entry['response'][:200]}...")

        return "\n\n".join(context_parts)

    def clear_memory(self) -> None:
        """Clear all memory."""
        self.memory = []
        self._save_memory()

    def export_memory(self, export_path: str) -> None:
        """
        Export memory to a file.

        Args:
            export_path: Path to export file
        """
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(self.memory, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise Exception(f"Error exporting memory: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Statistics dictionary
        """
        total_entries = len(self.memory)
        document_entries = len([e for e in self.memory if e.get('type') == 'document'])
        query_entries = total_entries - document_entries

        return {
            "total_entries": total_entries,
            "document_entries": document_entries,
            "query_entries": query_entries,
            "oldest_entry": self.memory[0]['timestamp'] if self.memory else None,
            "newest_entry": self.memory[-1]['timestamp'] if self.memory else None
        }
