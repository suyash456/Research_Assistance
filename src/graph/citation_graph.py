"""Citation graph management using Neo4j."""
from typing import List, Dict, Optional
from neo4j import GraphDatabase
from src.config import settings


class CitationGraph:
    """Manage citation relationships in a graph database."""

    def __init__(
        self,
        uri: str = None,
        user: str = None,
        password: str = None
    ):
        """
        Initialize citation graph.

        Args:
            uri: Neo4j connection URI
            user: Neo4j username
            password: Neo4j password
        """
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password

        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Test connection
            self.driver.verify_connectivity()
        except Exception as e:
            print(f"Warning: Could not connect to Neo4j: {e}")
            print("Citation graph features will be limited.")
            self.driver = None

    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()

    def add_paper(
        self,
        paper_id: str,
        title: str,
        authors: List[str] = None,
        year: int = None,
        abstract: str = None
    ) -> None:
        """
        Add a paper to the graph.

        Args:
            paper_id: Unique identifier for paper
            title: Paper title
            authors: List of author names
            year: Publication year
            abstract: Paper abstract
        """
        if not self.driver:
            return

        with self.driver.session() as session:
            session.run(
                """
                MERGE (p:Paper {id: $paper_id})
                SET p.title = $title,
                    p.year = $year,
                    p.abstract = $abstract,
                    p.updated = timestamp()
                """,
                paper_id=paper_id,
                title=title,
                year=year,
                abstract=abstract
            )

            # Add authors
            if authors:
                for author in authors:
                    session.run(
                        """
                        MERGE (a:Author {name: $author})
                        MERGE (p:Paper {id: $paper_id})
                        MERGE (a)-[:AUTHORED]->(p)
                        """,
                        author=author,
                        paper_id=paper_id
                    )

    def add_citation(self, citing_paper_id: str, cited_paper_id: str) -> None:
        """
        Add a citation relationship.

        Args:
            citing_paper_id: ID of paper that cites
            cited_paper_id: ID of paper being cited
        """
        if not self.driver:
            return

        with self.driver.session() as session:
            session.run(
                """
                MERGE (citing:Paper {id: $citing_id})
                MERGE (cited:Paper {id: $cited_id})
                MERGE (citing)-[:CITES]->(cited)
                """,
                citing_id=citing_paper_id,
                cited_id=cited_paper_id
            )

    def add_citations_from_list(
        self,
        paper_id: str,
        citations: List[str]
    ) -> None:
        """
        Add multiple citation relationships for a paper.

        Args:
            paper_id: ID of the citing paper
            citations: List of cited paper IDs
        """
        if not self.driver:
            return

        for citation in citations:
            self.add_citation(paper_id, citation)

    def find_related_papers(
        self,
        paper_id: str,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find papers related through citations.

        Args:
            paper_id: Paper ID to find related papers for
            limit: Maximum number of results

        Returns:
            List of related paper dictionaries
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            # Find papers that cite the same papers
            result = session.run(
                """
                MATCH (p:Paper {id: $paper_id})-[:CITES]->(cited:Paper)
                MATCH (cited)<-[:CITES]-(related:Paper)
                WHERE related.id <> $paper_id
                WITH related, COUNT(cited) as shared_citations
                RETURN related.id as id,
                       related.title as title,
                       related.year as year,
                       shared_citations
                ORDER BY shared_citations DESC
                LIMIT $limit
                """,
                paper_id=paper_id,
                limit=limit
            )

            papers = []
            for record in result:
                papers.append({
                    "id": record["id"],
                    "title": record["title"],
                    "year": record["year"],
                    "relevance_score": record["shared_citations"]
                })

            return papers

    def find_influential_papers(self, limit: int = 10) -> List[Dict]:
        """
        Find most cited papers in the graph.

        Args:
            limit: Maximum number of results

        Returns:
            List of influential paper dictionaries
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:Paper)<-[:CITES]-(citing:Paper)
                WITH p, COUNT(citing) as citation_count
                WHERE citation_count > 0
                RETURN p.id as id,
                       p.title as title,
                       p.year as year,
                       citation_count
                ORDER BY citation_count DESC
                LIMIT $limit
                """,
                limit=limit
            )

            papers = []
            for record in result:
                papers.append({
                    "id": record["id"],
                    "title": record["title"],
                    "year": record["year"],
                    "citation_count": record["citation_count"]
                })

            return papers

    def find_papers_by_author(self, author_name: str) -> List[Dict]:
        """
        Find all papers by an author.

        Args:
            author_name: Author name to search for

        Returns:
            List of paper dictionaries
        """
        if not self.driver:
            return []

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (a:Author {name: $author})-[:AUTHORED]->(p:Paper)
                RETURN p.id as id,
                       p.title as title,
                       p.year as year
                ORDER BY p.year DESC
                """,
                author=author_name
            )

            papers = []
            for record in result:
                papers.append({
                    "id": record["id"],
                    "title": record["title"],
                    "year": record["year"]
                })

            return papers

    def get_citation_network(self, paper_id: str, depth: int = 2) -> Dict:
        """
        Get citation network around a paper.

        Args:
            paper_id: Center paper ID
            depth: How many hops to traverse

        Returns:
            Dictionary with nodes and edges
        """
        if not self.driver:
            return {"nodes": [], "edges": []}

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH path = (p:Paper {id: $paper_id})-[:CITES*1..$depth]-(related:Paper)
                WITH relationships(path) as rels, nodes(path) as nodes
                UNWIND rels as rel
                RETURN DISTINCT
                    startNode(rel).id as source,
                    endNode(rel).id as target,
                    startNode(rel).title as source_title,
                    endNode(rel).title as target_title
                """,
                paper_id=paper_id,
                depth=depth
            )

            edges = []
            nodes_set = set()

            for record in result:
                edges.append({
                    "source": record["source"],
                    "target": record["target"]
                })
                nodes_set.add((record["source"], record["source_title"]))
                nodes_set.add((record["target"], record["target_title"]))

            nodes = [{"id": n[0], "title": n[1]} for n in nodes_set]

            return {
                "nodes": nodes,
                "edges": edges
            }

    def clear_graph(self):
        """Delete all nodes and relationships."""
        if not self.driver:
            return

        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
