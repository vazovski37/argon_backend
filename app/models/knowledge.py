"""
Knowledge Chunk Model for RAG
"""
from datetime import datetime
from uuid import uuid4
from app.extensions import db
from pgvector.sqlalchemy import Vector


class KnowledgeChunk(db.Model):
    """Knowledge chunks with vector embeddings for RAG."""
    
    __tablename__ = 'knowledge_chunks'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    
    # Content
    content = db.Column(db.Text, nullable=False)
    
    # Category: history, attraction, restaurant, practical, phrase
    category = db.Column(db.String(50), nullable=True, index=True)
    
    # Source file this chunk came from
    source_file = db.Column(db.String(255), nullable=True)
    
    # Additional data
    extra_data = db.Column(db.JSON, default=dict)
    
    # Vector embedding (768 dimensions for Google's embedding model)
    embedding = db.Column(Vector(768), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> dict:
        """Convert to dictionary (without embedding)."""
        return {
            'id': self.id,
            'content': self.content,
            'category': self.category,
            'source_file': self.source_file,
            'metadata': self.extra_data or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f'<KnowledgeChunk {self.id[:8]} ({self.category})>'


# Helper function to create vector index
def create_vector_index():
    """Create IVFFlat index for vector similarity search."""
    from sqlalchemy import text
    db.session.execute(text("""
        CREATE INDEX IF NOT EXISTS idx_knowledge_embedding 
        ON knowledge_chunks 
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """))
    db.session.commit()





