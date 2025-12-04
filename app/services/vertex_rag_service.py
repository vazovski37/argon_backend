"""
Vertex AI RAG Service - Connects to Google Vertex AI RAG Engine
"""
import os
from typing import List, Dict, Optional
from flask import current_app


class VertexAIRAGService:
    """
    Service for querying Google Vertex AI RAG Corpus.
    
    This connects to an existing RAG Corpus that has been created
    and linked to Google Drive files via the Vertex AI Console.
    """
    
    def __init__(
        self,
        project_id: str = None,
        location: str = None,
        corpus_name: str = None,
    ):
        """
        Initialize the Vertex AI RAG service.
        
        Args:
            project_id: GCP project ID
            location: GCP region (e.g., 'us-central1')
            corpus_name: Full resource name of the RAG corpus
                        Format: projects/{project}/locations/{location}/ragCorpora/{corpus_id}
        """
        self.project_id = project_id or os.getenv('GCP_PROJECT_ID', '')
        self.location = location or os.getenv('VERTEX_AI_LOCATION', 'us-central1')
        self.corpus_name = corpus_name or os.getenv('VERTEX_RAG_CORPUS_NAME', '')
        
        self._initialized = False
        self._rag = None
        
    def _ensure_initialized(self):
        """Lazy initialization of Vertex AI SDK."""
        if self._initialized:
            return
            
        try:
            import vertexai
            from vertexai.preview import rag
            
            # Initialize Vertex AI
            vertexai.init(project=self.project_id, location=self.location)
            self._rag = rag
            self._initialized = True
            
        except ImportError as e:
            raise RuntimeError(
                "google-cloud-aiplatform package not installed. "
                "Install with: pip install google-cloud-aiplatform"
            ) from e
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Vertex AI: {e}") from e
    
    def retrieve(
        self,
        query: str,
        similarity_top_k: int = 5,
        vector_distance_threshold: float = 0.5,
    ) -> List[Dict]:
        """
        Retrieve relevant contexts from the RAG Corpus.
        
        Args:
            query: The search query
            similarity_top_k: Number of top results to return
            vector_distance_threshold: Minimum similarity threshold (0-1)
            
        Returns:
            List of relevant context chunks with metadata
        """
        self._ensure_initialized()
        
        if not self.corpus_name:
            raise ValueError("RAG Corpus name not configured. Set VERTEX_RAG_CORPUS_NAME env variable.")
        
        try:
            # Query the RAG corpus
            response = self._rag.retrieval_query(
                rag_resources=[
                    self._rag.RagResource(
                        rag_corpus=self.corpus_name,
                    )
                ],
                text=query,
                similarity_top_k=similarity_top_k,
                vector_distance_threshold=vector_distance_threshold,
            )
            
            # Process results
            results = []
            if response and response.contexts:
                for context in response.contexts.contexts:
                    results.append({
                        'content': context.text,
                        'source': getattr(context, 'source_uri', None) or getattr(context, 'uri', 'Unknown'),
                        'score': getattr(context, 'distance', 0.0),
                        'metadata': {
                            'source_uri': getattr(context, 'source_uri', None),
                        }
                    })
            
            return results
            
        except Exception as e:
            print(f"[VertexRAG] Error retrieving context: {e}")
            raise
    
    def build_context(
        self,
        query: str,
        max_chunks: int = 5,
        user_visited: List[str] = None,
    ) -> str:
        """
        Build a context string from retrieved RAG results for AI prompts.
        
        Args:
            query: User's question
            max_chunks: Maximum number of chunks to include
            user_visited: List of locations user has visited
            
        Returns:
            Formatted context string
        """
        try:
            results = self.retrieve(query, similarity_top_k=max_chunks)
        except Exception as e:
            print(f"[VertexRAG] Retrieval failed: {e}")
            return ""
        
        if not results:
            return ""
        
        context_parts = ["## Relevant Information from Knowledge Base\n"]
        
        for i, result in enumerate(results, 1):
            content = result.get('content', '').strip()
            source = result.get('source', 'Unknown')
            
            if content:
                # Extract source filename from path
                source_name = source.split('/')[-1] if source else 'Unknown'
                context_parts.append(f"**Source {i}** ({source_name}):\n{content}\n")
        
        if user_visited:
            context_parts.append(f"\n## User has already visited: {', '.join(user_visited)}")
        
        return "\n".join(context_parts)
    
    def get_corpus_info(self) -> Dict:
        """
        Get information about the configured RAG corpus.
        
        Returns:
            Dictionary with corpus information
        """
        self._ensure_initialized()
        
        if not self.corpus_name:
            return {
                'configured': False,
                'error': 'RAG Corpus name not configured'
            }
        
        try:
            corpus = self._rag.get_corpus(name=self.corpus_name)
            return {
                'configured': True,
                'name': corpus.name,
                'display_name': getattr(corpus, 'display_name', None),
                'description': getattr(corpus, 'description', None),
                'create_time': str(getattr(corpus, 'create_time', None)),
            }
        except Exception as e:
            return {
                'configured': True,
                'name': self.corpus_name,
                'error': str(e)
            }
    
    def list_corpus_files(self) -> List[Dict]:
        """
        List files in the RAG corpus.
        
        Returns:
            List of file information dictionaries
        """
        self._ensure_initialized()
        
        if not self.corpus_name:
            return []
        
        try:
            files = self._rag.list_files(corpus_name=self.corpus_name)
            return [
                {
                    'name': f.name,
                    'display_name': getattr(f, 'display_name', None),
                    'size_bytes': getattr(f, 'size_bytes', None),
                    'create_time': str(getattr(f, 'create_time', None)),
                }
                for f in files
            ]
        except Exception as e:
            print(f"[VertexRAG] Error listing files: {e}")
            return []


# Singleton instance
_vertex_rag_service: Optional[VertexAIRAGService] = None


def get_vertex_rag_service() -> VertexAIRAGService:
    """Get or create the Vertex AI RAG service singleton."""
    global _vertex_rag_service
    
    if _vertex_rag_service is None:
        _vertex_rag_service = VertexAIRAGService()
    
    return _vertex_rag_service

