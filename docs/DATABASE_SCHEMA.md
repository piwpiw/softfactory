# 📝 CooCook Database Schema

> **Purpose**: ```
> **Status**: 🟢 ACTIVE (관리 중)
> **Impact**: [Engineering / Operations]

---

## ⚡ Executive Summary (핵심 요약)
- **주요 내용**: 본 문서는 CooCook Database Schema 관련 핵심 명세 및 관리 포인트를 포함합니다.
- **상태**: 현재 최신화 완료 및 검토 됨.
- **연관 문서**: [Master Index](./NOTION_MASTER_INDEX.md)

---

> PostgreSQL 16 | Designed for scalability & analytics

---

## 📊 ERD Overview

```
┌─────────────┐
│   Users     │─────┐
└─────────────┘     │
                    │
┌─────────────────┐ │
│  Preferences    │<┤
└─────────────────┘ │
                    │
┌──────────────┐    │
│   Chefs      │────┤
└──────────────┘    │
                    │
┌──────────────┐    │
│   Recipes    │<───┤
└──────────────┘    │
                    │
┌──────────────┐    │
│   Bookings   │────┘
└──────────────┘

┌────────────────┐   ┌──────────────┐   ┌──────────┐
│  Ingredients   │───│  Recipes     │───│  Reviews │
└────────────────┘   └──────────────┘   └──────────┘

┌────────────────┐   ┌──────────────┐   ┌──────────────┐
│  Ratings       │───│  Bookings    │───│  Payments    │
└────────────────┘   └──────────────┘   └──────────────┘
```

---

## 🗂️ Table Definitions

### Users
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    bio TEXT,
    user_type ENUM('CONSUMER', 'CHEF', 'BOTH') DEFAULT 'CONSUMER',
    phone VARCHAR(20),
    location_lat NUMERIC(10, 8),
    location_lng NUMERIC(11, 8),
    location_city VARCHAR(100),
    location_country VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,

    INDEX idx_email,
    INDEX idx_location_city,
    INDEX idx_created_at
);
```

### User Preferences
```sql
CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    dietary_restrictions TEXT[] DEFAULT '{}',
    cuisine_preferences TEXT[] DEFAULT '{}',
    spice_level INT DEFAULT 2 CHECK (spice_level BETWEEN 0 AND 5),
    budget_min_usd DECIMAL(8,2) DEFAULT 10,
    budget_max_usd DECIMAL(8,2) DEFAULT 100,
    allergies TEXT[] DEFAULT '{}',
    dietary_flags JSONB DEFAULT '{}',
    prep_time_max_mins INT DEFAULT 60,
    personalization_consent BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id),
    INDEX idx_user_id
);
```

### Recipes
```sql
CREATE TABLE recipes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chef_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    cuisine VARCHAR(100),
    difficulty ENUM('EASY', 'MEDIUM', 'HARD') DEFAULT 'MEDIUM',
    prep_time_mins INT NOT NULL,
    cook_time_mins INT NOT NULL,
    servings INT NOT NULL,
    price_usd DECIMAL(10,2) DEFAULT 0,
    rating DECIMAL(3,2),
    review_count INT DEFAULT 0,
    tags TEXT[] DEFAULT '{}',
    image_url TEXT,
    video_url TEXT,
    status ENUM('DRAFT', 'PUBLISHED', 'ARCHIVED') DEFAULT 'DRAFT',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    published_at TIMESTAMP,

    INDEX idx_chef_id,
    INDEX idx_cuisine,
    INDEX idx_tags,
    INDEX idx_status,
    INDEX idx_rating,
    FULLTEXT INDEX idx_title_description (title, description)
);
```

### Ingredients
```sql
CREATE TABLE ingredients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID NOT NULL REFERENCES recipes(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10,2),
    unit VARCHAR(50),
    optional BOOLEAN DEFAULT FALSE,
    step_order INT,
    created_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_recipe_id,
    INDEX idx_step_order
);
```

### Chefs
```sql
CREATE TABLE chefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bio TEXT,
    certifications TEXT[],
    cuisine_specialties TEXT[] NOT NULL,
    hourly_rate_usd DECIMAL(10,2) NOT NULL,
    rating DECIMAL(3,2) DEFAULT 0,
    total_bookings INT DEFAULT 0,
    completed_bookings INT DEFAULT 0,
    response_time_mins INT DEFAULT 60,
    languages TEXT[] DEFAULT '{}',
    verified_at TIMESTAMP,
    is_professional BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(user_id),
    INDEX idx_rating,
    INDEX idx_total_bookings
);
```

### Bookings
```sql
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chef_id UUID NOT NULL REFERENCES chefs(id) ON DELETE CASCADE,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    duration_hours INT NOT NULL,
    party_size INT NOT NULL,
    dietary_preferences TEXT[],
    special_requests TEXT,
    total_price_usd DECIMAL(10,2) NOT NULL,
    status ENUM('PENDING', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED') DEFAULT 'PENDING',
    payment_status ENUM('PENDING', 'PAID', 'REFUNDED') DEFAULT 'PENDING',
    confirmation_code VARCHAR(20) UNIQUE,
    meeting_location POINT,
    meeting_notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    INDEX idx_user_id,
    INDEX idx_chef_id,
    INDEX idx_booking_date,
    INDEX idx_status,
    INDEX idx_confirmation_code,
    SPATIAL INDEX idx_location (meeting_location)
);
```

### Reviews
```sql
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recipe_id UUID REFERENCES recipes(id) ON DELETE CASCADE,
    booking_id UUID REFERENCES bookings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(255),
    content TEXT,
    photos TEXT[],
    helpful_count INT DEFAULT 0,
    status ENUM('PENDING', 'PUBLISHED', 'FLAGGED') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    INDEX idx_user_id,
    INDEX idx_recipe_id,
    INDEX idx_booking_id,
    INDEX idx_rating,
    INDEX idx_created_at
);
```

### Payments
```sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id UUID NOT NULL REFERENCES bookings(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount_usd DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method ENUM('CREDIT_CARD', 'PAYPAL', 'BANK_TRANSFER', 'WALLET') NOT NULL,
    transaction_id VARCHAR(255) UNIQUE,
    status ENUM('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED') DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    INDEX idx_booking_id,
    INDEX idx_user_id,
    INDEX idx_status
);
```

### Analytics Events (Optimized for TimescaleDB)
```sql
CREATE TABLE events (
    time TIMESTAMP NOT NULL,
    user_id UUID,
    event_type VARCHAR(100) NOT NULL,
    event_data JSONB,
    session_id VARCHAR(255),
    user_agent TEXT,

    INDEX idx_user_id,
    INDEX idx_event_type,
    INDEX idx_time
) PARTITION BY RANGE (time);
```

---

## 🔑 Indexes & Performance

### Critical Indexes
```sql
-- User lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_location ON users(location_city, location_country);

-- Recipe discovery
CREATE INDEX idx_recipes_chef ON recipes(chef_id);
CREATE INDEX idx_recipes_cuisine_status ON recipes(cuisine, status);
CREATE INDEX idx_recipes_tags ON recipes USING GIN(tags);

-- Booking queries
CREATE INDEX idx_bookings_chef_date ON bookings(chef_id, booking_date);
CREATE INDEX idx_bookings_user_status ON bookings(user_id, status);

-- Analytics
CREATE INDEX idx_events_time_type ON events(time DESC, event_type);
```

---

## 📊 Migration Scripts

### V1 → V2 (Timeline: 2026-03-15)
```sql
-- Add recommendation engine columns
ALTER TABLE user_preferences ADD COLUMN embedding VECTOR(384);
ALTER TABLE recipes ADD COLUMN embedding VECTOR(384);

-- Create recommendation table
CREATE TABLE recommendations (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    recipe_id UUID NOT NULL,
    score DECIMAL(5,4),
    reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(recipe_id) REFERENCES recipes(id)
);
```

---

## 📈 Estimated Growth

| Year | Users | Recipes | Bookings | DB Size |
|------|-------|---------|----------|---------|
| 2026 | 100K | 50K | 25K | 2 GB |
| 2027 | 500K | 250K | 150K | 12 GB |
| 2028 | 2M | 1M | 600K | 50 GB |

**Recommendations:**
- Partition events table by month (TimescaleDB)
- Read replicas for analytics queries
- Caching layer (Redis) for popular recipes
- Elasticsearch for full-text search