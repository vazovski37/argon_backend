-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create vector index (will be created after tables exist)
-- This is handled by Flask-Migrate/SQLAlchemy

-- Seed some initial data for Poti locations
INSERT INTO locations (id, name, name_ka, description, category, latitude, longitude, xp_reward) VALUES
('loc-lighthouse', 'Poti Lighthouse', 'ფოთის შუქურა', 'Historic lighthouse built in 1864, offering panoramic views of the Black Sea coast.', 'attraction', 42.1461, 41.6719, 75),
('loc-argonauts', 'Argonauts Monument', 'არგონავტების ძეგლი', 'Iconic monument depicting Jason and the Argonauts, celebrating Poti''s mythological connection.', 'landmark', 42.1475, 41.6698, 50),
('loc-paliastomi', 'Paliastomi Lake', 'პალიასტომის ტბა', 'Beautiful lagoon lake connected to the Black Sea, home to diverse bird species.', 'nature', 42.1100, 41.7100, 100),
('loc-cathedral', 'Poti Cathedral', 'ფოთის საკათედრო ტაძარი', 'Neo-Byzantine cathedral built in 1906-1907, a masterpiece of Georgian religious architecture.', 'historical', 42.1467, 41.6725, 60),
('loc-port', 'Poti Sea Port', 'ფოთის საზღვაო ნავსადგური', 'One of Georgia''s largest ports on the Black Sea, with rich maritime history.', 'landmark', 42.1550, 41.6600, 40),
('loc-kolkheti', 'Kolkheti National Park', 'კოლხეთის ეროვნული პარკი', 'UNESCO World Heritage site with unique wetland ecosystems and relict forests.', 'nature', 42.1500, 41.8000, 150),
('loc-beach', 'Poti Beach', 'ფოთის სანაპირო', 'Sandy Black Sea beach perfect for relaxation and sunset views.', 'nature', 42.1400, 41.6500, 30)
ON CONFLICT (id) DO NOTHING;

-- Seed initial achievements
INSERT INTO achievements (id, name, description, icon, xp_reward, requirement_type, requirement_value, is_secret, category) VALUES
('ach-first-steps', 'First Steps', 'Visit your first location in Poti', '👣', 50, 'visits', 1, false, 'exploration'),
('ach-explorer', 'Explorer', 'Visit 5 different locations', '🧭', 100, 'visits', 5, false, 'exploration'),
('ach-adventurer', 'Adventurer', 'Visit 10 different locations', '🏔️', 200, 'visits', 10, false, 'exploration'),
('ach-first-words', 'First Words', 'Learn your first Georgian phrase', '🗣️', 50, 'phrases', 1, false, 'language'),
('ach-linguist', 'Linguist', 'Learn 5 Georgian phrases', '📚', 150, 'phrases', 5, false, 'language'),
('ach-shutterbug', 'Shutterbug', 'Take your first photo', '📸', 30, 'photos', 1, false, 'photos'),
('ach-photographer', 'Photographer', 'Take 10 photos', '🎞️', 100, 'photos', 10, false, 'photos'),
('ach-argonaut', 'Argonaut', 'Visit the Argonauts Monument', '⚓', 100, 'special', 1, false, 'special'),
('ach-lighthouse-keeper', 'Lighthouse Keeper', 'Visit the Poti Lighthouse', '🗼', 100, 'special', 1, false, 'special'),
('ach-nature-lover', 'Nature Lover', 'Visit Paliastomi Lake and Kolkheti National Park', '🌿', 200, 'special', 2, true, 'special')
ON CONFLICT (id) DO NOTHING;

-- Seed initial quests
INSERT INTO quests (id, name, description, story_intro, xp_reward, steps, is_daily, difficulty, estimated_time) VALUES
('quest-argonaut', 'The Argonaut''s Journey', 'Follow in the footsteps of Jason and the Argonauts', 
 'Long ago, Jason and his Argonauts sailed to these very shores in search of the Golden Fleece. Today, you will trace their legendary journey through Poti...',
 500, 
 '[{"title": "The Monument", "description": "Visit the Argonauts Monument to begin your quest", "location_id": "loc-argonauts"}, {"title": "The Port", "description": "Visit the port where the Argonauts may have landed", "location_id": "loc-port"}, {"title": "The Sea", "description": "Walk along the beach where legends were born", "location_id": "loc-beach"}]',
 false, 'medium', 60),
('quest-colchis', 'Secrets of Colchis', 'Discover the ancient kingdom of Colchis',
 'The ancient kingdom of Colchis was known throughout the ancient world. Explore its remnants and learn its secrets...',
 750,
 '[{"title": "Sacred Waters", "description": "Visit Paliastomi Lake, a sacred site", "location_id": "loc-paliastomi"}, {"title": "Ancient Forests", "description": "Explore Kolkheti National Park", "location_id": "loc-kolkheti"}, {"title": "The Cathedral", "description": "Visit Poti Cathedral", "location_id": "loc-cathedral"}]',
 false, 'hard', 120),
('quest-daily-explorer', 'Daily Explorer', 'Visit any 2 locations today',
 'A new day, new discoveries await!',
 100,
 '[{"title": "First Stop", "description": "Visit any location"}, {"title": "Second Stop", "description": "Visit another location"}]',
 true, 'easy', 30)
ON CONFLICT (id) DO NOTHING;

-- Seed some knowledge chunks for RAG (without embeddings - will be added via API)
INSERT INTO knowledge_chunks (id, content, category, source_file, extra_data) VALUES
('know-hist-1', 'Poti is an ancient city located on the eastern coast of the Black Sea in western Georgia. It has been an important port city since antiquity, when it was known as Phasis. According to Greek mythology, it was here that Jason and the Argonauts landed in search of the Golden Fleece.', 'history', 'poti_history.md', '{"topic": "origins"}'),
('know-hist-2', 'The Kingdom of Colchis, of which Phasis (modern Poti) was a major city, was known throughout the ancient world for its wealth and sophistication. The Greeks established colonies here, and trade flourished between Colchis and the Mediterranean world.', 'history', 'poti_history.md', '{"topic": "colchis"}'),
('know-attr-1', 'The Poti Lighthouse, built in 1864, stands as a symbol of the city''s maritime heritage. Rising 36 meters above the Black Sea, it guided countless ships to safe harbor. Today it offers panoramic views of the coast and remains one of the oldest lighthouses on the eastern Black Sea.', 'attraction', 'attractions.md', '{"location_id": "loc-lighthouse"}'),
('know-attr-2', 'The Argonauts Monument in central Poti depicts Jason and Medea with the Golden Fleece. Created by Georgian sculptor Merab Berdzenishvili, it commemorates the city''s mythological connection to the ancient Greek legend of the Argonauts.', 'attraction', 'attractions.md', '{"location_id": "loc-argonauts"}'),
('know-food-1', 'Elarji is the iconic dish of the Samegrelo region. It''s made from coarsely ground corn flour (ghomi) mixed with fresh sulguni cheese, creating a stretchy, elastic texture. The dish is traditionally served hot and pulled like taffy from the pot.', 'restaurant', 'food.md', '{"dish": "elarji"}'),
('know-food-2', 'Kupati is a traditional Georgian sausage from western Georgia. Made with pork, onions, and a blend of spices, it''s typically grilled over an open flame and served with adjika (spicy sauce) and fresh bread.', 'restaurant', 'food.md', '{"dish": "kupati"}')
ON CONFLICT (id) DO NOTHING;




