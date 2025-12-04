# Argonauts Database Schema Documentation

## Overview

This document describes the complete database schema for the Argonauts Poti AI Guide application. The database uses PostgreSQL 16 with the pgvector extension for vector similarity search (RAG functionality).

**Database Name:** `argonauts`  
**PostgreSQL Version:** 16  
**pgvector Extension:** 0.8.1  
**Total Tables:** 10

---

## Connection Information

### Docker Connection
```bash
docker exec -it argonauts-db psql -U postgres -d argonauts
```

### Direct Connection
- **Host:** localhost
- **Port:** 5432
- **Database:** argonauts
- **Username:** postgres
- **Password:** postgres

---

## Database Extensions

### pgvector (v0.8.1)
Used for vector similarity search in the RAG (Retrieval Augmented Generation) system. Enables storing and querying embeddings for the knowledge base.

---

## Table Summary

| Table Name | Description | Row Count |
|------------|-------------|-----------|
| `users` | User accounts and authentication | 1 |
| `user_progress` | User game progress (XP, level, rank) | 1 |
| `locations` | Points of interest in Poti | 7 |
| `user_location_visits` | Records of user visits to locations | 1 |
| `achievements` | Available achievements | 10 |
| `user_achievements` | User-earned achievements | 1 |
| `quests` | Available quests | 3 |
| `user_quests` | User quest progress | 0 |
| `photos` | User-uploaded photos | 0 |
| `knowledge_chunks` | RAG knowledge base with embeddings | 6 |

---

## Table Details

### 1. `users`

User accounts and authentication information.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `email` | VARCHAR(255) | NOT NULL | - | User email (unique) |
| `password_hash` | VARCHAR(255) | NULL | - | Hashed password (for email/password auth) |
| `google_id` | VARCHAR(255) | NULL | - | Google OAuth ID (unique) |
| `name` | VARCHAR(255) | NULL | - | User display name |
| `avatar_url` | TEXT | NULL | - | Profile picture URL |
| `is_active` | BOOLEAN | NULL | - | Account active status |
| `is_admin` | BOOLEAN | NULL | - | Admin privileges |
| `created_at` | TIMESTAMP | NULL | - | Account creation timestamp |
| `updated_at` | TIMESTAMP | NULL | - | Last update timestamp |

**Indexes:**
- Primary Key: `users_pkey` on `id`
- Unique: `ix_users_email` on `email`
- Unique: `ix_users_google_id` on `google_id`

**Referenced By:**
- `photos.user_id` → `users.id` (CASCADE DELETE)
- `user_achievements.user_id` → `users.id` (CASCADE DELETE)
- `user_location_visits.user_id` → `users.id` (CASCADE DELETE)
- `user_progress.user_id` → `users.id` (CASCADE DELETE)
- `user_quests.user_id` → `users.id` (CASCADE DELETE)

---

### 2. `user_progress`

Tracks user game progress including XP, level, rank, and statistics.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `user_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `users.id` (unique) |
| `total_xp` | INTEGER | NULL | - | Total experience points |
| `current_level` | INTEGER | NULL | - | Current user level |
| `current_rank` | VARCHAR(50) | NULL | - | Current rank/title |
| `locations_visited` | INTEGER | NULL | - | Count of unique locations visited |
| `photos_taken` | INTEGER | NULL | - | Total photos uploaded |
| `quests_completed` | INTEGER | NULL | - | Total quests completed |
| `achievements_earned` | INTEGER | NULL | - | Total achievements unlocked |
| `phrases_learned` | JSON | NULL | - | Array of learned Georgian phrases |
| `updated_at` | TIMESTAMP | NULL | - | Last update timestamp |

**Indexes:**
- Primary Key: `user_progress_pkey` on `id`
- Unique: `user_progress_user_id_key` on `user_id`

**Foreign Keys:**
- `user_id` → `users.id` (ON DELETE CASCADE)

---

### 3. `locations`

Points of interest in Poti (attractions, landmarks, nature spots).

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `name` | VARCHAR(255) | NOT NULL | - | Location name (English) |
| `name_ka` | VARCHAR(255) | NULL | - | Location name (Georgian) |
| `description` | TEXT | NULL | - | Detailed description |
| `category` | VARCHAR(50) | NULL | - | Category (attraction, landmark, nature, historical) |
| `latitude` | NUMERIC(10,8) | NULL | - | GPS latitude |
| `longitude` | NUMERIC(11,8) | NULL | - | GPS longitude |
| `xp_reward` | INTEGER | NULL | - | XP awarded for visiting |
| `image_url` | TEXT | NULL | - | Location image URL |
| `extra_data` | JSON | NULL | - | Additional metadata |
| `created_at` | TIMESTAMP | NULL | - | Creation timestamp |
| `updated_at` | TIMESTAMP | NULL | - | Last update timestamp |

**Indexes:**
- Primary Key: `locations_pkey` on `id`

**Referenced By:**
- `photos.location_id` → `locations.id` (ON DELETE SET NULL)
- `user_location_visits.location_id` → `locations.id` (ON DELETE CASCADE)

**Seed Data:** 7 locations including Poti Lighthouse, Argonauts Monument, Paliastomi Lake, etc.

---

### 4. `user_location_visits`

Records when users visit locations.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `user_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `users.id` |
| `location_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `locations.id` |
| `visited_at` | TIMESTAMP | NULL | - | Visit timestamp |
| `photo_url` | TEXT | NULL | - | Photo taken at location |

**Indexes:**
- Primary Key: `user_location_visits_pkey` on `id`
- Unique: `unique_user_location_visit` on (`user_id`, `location_id`)

**Foreign Keys:**
- `user_id` → `users.id` (ON DELETE CASCADE)
- `location_id` → `locations.id` (ON DELETE CASCADE)

**Note:** Unique constraint ensures one visit record per user-location pair.

---

### 5. `achievements`

Available achievements that users can earn.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `name` | VARCHAR(255) | NOT NULL | - | Achievement name (unique) |
| `description` | TEXT | NULL | - | Achievement description |
| `icon` | VARCHAR(10) | NULL | - | Emoji icon |
| `xp_reward` | INTEGER | NULL | - | XP awarded for earning |
| `requirement_type` | VARCHAR(50) | NULL | - | Type (visits, phrases, photos, special) |
| `requirement_value` | INTEGER | NULL | - | Required count/value |
| `is_secret` | BOOLEAN | NULL | - | Hidden until earned |
| `category` | VARCHAR(50) | NULL | - | Category (exploration, language, photos, special) |
| `created_at` | TIMESTAMP | NULL | - | Creation timestamp |

**Indexes:**
- Primary Key: `achievements_pkey` on `id`
- Unique: `achievements_name_key` on `name`

**Referenced By:**
- `user_achievements.achievement_id` → `achievements.id` (ON DELETE CASCADE)

**Seed Data:** 10 achievements including First Steps, Explorer, Linguist, Argonaut, etc.

---

### 6. `user_achievements`

Junction table tracking which achievements users have earned.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `user_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `users.id` |
| `achievement_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `achievements.id` |
| `earned_at` | TIMESTAMP | NULL | - | When achievement was earned |

**Indexes:**
- Primary Key: `user_achievements_pkey` on `id`
- Unique: `unique_user_achievement` on (`user_id`, `achievement_id`)

**Foreign Keys:**
- `user_id` → `users.id` (ON DELETE CASCADE)
- `achievement_id` → `achievements.id` (ON DELETE CASCADE)

**Note:** Unique constraint prevents duplicate achievement awards.

---

### 7. `quests`

Available quests/challenges for users.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `name` | VARCHAR(255) | NOT NULL | - | Quest name |
| `description` | TEXT | NULL | - | Quest description |
| `story_intro` | TEXT | NULL | - | Narrative introduction |
| `xp_reward` | INTEGER | NULL | - | XP awarded on completion |
| `steps` | JSON | NOT NULL | - | Array of quest steps with location requirements |
| `is_daily` | BOOLEAN | NULL | - | Daily recurring quest |
| `difficulty` | VARCHAR(20) | NULL | - | Difficulty level (easy, medium, hard) |
| `estimated_time` | INTEGER | NULL | - | Estimated completion time (minutes) |
| `created_at` | TIMESTAMP | NULL | - | Creation timestamp |

**Indexes:**
- Primary Key: `quests_pkey` on `id`

**Referenced By:**
- `user_quests.quest_id` → `quests.id` (ON DELETE CASCADE)

**Seed Data:** 3 quests including "The Argonaut's Journey", "Secrets of Colchis", and "Daily Explorer".

**Note:** `steps` JSON structure:
```json
[
  {
    "title": "Step Name",
    "description": "Step description",
    "location_id": "loc-argonauts"
  }
]
```

---

### 8. `user_quests`

Tracks user progress through quests.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `user_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `users.id` |
| `quest_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `quests.id` |
| `status` | VARCHAR(20) | NULL | - | Quest status (started, completed, etc.) |
| `current_step` | INTEGER | NULL | - | Current step index |
| `started_at` | TIMESTAMP | NULL | - | Quest start timestamp |
| `completed_at` | TIMESTAMP | NULL | - | Quest completion timestamp |

**Indexes:**
- Primary Key: `user_quests_pkey` on `id`
- Unique: `unique_user_quest` on (`user_id`, `quest_id`)

**Foreign Keys:**
- `user_id` → `users.id` (ON DELETE CASCADE)
- `quest_id` → `quests.id` (ON DELETE CASCADE)

**Note:** Unique constraint ensures one active quest per user-quest pair.

---

### 9. `photos`

User-uploaded photos with location tagging.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `user_id` | VARCHAR(36) | NOT NULL | - | Foreign key to `users.id` |
| `location_id` | VARCHAR(36) | NULL | - | Foreign key to `locations.id` |
| `file_path` | TEXT | NOT NULL | - | Local file path |
| `file_name` | VARCHAR(255) | NULL | - | Original filename |
| `file_size` | INTEGER | NULL | - | File size in bytes |
| `mime_type` | VARCHAR(50) | NULL | - | MIME type |
| `gcs_url` | TEXT | NULL | - | Google Cloud Storage URL |
| `caption` | TEXT | NULL | - | User-provided caption |
| `is_selfie` | BOOLEAN | NULL | - | Selfie flag |
| `latitude` | NUMERIC(10,8) | NULL | - | GPS latitude |
| `longitude` | NUMERIC(11,8) | NULL | - | GPS longitude |
| `uploaded_at` | TIMESTAMP | NULL | - | Upload timestamp |

**Indexes:**
- Primary Key: `photos_pkey` on `id`

**Foreign Keys:**
- `user_id` → `users.id` (ON DELETE CASCADE)
- `location_id` → `locations.id` (ON DELETE SET NULL)

**Note:** Location can be NULL if photo isn't tagged to a location.

---

### 10. `knowledge_chunks`

RAG (Retrieval Augmented Generation) knowledge base with vector embeddings.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `id` | VARCHAR(36) | NOT NULL | - | Primary key (UUID) |
| `content` | TEXT | NOT NULL | - | Knowledge content text |
| `category` | VARCHAR(50) | NULL | - | Category (history, attraction, restaurant, etc.) |
| `source_file` | VARCHAR(255) | NULL | - | Source document filename |
| `extra_data` | JSON | NULL | - | Additional metadata |
| `embedding` | VECTOR(768) | NULL | - | Vector embedding for similarity search |
| `created_at` | TIMESTAMP | NULL | - | Creation timestamp |
| `updated_at` | TIMESTAMP | NULL | - | Last update timestamp |

**Indexes:**
- Primary Key: `knowledge_chunks_pkey` on `id`
- Index: `ix_knowledge_chunks_category` on `category`

**Note:** Uses pgvector extension for `embedding` column. Embeddings are 768-dimensional vectors (typically from Google Gemini or similar models).

**Seed Data:** 6 knowledge chunks covering Poti history, attractions, and food.

---

## Entity Relationships

### Relationship Diagram

```
users (1) ──< (many) user_progress
users (1) ──< (many) user_location_visits
users (1) ──< (many) user_achievements
users (1) ──< (many) user_quests
users (1) ──< (many) photos

locations (1) ──< (many) user_location_visits
locations (1) ──< (many) photos

achievements (1) ──< (many) user_achievements

quests (1) ──< (many) user_quests
```

### Foreign Key Summary

| From Table | Column | To Table | Column | Delete Action |
|------------|--------|----------|--------|---------------|
| `photos` | `user_id` | `users` | `id` | CASCADE |
| `photos` | `location_id` | `locations` | `id` | SET NULL |
| `user_achievements` | `user_id` | `users` | `id` | CASCADE |
| `user_achievements` | `achievement_id` | `achievements` | `id` | CASCADE |
| `user_location_visits` | `user_id` | `users` | `id` | CASCADE |
| `user_location_visits` | `location_id` | `locations` | `id` | CASCADE |
| `user_progress` | `user_id` | `users` | `id` | CASCADE |
| `user_quests` | `user_id` | `users` | `id` | CASCADE |
| `user_quests` | `quest_id` | `quests` | `id` | CASCADE |

---

## Indexes Summary

| Table | Index Name | Type | Columns |
|-------|------------|------|---------|
| `users` | `users_pkey` | PRIMARY KEY | `id` |
| `users` | `ix_users_email` | UNIQUE | `email` |
| `users` | `ix_users_google_id` | UNIQUE | `google_id` |
| `user_progress` | `user_progress_pkey` | PRIMARY KEY | `id` |
| `user_progress` | `user_progress_user_id_key` | UNIQUE | `user_id` |
| `locations` | `locations_pkey` | PRIMARY KEY | `id` |
| `user_location_visits` | `user_location_visits_pkey` | PRIMARY KEY | `id` |
| `user_location_visits` | `unique_user_location_visit` | UNIQUE | `user_id`, `location_id` |
| `achievements` | `achievements_pkey` | PRIMARY KEY | `id` |
| `achievements` | `achievements_name_key` | UNIQUE | `name` |
| `user_achievements` | `user_achievements_pkey` | PRIMARY KEY | `id` |
| `user_achievements` | `unique_user_achievement` | UNIQUE | `user_id`, `achievement_id` |
| `quests` | `quests_pkey` | PRIMARY KEY | `id` |
| `user_quests` | `user_quests_pkey` | PRIMARY KEY | `id` |
| `user_quests` | `unique_user_quest` | UNIQUE | `user_id`, `quest_id` |
| `photos` | `photos_pkey` | PRIMARY KEY | `id` |
| `knowledge_chunks` | `knowledge_chunks_pkey` | PRIMARY KEY | `id` |
| `knowledge_chunks` | `ix_knowledge_chunks_category` | INDEX | `category` |

---

## Common Queries

### Get User Progress with Details
```sql
SELECT 
    u.email,
    u.name,
    up.total_xp,
    up.current_level,
    up.current_rank,
    up.locations_visited,
    up.achievements_earned
FROM users u
JOIN user_progress up ON u.id = up.user_id
WHERE u.id = 'user-id-here';
```

### Get User's Visited Locations
```sql
SELECT 
    l.name,
    l.name_ka,
    l.category,
    l.xp_reward,
    ulv.visited_at
FROM user_location_visits ulv
JOIN locations l ON ulv.location_id = l.id
WHERE ulv.user_id = 'user-id-here'
ORDER BY ulv.visited_at DESC;
```

### Get User's Achievements
```sql
SELECT 
    a.name,
    a.description,
    a.icon,
    a.xp_reward,
    ua.earned_at
FROM user_achievements ua
JOIN achievements a ON ua.achievement_id = a.id
WHERE ua.user_id = 'user-id-here'
ORDER BY ua.earned_at DESC;
```

### Get Active Quests for User
```sql
SELECT 
    q.name,
    q.description,
    q.xp_reward,
    uq.status,
    uq.current_step,
    uq.started_at
FROM user_quests uq
JOIN quests q ON uq.quest_id = q.id
WHERE uq.user_id = 'user-id-here'
  AND uq.status != 'completed'
ORDER BY uq.started_at DESC;
```

### Search Knowledge Base (Vector Similarity)
```sql
-- Find similar knowledge chunks using vector similarity
SELECT 
    id,
    category,
    LEFT(content, 100) as content_preview,
    1 - (embedding <=> '[0.1,0.2,...]'::vector) as similarity
FROM knowledge_chunks
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1,0.2,...]'::vector
LIMIT 5;
```

### Leaderboard Query
```sql
SELECT 
    u.name,
    u.email,
    up.total_xp,
    up.current_level,
    up.current_rank,
    up.locations_visited,
    up.achievements_earned
FROM user_progress up
JOIN users u ON up.user_id = u.id
ORDER BY up.total_xp DESC
LIMIT 10;
```

### Get Location Statistics
```sql
SELECT 
    l.name,
    l.category,
    COUNT(DISTINCT ulv.user_id) as visitors_count,
    COUNT(ulv.id) as total_visits,
    AVG(l.xp_reward) as avg_xp_reward
FROM locations l
LEFT JOIN user_location_visits ulv ON l.id = ulv.location_id
GROUP BY l.id, l.name, l.category
ORDER BY visitors_count DESC;
```

---

## Database Maintenance

### Backup Database
```bash
docker exec argonauts-db pg_dump -U postgres argonauts > backup.sql
```

### Restore Database
```bash
docker exec -i argonauts-db psql -U postgres argonauts < backup.sql
```

### Check Database Size
```sql
SELECT pg_size_pretty(pg_database_size('argonauts'));
```

### Analyze Tables
```sql
ANALYZE;
```

### Vacuum Database
```sql
VACUUM ANALYZE;
```

---

## Notes

- All primary keys use VARCHAR(36) for UUID strings
- Timestamps are stored as `TIMESTAMP WITHOUT TIME ZONE`
- JSON columns are used for flexible data structures (quest steps, phrases, extra_data)
- Vector embeddings use pgvector extension with 768 dimensions
- Foreign keys use CASCADE DELETE for most relationships, except `photos.location_id` which uses SET NULL
- Unique constraints prevent duplicate user-location visits, user-achievements, and user-quests

---

**Last Updated:** Generated from database schema on 2025-12-05  
**Database Version:** PostgreSQL 16 with pgvector 0.8.1

