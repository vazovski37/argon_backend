"""
RAG (Retrieval Augmented Generation) API
"""
import os
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_current_user
from app.services.rag_service import RAGService
from app.services.vertex_rag_service import get_vertex_rag_service, VertexAIRAGService
from app.models.knowledge import KnowledgeChunk
from app.extensions import db

rag_bp = Blueprint('rag', __name__)


def get_rag_service():
    """Get RAG service instance."""
    api_key = current_app.config.get('GEMINI_API_KEY')
    return RAGService(api_key=api_key)


# ============================================
# Vertex AI RAG Endpoints
# ============================================

@rag_bp.route('/vertex/query', methods=['POST'])
@jwt_required(optional=True)
def vertex_query():
    """
    Query the Vertex AI RAG Corpus for relevant context.
    
    This endpoint connects to your Google Cloud Vertex AI RAG Engine
    and retrieves relevant information from your Google Drive-linked corpus.
    
    Request body:
        query: Search query (required)
        top_k: Number of results (default 5)
        threshold: Similarity threshold 0-1 (default 0.5)
    
    Returns:
        {
            "query": "...",
            "results": [...],
            "context": "formatted context string"
        }
    """
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    top_k = data.get('top_k', 5)
    threshold = data.get('threshold', 0.5)
    
    try:
        service = get_vertex_rag_service()
        results = service.retrieve(
            query=query,
            similarity_top_k=top_k,
            vector_distance_threshold=threshold
        )
        
        # Get user's visited locations for context
        user_visited = []
        user = get_current_user()
        if user:
            from app.models.location import UserLocationVisit
            visits = UserLocationVisit.query.filter_by(user_id=user.id).all()
            user_visited = [v.location.name for v in visits if v.location]
        
        # Build context string
        context = service.build_context(query, max_chunks=top_k, user_visited=user_visited)
        
        return jsonify({
            'query': query,
            'results': results,
            'context': context,
            'total': len(results)
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'RAG query failed: {str(e)}'}), 500


@rag_bp.route('/vertex/context', methods=['POST'])
@jwt_required(optional=True)
def vertex_context():
    """
    Get formatted context from Vertex AI RAG for AI prompts.
    
    This is the main endpoint to call when your AI needs Poti-specific information.
    It retrieves relevant chunks from the RAG corpus and formats them for use
    in AI prompts.
    
    Request body:
        query: User's question (required)
        max_chunks: Maximum chunks to include (default 5)
    
    Returns:
        {
            "context": "formatted context string",
            "user_visited": ["location1", "location2"],
            "source": "vertex_ai"
        }
    """
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    max_chunks = data.get('max_chunks', 5)
    
    # Get user's visited locations
    user_visited = []
    user = get_current_user()
    if user:
        from app.models.location import UserLocationVisit
        visits = UserLocationVisit.query.filter_by(user_id=user.id).all()
        user_visited = [v.location.name for v in visits if v.location]
    
    try:
        service = get_vertex_rag_service()
        context = service.build_context(
            query=query,
            max_chunks=max_chunks,
            user_visited=user_visited
        )
        
        return jsonify({
            'context': context,
            'user_visited': user_visited,
            'source': 'vertex_ai'
        })
        
    except Exception as e:
        # Fallback to local RAG if Vertex AI fails
        print(f"[RAG] Vertex AI failed, falling back to local: {e}")
        
        local_rag = get_rag_service()
        context = local_rag.build_context(query, user_visited=user_visited, max_chunks=max_chunks)
        
        return jsonify({
            'context': context,
            'user_visited': user_visited,
            'source': 'local_fallback'
        })


@rag_bp.route('/vertex/info', methods=['GET'])
def vertex_info():
    """
    Get information about the Vertex AI RAG Corpus configuration.
    
    Returns corpus info and status.
    """
    try:
        service = get_vertex_rag_service()
        info = service.get_corpus_info()
        
        return jsonify({
            'project_id': service.project_id,
            'location': service.location,
            'corpus': info
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e),
            'configured': False
        }), 500


@rag_bp.route('/vertex/files', methods=['GET'])
@jwt_required()
def vertex_files():
    """
    List files in the Vertex AI RAG Corpus (admin only).
    """
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        service = get_vertex_rag_service()
        files = service.list_corpus_files()
        
        return jsonify({
            'files': files,
            'total': len(files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================
# Original Local RAG Endpoints
# ============================================


@rag_bp.route('/search', methods=['POST'])
def search():
    """
    Search the knowledge base.
    
    Request body:
        query: Search query (required)
        k: Number of results (default 5)
        category: Filter by category (optional)
    """
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    k = data.get('k', 5)
    category = data.get('category')
    
    rag = get_rag_service()
    results = rag.retrieve(query, k=k, category=category)
    
    return jsonify({
        'query': query,
        'results': results,
        'total': len(results)
    })


@rag_bp.route('/context', methods=['POST'])
@jwt_required(optional=True)
def get_context():
    """
    Get AI context for a query.
    
    Request body:
        query: User's question (required)
        max_chunks: Maximum chunks to include (default 5)
    """
    data = request.get_json()
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    max_chunks = data.get('max_chunks', 5)
    
    # Get user's visited locations if authenticated
    user_visited = []
    user = get_current_user()
    if user:
        from app.models.location import UserLocationVisit
        visits = UserLocationVisit.query.filter_by(user_id=user.id).all()
        user_visited = [v.location.name for v in visits if v.location]
    
    rag = get_rag_service()
    context = rag.build_context(query, user_visited=user_visited, max_chunks=max_chunks)
    
    return jsonify({
        'context': context,
        'user_visited': user_visited
    })


@rag_bp.route('/ingest', methods=['POST'])
@jwt_required()
def ingest():
    """
    Ingest content into the knowledge base (admin only).
    
    Request body:
        content: Text content to ingest (required)
        category: Category (required)
        source: Source file name (optional)
        metadata: Additional metadata (optional)
        chunk_size: Characters per chunk (default 500)
        chunk_overlap: Overlap between chunks (default 50)
    """
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    content = data.get('content', '').strip()
    category = data.get('category', '').strip()
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
    
    if not category:
        return jsonify({'error': 'Category is required'}), 400
    
    source = data.get('source')
    metadata = data.get('metadata', {})
    chunk_size = data.get('chunk_size', 500)
    chunk_overlap = data.get('chunk_overlap', 50)
    
    rag = get_rag_service()
    
    try:
        count = rag.ingest_text(
            content=content,
            category=category,
            source=source,
            metadata=metadata,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        return jsonify({
            'success': True,
            'chunks_created': count,
            'category': category,
            'source': source
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/ingest-file', methods=['POST'])
@jwt_required()
def ingest_file():
    """
    Ingest a file into the knowledge base (admin only).
    """
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    category = request.form.get('category', 'general')
    
    # Read file content
    content = file.read().decode('utf-8')
    
    rag = get_rag_service()
    
    try:
        count = rag.ingest_text(
            content=content,
            category=category,
            source=file.filename
        )
        
        return jsonify({
            'success': True,
            'chunks_created': count,
            'category': category,
            'source': file.filename
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@rag_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get knowledge base statistics."""
    rag = get_rag_service()
    stats = rag.get_stats()
    return jsonify(stats)


@rag_bp.route('/chunks', methods=['GET'])
def list_chunks():
    """List knowledge chunks with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category = request.args.get('category')
    
    query = KnowledgeChunk.query
    if category:
        query = query.filter_by(category=category)
    
    pagination = query.order_by(KnowledgeChunk.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'chunks': [c.to_dict() for c in pagination.items],
        'page': page,
        'per_page': per_page,
        'total': pagination.total,
        'pages': pagination.pages
    })


@rag_bp.route('/chunks/<chunk_id>', methods=['DELETE'])
@jwt_required()
def delete_chunk(chunk_id: str):
    """Delete a knowledge chunk (admin only)."""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    chunk = KnowledgeChunk.query.get_or_404(chunk_id)
    db.session.delete(chunk)
    db.session.commit()
    
    return jsonify({'message': 'Chunk deleted'})


@rag_bp.route('/clear/<category>', methods=['DELETE'])
@jwt_required()
def clear_category(category: str):
    """Clear all chunks in a category (admin only)."""
    user = get_current_user()
    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403
    
    rag = get_rag_service()
    count = rag.delete_by_category(category)
    
    return jsonify({
        'message': f'Deleted {count} chunks from category {category}',
        'deleted': count
    })




