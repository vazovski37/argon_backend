"""
RAG Service - Retrieval Augmented Generation
"""
import os
from typing import List, Dict, Optional
from flask import current_app
from sqlalchemy import text
from app.models.knowledge import KnowledgeChunk
from app.extensions import db

# Try to import Google's embedding model
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


class RAGService:
    """
    Retrieval Augmented Generation service using pgvector.
    """
    
    EMBEDDING_DIM = 768  # Google's embedding-001 dimension
    
    def __init__(self, api_key: str = None):
        """Initialize the RAG service."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if GENAI_AVAILABLE and self.api_key:
            genai.configure(api_key=self.api_key)
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text using Google's embedding model.
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats (embedding vector)
        """
        if not GENAI_AVAILABLE:
            raise RuntimeError("google-generativeai package not installed")
        
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY not configured")
        
        result = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        
        return result['embedding']
    
    def ingest_text(self, content: str, category: str, source: str = None,
                    metadata: Dict = None, chunk_size: int = 500, 
                    chunk_overlap: int = 50) -> int:
        """
        Split text into chunks, embed them, and store in database.
        
        Args:
            content: Text content to ingest
            category: Category (history, attraction, restaurant, etc.)
            source: Source file name
            metadata: Additional metadata
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            Number of chunks created
        """
        # Simple chunking (for production, use langchain's text splitter)
        chunks = self._split_text(content, chunk_size, chunk_overlap)
        
        count = 0
        for chunk_text in chunks:
            if not chunk_text.strip():
                continue
            
            try:
                embedding = self.get_embedding(chunk_text)
            except Exception as e:
                print(f"Error getting embedding: {e}")
                embedding = None
            
            chunk = KnowledgeChunk(
                content=chunk_text,
                category=category,
                source_file=source,
                metadata=metadata or {},
                embedding=embedding
            )
            db.session.add(chunk)
            count += 1
        
        db.session.commit()
        return count
    
    def _split_text(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """Simple text splitter."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at a sentence or paragraph
            if end < len(text):
                # Look for paragraph break
                para_break = text.rfind('\n\n', start, end)
                if para_break > start:
                    end = para_break
                else:
                    # Look for sentence break
                    for sep in ['. ', '! ', '? ', '\n']:
                        sent_break = text.rfind(sep, start, end)
                        if sent_break > start:
                            end = sent_break + len(sep)
                            break
            
            chunks.append(text[start:end].strip())
            start = end - overlap
        
        return chunks
    
    def retrieve(self, query: str, k: int = 5, 
                 category: Optional[str] = None,
                 threshold: float = 0.5) -> List[Dict]:
        """
        Retrieve relevant chunks for a query using vector similarity.
        
        Args:
            query: Search query
            k: Number of results to return
            category: Filter by category
            threshold: Minimum similarity threshold
            
        Returns:
            List of matching chunks with similarity scores
        """
        try:
            query_embedding = self.get_embedding(query)
        except Exception as e:
            print(f"Error getting query embedding: {e}")
            # Fallback to text search
            return self._text_search(query, k, category)
        
        # pgvector similarity search
        embedding_str = f"[{','.join(map(str, query_embedding))}]"
        
        sql = """
            SELECT 
                id, content, category, source_file, metadata,
                1 - (embedding <=> :embedding::vector) as similarity
            FROM knowledge_chunks
            WHERE embedding IS NOT NULL
            {category_filter}
            ORDER BY embedding <=> :embedding::vector
            LIMIT :k
        """.format(
            category_filter="AND category = :category" if category else ""
        )
        
        params = {'embedding': embedding_str, 'k': k}
        if category:
            params['category'] = category
        
        results = db.session.execute(text(sql), params).fetchall()
        
        return [
            {
                'id': r.id,
                'content': r.content,
                'category': r.category,
                'source_file': r.source_file,
                'metadata': r.metadata,
                'similarity': float(r.similarity)
            }
            for r in results
            if r.similarity >= threshold
        ]
    
    def _text_search(self, query: str, k: int, category: Optional[str]) -> List[Dict]:
        """Fallback text search when embeddings not available."""
        sql = """
            SELECT id, content, category, source_file, metadata
            FROM knowledge_chunks
            WHERE content ILIKE :query
            {category_filter}
            LIMIT :k
        """.format(
            category_filter="AND category = :category" if category else ""
        )
        
        params = {'query': f'%{query}%', 'k': k}
        if category:
            params['category'] = category
        
        results = db.session.execute(text(sql), params).fetchall()
        
        return [
            {
                'id': r.id,
                'content': r.content,
                'category': r.category,
                'source_file': r.source_file,
                'metadata': r.metadata,
                'similarity': 0.5  # Default score for text search
            }
            for r in results
        ]
    
    def build_context(self, query: str, user_visited: List[str] = None,
                      max_chunks: int = 5) -> str:
        """
        Build context string for AI prompt from retrieved chunks.
        
        Args:
            query: User's query
            user_visited: List of locations the user has visited
            max_chunks: Maximum chunks to include
            
        Returns:
            Context string to add to AI prompt
        """
        chunks = self.retrieve(query, k=max_chunks)
        
        if not chunks:
            return ""
        
        context_parts = ["## Relevant Information\n"]
        
        for chunk in chunks:
            category = chunk['category'].upper() if chunk['category'] else 'INFO'
            context_parts.append(f"[{category}]: {chunk['content']}\n")
        
        if user_visited:
            context_parts.append(f"\n## User has visited: {', '.join(user_visited)}")
        
        return "\n".join(context_parts)
    
    def delete_by_category(self, category: str) -> int:
        """Delete all chunks in a category."""
        result = KnowledgeChunk.query.filter_by(category=category).delete()
        db.session.commit()
        return result
    
    def delete_by_source(self, source_file: str) -> int:
        """Delete all chunks from a source file."""
        result = KnowledgeChunk.query.filter_by(source_file=source_file).delete()
        db.session.commit()
        return result
    
    def get_stats(self) -> Dict:
        """Get statistics about the knowledge base."""
        from sqlalchemy import func
        
        total = KnowledgeChunk.query.count()
        
        categories = db.session.query(
            KnowledgeChunk.category,
            func.count(KnowledgeChunk.id)
        ).group_by(KnowledgeChunk.category).all()
        
        with_embeddings = KnowledgeChunk.query.filter(
            KnowledgeChunk.embedding.isnot(None)
        ).count()
        
        return {
            'total_chunks': total,
            'with_embeddings': with_embeddings,
            'categories': {cat: count for cat, count in categories}
        }




