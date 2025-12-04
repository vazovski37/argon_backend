# Argonauts Backend

Flask backend for the Argonauts Poti AI Guide application with RAG (Retrieval Augmented Generation) support.

## Features

- 🔐 **Authentication**: JWT-based auth with Google OAuth support
- 🎮 **Gamification**: XP, levels, achievements, quests
- 📍 **Locations**: Poti points of interest management
- 📸 **Photos**: User photo uploads with location tagging
- 🧠 **RAG**: Vector-based knowledge retrieval using pgvector
- 📊 **Analytics**: Leaderboards and user statistics

## Tech Stack

- **Framework**: Flask 3.x
- **Database**: PostgreSQL 16 with pgvector extension
- **Cache**: Redis
- **Storage**: MinIO (S3-compatible)
- **AI**: Google Gemini for embeddings

## Quick Start

### Using Docker (Recommended)

1. Copy environment file:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` with your API keys:
   ```
   GEMINI_API_KEY=your-gemini-api-key
   GOOGLE_CLIENT_ID=your-google-client-id
   ```

3. Start all services:
   ```bash
   docker-compose up -d
   ```

4. The API will be available at `http://localhost:5000`

### Manual Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL with pgvector:
   ```sql
   CREATE DATABASE argonauts;
   CREATE EXTENSION vector;
   ```

4. Run the application:
   ```bash
   python run.py
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with email/password
- `POST /api/auth/google` - Google OAuth login
- `GET /api/auth/me` - Get current user

### Game Progress
- `GET /api/game/progress` - Get user's game progress
- `POST /api/game/visit-location` - Record location visit
- `POST /api/game/learn-phrase` - Record learned phrase
- `GET /api/game/achievements` - Get all achievements
- `GET /api/game/stats` - Get detailed statistics
- `GET /api/game/leaderboard` - Get global leaderboard

### Locations
- `GET /api/locations` - List all locations
- `GET /api/locations/:id` - Get single location
- `GET /api/locations/search?q=` - Search locations
- `GET /api/locations/nearby?lat=&lng=` - Get nearby locations

### Quests
- `GET /api/quests` - List all quests
- `GET /api/quests/my-quests` - Get user's quests
- `POST /api/quests/:id/start` - Start a quest
- `POST /api/quests/:id/advance` - Advance quest step

### Photos
- `GET /api/photos` - Get user's photos
- `POST /api/photos/upload` - Upload a photo
- `DELETE /api/photos/:id` - Delete a photo

### RAG (Knowledge Base)
- `POST /api/rag/search` - Search knowledge base
- `POST /api/rag/context` - Get AI context for query
- `GET /api/rag/stats` - Get knowledge base statistics
- `POST /api/rag/ingest` - Add content (admin only)

## Project Structure

```
backend/
├── app/
│   ├── __init__.py      # Flask app factory
│   ├── config.py        # Configuration
│   ├── extensions.py    # Flask extensions
│   ├── models/          # SQLAlchemy models
│   ├── api/             # API blueprints
│   ├── services/        # Business logic
│   └── utils/           # Utilities
├── knowledge/           # RAG source documents
├── migrations/          # Database migrations
├── uploads/             # User uploads
├── docker-compose.yml   # Docker setup
├── Dockerfile
├── requirements.txt
└── run.py               # Entry point
```

## Database Schema

The database includes these main tables:
- `users` - User accounts
- `user_progress` - Game state (XP, level, rank)
- `locations` - Points of interest
- `user_location_visits` - Visit records
- `achievements` - Available achievements
- `user_achievements` - Earned achievements
- `quests` - Available quests
- `user_quests` - Quest progress
- `photos` - User photos
- `knowledge_chunks` - RAG embeddings

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `JWT_SECRET_KEY` | JWT signing key | Yes |
| `GEMINI_API_KEY` | Google Gemini API key | Yes (for RAG) |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | Yes (for OAuth) |
| `REDIS_URL` | Redis connection string | No |
| `S3_ENDPOINT` | MinIO/S3 endpoint | No |

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black app/
```

## License

MIT




