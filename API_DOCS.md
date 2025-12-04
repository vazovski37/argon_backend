# Argonauts API Documentation

Base URL: `http://localhost:5000/api`

## Authentication

All endpoints marked with 🔒 require a valid JWT token in the `Authorization` header:
```
Authorization: Bearer <your_jwt_token>
```

Endpoints marked with 👑 require admin privileges.

---

## 🔐 Auth Endpoints

### POST `/auth/register`
Register a new user with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}
```

**Response (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar_url": null,
    "is_admin": false
  }
}
```

---

### POST `/auth/login`
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { ... }
}
```

---

### POST `/auth/google`
Authenticate with Google OAuth.

**Request Body:**
```json
{
  "credential": "google_id_token_from_frontend"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": { ... }
}
```

**Use Case:** Frontend uses Google Sign-In button, sends the credential token to this endpoint.

---

### GET `/auth/me` 🔒
Get current authenticated user info.

**Response (200):**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "name": "John Doe",
    "avatar_url": "https://...",
    "is_admin": false
  },
  "progress": {
    "current_level": 5,
    "current_rank": "Explorer",
    "total_xp": 1250,
    "locations_visited": 3,
    "quests_completed": 2,
    "photos_taken": 5
  }
}
```

---

### PATCH `/auth/me` 🔒
Update current user's profile.

**Request Body:**
```json
{
  "name": "New Name",
  "avatar_url": "https://new-avatar-url.com/image.jpg"
}
```

**Response (200):**
```json
{
  "user": { ... }
}
```

---

### POST `/auth/change-password` 🔒
Change user's password.

**Request Body:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

---

## 📍 Locations Endpoints

### GET `/locations/`
Get all locations.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category (attraction, restaurant, landmark, nature, historical) |

**Response (200):**
```json
{
  "locations": [
    {
      "id": "loc-lighthouse",
      "name": "Poti Lighthouse",
      "name_ka": "ფოთის შუქურა",
      "description": "Historic lighthouse built in 1864...",
      "category": "attraction",
      "latitude": 42.1461,
      "longitude": 41.6719,
      "xp_reward": 75,
      "image_url": null,
      "metadata": {}
    }
  ],
  "total": 7
}
```

---

### GET `/locations/<location_id>`
Get a single location by ID.

**Response (200):**
```json
{
  "id": "loc-lighthouse",
  "name": "Poti Lighthouse",
  ...
}
```

---

### GET `/locations/search`
Search locations by name or description.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Search query (required) |

**Example:** `GET /locations/search?q=lighthouse`

**Response (200):**
```json
{
  "locations": [...],
  "total": 1
}
```

---

### GET `/locations/nearby`
Get locations near coordinates.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `lat` | float | Latitude (required) |
| `lng` | float | Longitude (required) |
| `radius` | float | Radius in km (default: 5) |

**Example:** `GET /locations/nearby?lat=42.1461&lng=41.6719&radius=2`

**Response (200):**
```json
{
  "locations": [
    {
      "id": "loc-lighthouse",
      "name": "Poti Lighthouse",
      "distance_km": 0.15,
      ...
    }
  ],
  "total": 3
}
```

---

### GET `/locations/categories`
Get all location categories with counts.

**Response (200):**
```json
{
  "categories": [
    { "name": "attraction", "count": 2 },
    { "name": "nature", "count": 3 },
    { "name": "landmark", "count": 2 }
  ]
}
```

---

### POST `/locations/` 🔒👑
Create a new location (admin only).

**Request Body:**
```json
{
  "name": "New Location",
  "name_ka": "ახალი ადგილი",
  "description": "Description here",
  "category": "attraction",
  "latitude": 42.15,
  "longitude": 41.67,
  "xp_reward": 50,
  "image_url": "https://...",
  "metadata": { "opening_hours": "9am-5pm" }
}
```

---

### PUT `/locations/<location_id>` 🔒👑
Update a location (admin only).

---

### DELETE `/locations/<location_id>` 🔒👑
Delete a location (admin only).

---

## 🎮 Game Endpoints

### GET `/game/progress` 🔒
Get current user's game progress.

**Response (200):**
```json
{
  "current_level": 5,
  "current_rank": "Explorer",
  "total_xp": 1250,
  "xp_for_current_level": 1000,
  "xp_for_next_level": 1500,
  "locations_visited": 3,
  "quests_completed": 2,
  "photos_taken": 5,
  "phrases_learned": ["გამარჯობა", "მადლობა"]
}
```

---

### POST `/game/visit-location` 🔒
Record a location visit and award XP.

**Request Body:**
```json
{
  "location_id": "loc-lighthouse"
}
```
Or:
```json
{
  "location_name": "Poti Lighthouse"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Visited Poti Lighthouse!",
  "xp_earned": 75,
  "level_up": false,
  "new_achievements": [
    {
      "id": "ach-first-steps",
      "name": "First Steps",
      "description": "Visit your first location"
    }
  ],
  "location": { ... }
}
```

**Use Case:** Call this when user physically visits a location (verified by GPS).

---

### POST `/game/learn-phrase` 🔒
Record a learned Georgian phrase.

**Request Body:**
```json
{
  "phrase": "გამარჯობა",
  "meaning": "Hello"
}
```

**Response (200):**
```json
{
  "success": true,
  "message": "Learned phrase: გამარჯობა",
  "xp_earned": 10,
  "new_achievements": []
}
```

---

### GET `/game/achievements` 🔒
Get all achievements and user's earned achievements.

**Response (200):**
```json
{
  "achievements": [
    {
      "id": "ach-first-steps",
      "name": "First Steps",
      "description": "Visit your first location in Poti",
      "icon": "👣",
      "xp_reward": 50,
      "earned": true,
      "earned_at": "2024-01-15T10:30:00"
    },
    {
      "id": "ach-explorer",
      "name": "Explorer",
      "description": "Visit 5 different locations",
      "icon": "🧭",
      "xp_reward": 100,
      "earned": false
    }
  ],
  "total_earned": 3,
  "total_available": 10
}
```

---

### GET `/game/visited-locations` 🔒
Get all locations user has visited.

**Response (200):**
```json
{
  "visits": [
    {
      "id": "visit-uuid",
      "location_id": "loc-lighthouse",
      "visited_at": "2024-01-15T10:30:00",
      "location": { ... }
    }
  ],
  "total": 3
}
```

---

### GET `/game/stats` 🔒
Get detailed user statistics.

**Response (200):**
```json
{
  "level": 5,
  "rank": "Explorer",
  "total_xp": 1250,
  "xp_to_next_level": 250,
  "xp_progress_percent": 50,
  "locations_visited": 3,
  "achievements_earned": 4,
  "quests_completed": 2,
  "photos_taken": 5,
  "phrases_learned": 8
}
```

---

### GET `/game/leaderboard`
Get the global leaderboard (public).

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `limit` | int | Number of users (default: 10) |

**Response (200):**
```json
{
  "leaderboard": [
    {
      "rank": 1,
      "user_id": "uuid",
      "name": "Top Player",
      "avatar_url": "https://...",
      "level": 15,
      "title": "Master Explorer",
      "total_xp": 5000,
      "locations_visited": 7
    }
  ]
}
```

---

## 🗺️ Quests Endpoints

### GET `/quests/`
Get all available quests.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `daily` | bool | Include daily quests (default: true) |

**Response (200):**
```json
{
  "quests": [
    {
      "id": "quest-argonaut",
      "name": "The Argonaut's Journey",
      "description": "Follow in the footsteps of Jason and the Argonauts",
      "story_intro": "Long ago, Jason and his Argonauts sailed...",
      "xp_reward": 500,
      "difficulty": "medium",
      "estimated_time": 60,
      "is_daily": false,
      "steps": [
        {
          "title": "The Monument",
          "description": "Visit the Argonauts Monument",
          "location_id": "loc-argonauts"
        }
      ]
    }
  ],
  "total": 3
}
```

---

### GET `/quests/<quest_id>`
Get a single quest by ID.

---

### GET `/quests/my-quests` 🔒
Get current user's quests (active and completed).

**Response (200):**
```json
{
  "active": [
    {
      "id": "user-quest-uuid",
      "quest_id": "quest-argonaut",
      "status": "active",
      "current_step": 1,
      "started_at": "2024-01-15T10:00:00",
      "quest": { ... }
    }
  ],
  "completed": [...],
  "total_active": 1,
  "total_completed": 2
}
```

---

### POST `/quests/<quest_id>/start` 🔒
Start a quest for the current user.

**Response (200):**
```json
{
  "success": true,
  "message": "Started quest: The Argonaut's Journey",
  "user_quest": { ... },
  "story_intro": "Long ago, Jason and his Argonauts sailed..."
}
```

---

### POST `/quests/<quest_id>/advance` 🔒
Advance to the next step in a quest.

**Response (200):**
```json
{
  "success": true,
  "current_step": 2,
  "completed": false,
  "message": "Advanced to step 2",
  "next_step": {
    "title": "The Port",
    "description": "Visit the port where the Argonauts may have landed"
  }
}
```

On completion:
```json
{
  "success": true,
  "completed": true,
  "xp_earned": 500,
  "level_up": true,
  "new_level": 6,
  "message": "Completed quest: The Argonaut's Journey! Earned 500 XP."
}
```

---

### POST `/quests/<quest_id>/abandon` 🔒
Abandon an active quest.

---

### POST `/quests/` 🔒👑
Create a new quest (admin only).

---

## 📸 Photos Endpoints

### GET `/photos/` 🔒
Get current user's photos.

**Response (200):**
```json
{
  "photos": [
    {
      "id": "photo-uuid",
      "user_id": "user-uuid",
      "location_id": "loc-lighthouse",
      "file_name": "lighthouse.jpg",
      "url": "https://storage.googleapis.com/argonauts-media-storage/photos/user-id/uuid.jpg",
      "caption": "Beautiful sunset view!",
      "is_selfie": false,
      "latitude": 42.1461,
      "longitude": 41.6719,
      "uploaded_at": "2024-01-15T10:30:00",
      "location": { ... }
    }
  ],
  "total": 5
}
```

---

### GET `/photos/location/<location_id>`
Get all photos for a location (public).

---

### POST `/photos/upload` 🔒
Upload a new photo to Google Cloud Storage.

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | Image file (required) - png, jpg, jpeg, gif, webp |
| `location_id` | string | Associated location ID (optional) |
| `caption` | string | Photo caption (optional) |
| `is_selfie` | bool | Whether it's a selfie (optional) |
| `latitude` | float | GPS latitude (optional) |
| `longitude` | float | GPS longitude (optional) |

**Response (201):**
```json
{
  "photo": {
    "id": "photo-uuid",
    "url": "https://storage.googleapis.com/...",
    ...
  },
  "xp_earned": 10,
  "new_achievements": []
}
```

**Use Case:** User takes a photo at a location, uploads with GPS coords and location_id.

---

### DELETE `/photos/<photo_id>` 🔒
Delete a photo (owner or admin only).

---

### GET `/photos/file/<filepath>`
Redirect to the GCS public URL for a photo.

---

## 🤖 RAG (AI) Endpoints

### Vertex AI RAG (Primary)

These endpoints connect to Google Vertex AI RAG Engine for retrieving information from your Google Drive-linked corpus.

### POST `/rag/vertex/query`
Query the Vertex AI RAG Corpus for relevant context.

**Request Body:**
```json
{
  "query": "What is the history of Poti?",
  "top_k": 5,
  "threshold": 0.5
}
```

**Response (200):**
```json
{
  "query": "What is the history of Poti?",
  "results": [
    {
      "content": "Poti is an ancient city located on the eastern coast of the Black Sea...",
      "source": "poti_history.pdf",
      "score": 0.89,
      "metadata": {
        "source_uri": "gs://bucket/poti_history.pdf"
      }
    }
  ],
  "context": "## Relevant Information from Knowledge Base\n\n**Source 1** (poti_history.pdf):\n...",
  "total": 3
}
```

---

### POST `/rag/vertex/context`
Get formatted context from Vertex AI RAG for AI prompts. **This is the main endpoint to call when your AI needs Poti-specific information.**

**Request Body:**
```json
{
  "query": "Tell me about the Argonauts in Poti",
  "max_chunks": 5
}
```

**Response (200):**
```json
{
  "context": "## Relevant Information from Knowledge Base\n\n**Source 1** (argonauts.pdf):\nAccording to Greek mythology, Jason and the Argonauts sailed to Colchis...\n\n**Source 2** (poti_history.pdf):\nPoti is believed to be the ancient Phasis, where the Argonauts landed...\n\n## User has already visited: Poti Lighthouse, Argonauts Monument",
  "user_visited": ["Poti Lighthouse", "Argonauts Monument"],
  "source": "vertex_ai"
}
```

**Use Case:** When the AI receives a question about Poti:
1. Call this endpoint with the user's question
2. Include the returned `context` in your AI prompt
3. The AI can now answer with accurate Poti-specific information

**Note:** If Vertex AI is unavailable, falls back to local RAG with `source: "local_fallback"`.

---

### GET `/rag/vertex/info`
Get information about the Vertex AI RAG Corpus configuration.

**Response (200):**
```json
{
  "project_id": "your-gcp-project",
  "location": "us-central1",
  "corpus": {
    "configured": true,
    "name": "projects/your-project/locations/us-central1/ragCorpora/123456",
    "display_name": "Poti Knowledge Base",
    "description": "Information about Poti, Georgia"
  }
}
```

---

### GET `/rag/vertex/files` 🔒👑
List files in the Vertex AI RAG Corpus (admin only).

**Response (200):**
```json
{
  "files": [
    {
      "name": "projects/.../ragFiles/123",
      "display_name": "poti_history.pdf",
      "size_bytes": 125000,
      "create_time": "2024-01-15T10:00:00"
    }
  ],
  "total": 5
}
```

---

### Local RAG (Fallback)

These endpoints use the local pgvector-based RAG when Vertex AI is unavailable.

### POST `/rag/search`
Search the knowledge base.

**Request Body:**
```json
{
  "query": "history of poti",
  "k": 5,
  "category": "history"
}
```

**Response (200):**
```json
{
  "query": "history of poti",
  "results": [
    {
      "id": "know-hist-1",
      "content": "Poti is an ancient city located on the eastern coast...",
      "category": "history",
      "score": 0.92
    }
  ],
  "total": 3
}
```

---

### POST `/rag/context`
Get AI context for a query (use this to build prompts).

**Request Body:**
```json
{
  "query": "What should I visit in Poti?",
  "max_chunks": 5
}
```

**Response (200):**
```json
{
  "context": "Based on the knowledge base:\n\n1. The Poti Lighthouse, built in 1864...\n2. The Argonauts Monument...",
  "user_visited": ["Poti Lighthouse"]
}
```

**Use Case:** Frontend sends user question → gets context → combines with question → sends to AI chat API.

---

### POST `/rag/ingest` 🔒👑
Ingest content into the knowledge base (admin only).

**Request Body:**
```json
{
  "content": "Long text about Poti history...",
  "category": "history",
  "source": "poti_history.md",
  "metadata": { "topic": "origins" },
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**Response (200):**
```json
{
  "success": true,
  "chunks_created": 5,
  "category": "history",
  "source": "poti_history.md"
}
```

---

### POST `/rag/ingest-file` 🔒👑
Ingest a file into the knowledge base (admin only).

**Request:** `multipart/form-data`

| Field | Type | Description |
|-------|------|-------------|
| `file` | file | Text file (required) |
| `category` | string | Category (default: general) |

---

### GET `/rag/stats`
Get knowledge base statistics.

**Response (200):**
```json
{
  "total_chunks": 45,
  "categories": {
    "history": 12,
    "attraction": 15,
    "restaurant": 8,
    "practical": 10
  },
  "sources": ["poti_history.md", "attractions.md", "food.md"]
}
```

---

### GET `/rag/chunks`
List knowledge chunks with pagination.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | int | Page number (default: 1) |
| `per_page` | int | Items per page (default: 20) |
| `category` | string | Filter by category |

---

### DELETE `/rag/chunks/<chunk_id>` 🔒👑
Delete a knowledge chunk (admin only).

---

### DELETE `/rag/clear/<category>` 🔒👑
Clear all chunks in a category (admin only).

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "error": "Error message here"
}
```

Common HTTP status codes:
| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid input |
| 401 | Unauthorized - Invalid or missing token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error |

---

## Data Types

### User Object
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "avatar_url": "https://...",
  "google_id": "google-oauth-id",
  "is_admin": false,
  "is_active": true,
  "created_at": "2024-01-01T00:00:00"
}
```

### Location Object
```json
{
  "id": "loc-lighthouse",
  "name": "Poti Lighthouse",
  "name_ka": "ფოთის შუქურა",
  "description": "Historic lighthouse built in 1864...",
  "category": "attraction",
  "latitude": 42.1461,
  "longitude": 41.6719,
  "xp_reward": 75,
  "image_url": "https://...",
  "metadata": {}
}
```

### Quest Object
```json
{
  "id": "quest-argonaut",
  "name": "The Argonaut's Journey",
  "description": "Follow in the footsteps of Jason...",
  "story_intro": "Long ago...",
  "xp_reward": 500,
  "difficulty": "medium",
  "estimated_time": 60,
  "is_daily": false,
  "steps": [...]
}
```

### Achievement Object
```json
{
  "id": "ach-first-steps",
  "name": "First Steps",
  "description": "Visit your first location in Poti",
  "icon": "👣",
  "xp_reward": 50,
  "requirement_type": "visits",
  "requirement_value": 1,
  "category": "exploration",
  "is_secret": false
}
```

---

## Categories Reference

### Location Categories
- `attraction` - Tourist attractions
- `restaurant` - Food & dining
- `landmark` - Notable landmarks
- `nature` - Natural sites
- `historical` - Historical sites

### Achievement Categories
- `exploration` - Visit-based achievements
- `language` - Georgian phrase achievements
- `photos` - Photography achievements
- `special` - Special location achievements

### Knowledge Categories
- `history` - Historical information
- `attraction` - Attraction descriptions
- `restaurant` - Food & dining info
- `practical` - Practical travel info
- `phrase` - Georgian phrases

