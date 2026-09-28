-- Back2You: AI-Powered Campus Lost & Found Intelligence Platform
-- PostgreSQL / Supabase Schema

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255),
    role VARCHAR(50) DEFAULT 'USER' CHECK (role IN ('USER', 'ADMIN', 'MODERATOR')),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Items table (Lost and Found items)
CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(20) NOT NULL CHECK (type IN ('lost', 'found')),
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    brand VARCHAR(100),
    color VARCHAR(100),
    distinguishing_features TEXT,
    image_url TEXT,
    location VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    status VARCHAR(50) DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'MATCH_FOUND', 'CLAIM_PENDING', 'UNDER_REVIEW', 'VERIFIED', 'RETURNED', 'CLOSED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Item Embeddings table (Stores dense vector embeddings from Vision and NLP models)
CREATE TABLE IF NOT EXISTS item_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID UNIQUE REFERENCES items(id) ON DELETE CASCADE,
    image_embedding JSONB,
    text_embedding JSONB,
    model_name VARCHAR(100) DEFAULT 'all-MiniLM-L6-v2 + MobileNet/CLIP',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Matches table (Records AI similarity and ranked candidate matches)
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lost_item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    found_item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    image_similarity DOUBLE PRECISION DEFAULT 0.0,
    text_similarity DOUBLE PRECISION DEFAULT 0.0,
    category_similarity DOUBLE PRECISION DEFAULT 0.0,
    brand_similarity DOUBLE PRECISION DEFAULT 0.0,
    color_similarity DOUBLE PRECISION DEFAULT 0.0,
    location_similarity DOUBLE PRECISION DEFAULT 0.0,
    time_similarity DOUBLE PRECISION DEFAULT 0.0,
    final_confidence DOUBLE PRECISION NOT NULL,
    status VARCHAR(50) DEFAULT 'POTENTIAL_MATCH' CHECK (status IN ('POTENTIAL_MATCH', 'CLAIMED', 'VERIFIED', 'DISMISSED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(lost_item_id, found_item_id)
);

-- Claims table (User claim submissions & admin verification)
CREATE TABLE IF NOT EXISTS claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    match_id UUID REFERENCES matches(id) ON DELETE SET NULL,
    item_id UUID REFERENCES items(id) ON DELETE CASCADE,
    claimant_id UUID REFERENCES users(id) ON DELETE CASCADE,
    verification_answers JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'UNDER_REVIEW', 'VERIFIED', 'REJECTED', 'RETURNED')),
    reviewed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Gamification table (Community Helper streak and reward points)
CREATE TABLE IF NOT EXISTS gamification (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    points INT DEFAULT 0,
    verified_reports INT DEFAULT 0,
    successful_returns INT DEFAULT 0,
    last_activity DATE
);

-- Badges catalog
CREATE TABLE IF NOT EXISTS badges (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(100) NOT NULL
);

-- User Badges earned
CREATE TABLE IF NOT EXISTS user_badges (
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    badge_id VARCHAR(50) REFERENCES badges(id) ON DELETE CASCADE,
    earned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(user_id, badge_id)
);

-- In-app Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info' CHECK (type IN ('match', 'claim', 'reward', 'system', 'info')),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_items_type ON items(type);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_location ON items(location);
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_user_id ON items(user_id);
CREATE INDEX IF NOT EXISTS idx_matches_lost ON matches(lost_item_id);
CREATE INDEX IF NOT EXISTS idx_matches_found ON matches(found_item_id);
CREATE INDEX IF NOT EXISTS idx_claims_claimant ON claims(claimant_id);
CREATE INDEX IF NOT EXISTS idx_claims_item ON claims(item_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);

-- Seed Badges
INSERT INTO badges (id, name, description, icon) VALUES
('first_finder', 'First Finder', 'Reported your first verified found item.', 'award'),
('community_helper', 'Community Helper', 'Successfully helped reconnect a lost belonging with its owner.', 'shield-check'),
('streak_7', '7-Day Helper', 'Maintained an active 7-day verified activity streak.', 'zap'),
('streak_30', '30-Day Helper', 'Maintained a dedicated 30-day verified helper streak.', 'sparkles'),
('recovery_hero', 'Recovery Hero', 'Facilitated 3 or more successful campus recoveries.', 'heart-handshake')
ON CONFLICT (id) DO NOTHING;
