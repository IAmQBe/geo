# Джем Бот (Jam Bot) — System Architecture

> **Blueprint for Implementation**
> Moscow / Saint Petersburg → All Russian Regions
> Telegram bot for café, restaurant, and place recommendations

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [High-Level System Architecture](#3-high-level-system-architecture)
4. [Database Schema](#4-database-schema)
5. [Smart Parser Architecture](#5-smart-parser-architecture)
6. [Bot Flow Architecture](#6-bot-flow-architecture)
7. [AI Integration](#7-ai-integration)
8. [Admin Panel](#8-admin-panel)
9. [Infrastructure & Deployment](#9-infrastructure--deployment)
10. [Project File Structure](#10-project-file-structure)
11. [Security Considerations](#11-security-considerations)
12. [Scaling Strategy](#12-scaling-strategy)

---

## 1. Project Overview

**Джем Бот** is a Telegram bot that recommends cafés, restaurants, and places to visit across Russian cities. It starts with Moscow and Saint Petersburg, then expands to all Russian regions.

### Core Features

| Feature | Description |
|---|---|
| Category browsing | 11 categories: eat, breakfast, work with laptop, warm up on terraces, specialty coffee, date, evening with friends, dance, drink, beauty, countryside |
| Place cards | Photo gallery, description, rating, action buttons |
| User data collection | Choices, ratings, favorites, visit history, comments/reviews |
| Smart parsing | Yandex Maps + 2GIS scraping without paid APIs |
| AI recommendations | Personalized suggestions based on user history |
| Multi-city support | Moscow → Saint Petersburg → All Russian regions |

### Categories

| Emoji | Category (RU) | Category (EN) | Slug |
|---|---|---|---|
| 🍽️ | Поесть | Eat | `eat` |
| ☕ | Завтрак | Breakfast | `breakfast` |
| 💻 | Поработать с ноутбуком | Work with laptop | `work` |
| 🌿 | Погреться на террасах | Warm up on terraces | `terrace` |
| ☕ | Спешелти кофе | Specialty coffee | `specialty_coffee` |
| 💑 | Свидание | Date | `date` |
| 🥂 | Вечер с друзьями | Evening with friends | `friends` |
| 💃 | Потанцевать | Dance | `dance` |
| 🍸 | Выпить | Drink | `drink` |
| 💅 | Красота | Beauty | `beauty` |
| 🌲 | За городом | Countryside | `countryside` |

---

## 2. Tech Stack

### Core Services

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| Bot Framework | aiogram | 3.x | Telegram bot logic, FSM, handlers |
| Language | Python | 3.11+ | Primary language |
| Database | PostgreSQL | 15+ | Primary data store |
| ORM | SQLAlchemy | 2.x (async) | Database abstraction |
| Migrations | Alembic | latest | Schema versioning |
| Cache / Queue | Redis | 7.x | Session cache, task queue, rate limiting |
| Task Queue | Celery | 5.x | Async tasks, scheduled parsing |
| Task Scheduler | Celery Beat | 5.x | Cron-like scheduling for parsers |
| Web Scraping | Playwright | latest | JS-rendered page scraping |
| Stealth | playwright-stealth | latest | Anti-detection for headless browser |
| HTTP Client | httpx | latest | Async HTTP requests |
| AI / LLM | OpenAI GPT-4o | latest | Recommendations, descriptions |
| Local LLM (fallback) | Ollama + Mistral | latest | Offline AI processing |
| Admin Panel | FastAPI + Jinja2 | latest | Web-based admin interface |
| Containerization | Docker + Compose | latest | Service orchestration |
| Reverse Proxy | Nginx | latest | SSL termination, routing |
| Monitoring | Prometheus + Grafana | latest | Metrics and dashboards |
| Logging | structlog + Loki | latest | Structured logging |
| Object Storage | MinIO (S3-compatible) | latest | Photo storage |

### Python Dependencies Summary

```
aiogram==3.x
sqlalchemy[asyncio]==2.x
alembic
asyncpg
redis[hiredis]
celery[redis]
playwright
playwright-stealth
httpx
fake-useragent
openai
fastapi
uvicorn
jinja2
pydantic-settings
structlog
prometheus-client
pillow
aiofiles
python-dotenv
```

---

## 3. High-Level System Architecture

```mermaid
graph TB
    subgraph Users
        TG[Telegram Users]
        ADMIN[Admin Users]
    end

    subgraph Bot Layer
        BOT[aiogram Bot Service]
        FSM[FSM State Manager]
        HANDLERS[Message Handlers]
        MIDDLEWARES[Middlewares]
    end

    subgraph API Layer
        ADMIN_API[FastAPI Admin Panel]
    end

    subgraph Data Layer
        PG[(PostgreSQL)]
        REDIS[(Redis Cache)]
        MINIO[(MinIO S3 Photos)]
    end

    subgraph Task Layer
        CELERY[Celery Workers]
        BEAT[Celery Beat Scheduler]
        TASKS[Parsing Tasks]
    end

    subgraph Parser Layer
        YANDEX[Yandex Maps Parser]
        TWOGIS[2GIS Parser]
        PROXY[Proxy Rotator]
        BROWSER[Playwright Headless]
        PIPELINE[Data Normalization Pipeline]
    end

    subgraph AI Layer
        OPENAI[OpenAI GPT-4o]
        LOCAL_LLM[Ollama Local LLM]
        RECOMMENDER[Recommendation Engine]
    end

    subgraph Infrastructure
        NGINX[Nginx Reverse Proxy]
        PROMETHEUS[Prometheus]
        GRAFANA[Grafana]
        LOKI[Loki Logs]
    end

    TG -->|HTTPS Webhook| NGINX
    ADMIN -->|HTTPS| NGINX
    NGINX --> BOT
    NGINX --> ADMIN_API

    BOT --> FSM
    BOT --> HANDLERS
    BOT --> MIDDLEWARES
    HANDLERS --> PG
    HANDLERS --> REDIS
    HANDLERS --> MINIO
    HANDLERS --> RECOMMENDER

    ADMIN_API --> PG
    ADMIN_API --> MINIO

    BEAT -->|Triggers| TASKS
    TASKS --> CELERY
    CELERY --> YANDEX
    CELERY --> TWOGIS
    YANDEX --> PROXY
    TWOGIS --> PROXY
    PROXY --> BROWSER
    BROWSER --> PIPELINE
    PIPELINE --> PG
    PIPELINE --> MINIO

    RECOMMENDER --> OPENAI
    RECOMMENDER --> LOCAL_LLM
    RECOMMENDER --> PG

    BOT --> PROMETHEUS
    CELERY --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    BOT --> LOKI
```

### Request Flow

```mermaid
sequenceDiagram
    participant U as User
    participant TG as Telegram
    participant BOT as Bot Service
    participant REDIS as Redis
    participant PG as PostgreSQL
    participant AI as AI Engine

    U->>TG: Sends message/callback
    TG->>BOT: Webhook POST
    BOT->>REDIS: Check user session/state
    REDIS-->>BOT: Session data
    BOT->>PG: Query places/user data
    PG-->>BOT: Data
    BOT->>AI: Get recommendations (async)
    AI-->>BOT: Personalized suggestions
    BOT->>REDIS: Update session state
    BOT->>TG: Send response with inline keyboard
    TG->>U: Display message
```

---

## 4. Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    cities {
        int id PK
        string name
        string region
        string timezone
        bool is_active
        float lat
        float lon
        timestamp created_at
    }

    categories {
        int id PK
        string slug
        string name_ru
        string name_en
        string emoji
        string description
        int sort_order
        bool is_active
    }

    places {
        int id PK
        string name
        int category_id FK
        int city_id FK
        string address
        text description
        text ai_description
        float rating
        int review_count
        float lat
        float lon
        string phone
        string website
        string working_hours
        string price_range
        string source_url_yandex
        string source_url_2gis
        string source_id_yandex
        string source_id_2gis
        bool is_active
        bool is_verified
        timestamp last_parsed_at
        timestamp created_at
        timestamp updated_at
    }

    place_photos {
        int id PK
        int place_id FK
        string url
        string storage_key
        bool is_primary
        int sort_order
        timestamp created_at
    }

    place_tags {
        int id PK
        int place_id FK
        string tag
    }

    users {
        int id PK
        bigint telegram_id
        string username
        string first_name
        string last_name
        string language_code
        int preferred_city_id FK
        jsonb preferences
        bool is_active
        bool is_blocked
        timestamp last_active_at
        timestamp created_at
    }

    user_favorites {
        int id PK
        int user_id FK
        int place_id FK
        timestamp added_at
    }

    visit_history {
        int id PK
        int user_id FK
        int place_id FK
        timestamp visited_at
        int rating
        text comment
        bool is_confirmed
    }

    place_reviews {
        int id PK
        int user_id FK
        int place_id FK
        int rating
        text text
        bool is_moderated
        bool is_visible
        timestamp created_at
        timestamp updated_at
    }

    parse_jobs {
        int id PK
        string source
        string city_slug
        string category_slug
        string status
        int places_found
        int places_added
        int places_updated
        text error_message
        timestamp started_at
        timestamp finished_at
    }

    ai_recommendations {
        int id PK
        int user_id FK
        int place_id FK
        float score
        string reason
        timestamp generated_at
        bool was_shown
        bool was_clicked
    }

    cities ||--o{ places : "has"
    cities ||--o{ users : "preferred by"
    categories ||--o{ places : "has"
    places ||--o{ place_photos : "has"
    places ||--o{ place_tags : "has"
    places ||--o{ user_favorites : "favorited in"
    places ||--o{ visit_history : "visited in"
    places ||--o{ place_reviews : "reviewed in"
    places ||--o{ ai_recommendations : "recommended in"
    users ||--o{ user_favorites : "has"
    users ||--o{ visit_history : "has"
    users ||--o{ place_reviews : "has"
    users ||--o{ ai_recommendations : "has"
```

### SQL Schema (Key Tables)

```sql
-- Cities
CREATE TABLE cities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    timezone VARCHAR(50) DEFAULT 'Europe/Moscow',
    is_active BOOLEAN DEFAULT TRUE,
    lat FLOAT,
    lon FLOAT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Categories
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,
    name_ru VARCHAR(100) NOT NULL,
    name_en VARCHAR(100),
    emoji VARCHAR(10),
    description TEXT,
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

-- Places
CREATE TABLE places (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category_id INT REFERENCES categories(id),
    city_id INT REFERENCES cities(id),
    address TEXT,
    description TEXT,
    ai_description TEXT,
    rating FLOAT,
    review_count INT DEFAULT 0,
    lat FLOAT,
    lon FLOAT,
    phone VARCHAR(50),
    website VARCHAR(255),
    working_hours JSONB,
    price_range VARCHAR(20),
    source_url_yandex TEXT,
    source_url_2gis TEXT,
    source_id_yandex VARCHAR(100),
    source_id_2gis VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_parsed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_places_city_category ON places(city_id, category_id);
CREATE INDEX idx_places_rating ON places(rating DESC);
CREATE INDEX idx_places_location ON places USING GIST(point(lon, lat));

-- Users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'ru',
    preferred_city_id INT REFERENCES cities(id),
    preferences JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    is_blocked BOOLEAN DEFAULT FALSE,
    last_active_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);

-- User Favorites
CREATE TABLE user_favorites (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    place_id INT REFERENCES places(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, place_id)
);

-- Visit History
CREATE TABLE visit_history (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    place_id INT REFERENCES places(id),
    visited_at TIMESTAMP DEFAULT NOW(),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    is_confirmed BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_visit_history_user_date ON visit_history(user_id, visited_at DESC);

-- Place Reviews
CREATE TABLE place_reviews (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    place_id INT REFERENCES places(id) ON DELETE CASCADE,
    rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    text TEXT,
    is_moderated BOOLEAN DEFAULT FALSE,
    is_visible BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, place_id)
);

-- Place Photos
CREATE TABLE place_photos (
    id SERIAL PRIMARY KEY,
    place_id INT REFERENCES places(id) ON DELETE CASCADE,
    url TEXT,
    storage_key VARCHAR(255),
    is_primary BOOLEAN DEFAULT FALSE,
    sort_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Parse Jobs Log
CREATE TABLE parse_jobs (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    city_slug VARCHAR(50),
    category_slug VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending',
    places_found INT DEFAULT 0,
    places_added INT DEFAULT 0,
    places_updated INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- AI Recommendations
CREATE TABLE ai_recommendations (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id) ON DELETE CASCADE,
    place_id INT REFERENCES places(id) ON DELETE CASCADE,
    score FLOAT,
    reason TEXT,
    generated_at TIMESTAMP DEFAULT NOW(),
    was_shown BOOLEAN DEFAULT FALSE,
    was_clicked BOOLEAN DEFAULT FALSE
);
```

---

## 5. Smart Parser Architecture

### Overview

The parser system scrapes Yandex Maps and 2GIS **without using their paid APIs**. It uses headless browsers with stealth plugins, proxy rotation, and intelligent rate limiting to avoid detection.

### Parser Architecture Diagram

```mermaid
graph TB
    subgraph Scheduler
        BEAT[Celery Beat]
        SCHEDULE[Bi-weekly / Monthly Schedule]
    end

    subgraph Task Orchestrator
        TASK_MGR[Parse Task Manager]
        QUEUE[Redis Task Queue]
        WORKERS[Celery Workers x3]
    end

    subgraph Anti-Detection Layer
        PROXY_POOL[Proxy Pool Manager]
        UA_ROTATOR[User-Agent Rotator]
        FINGERPRINT[Browser Fingerprint Randomizer]
        DELAY[Random Delay Engine]
        CAPTCHA[CAPTCHA Handler]
    end

    subgraph Browser Pool
        PW1[Playwright Instance 1]
        PW2[Playwright Instance 2]
        PW3[Playwright Instance 3]
    end

    subgraph Parsers
        YANDEX_P[Yandex Maps Parser]
        TWOGIS_P[2GIS Parser]
    end

    subgraph Data Pipeline
        EXTRACTOR[Data Extractor]
        VALIDATOR[Data Validator]
        DEDUPLICATOR[Deduplicator]
        NORMALIZER[Data Normalizer]
        PHOTO_DL[Photo Downloader]
        DB_WRITER[Database Writer]
    end

    subgraph Fallback
        RETRY[Retry with Backoff]
        FALLBACK_PROXY[Fallback Proxy]
        SKIP[Skip and Log]
    end

    BEAT --> SCHEDULE
    SCHEDULE --> TASK_MGR
    TASK_MGR --> QUEUE
    QUEUE --> WORKERS

    WORKERS --> PROXY_POOL
    WORKERS --> UA_ROTATOR
    WORKERS --> FINGERPRINT
    WORKERS --> DELAY

    PROXY_POOL --> PW1
    UA_ROTATOR --> PW1
    FINGERPRINT --> PW1
    PROXY_POOL --> PW2
    UA_ROTATOR --> PW2
    FINGERPRINT --> PW2
    PROXY_POOL --> PW3
    UA_ROTATOR --> PW3
    FINGERPRINT --> PW3

    PW1 --> YANDEX_P
    PW2 --> TWOGIS_P
    PW3 --> YANDEX_P

    YANDEX_P --> EXTRACTOR
    TWOGIS_P --> EXTRACTOR

    EXTRACTOR --> VALIDATOR
    VALIDATOR --> DEDUPLICATOR
    DEDUPLICATOR --> NORMALIZER
    NORMALIZER --> PHOTO_DL
    PHOTO_DL --> DB_WRITER

    YANDEX_P -->|On Block| RETRY
    TWOGIS_P -->|On Block| RETRY
    RETRY -->|Max Retries| FALLBACK_PROXY
    FALLBACK_PROXY -->|Still Blocked| SKIP
    CAPTCHA --> RETRY
```

### Anti-Detection Strategies

#### 1. Proxy Rotation

```
Sources:
  - Free proxy lists: proxy-list.download, free-proxy-list.net, proxyscrape.com
  - Paid proxies (optional): BrightData residential proxies
  - Proxy health check: ping + anonymity test before use
  - Rotation strategy: Round-robin with health scoring
  - Blacklist: Auto-blacklist proxies that trigger blocks

Proxy Pool Manager:
  - Maintains pool of 50-200 working proxies
  - Health check every 15 minutes
  - Automatic refresh from free sources every hour
  - Tracks success/failure rate per proxy
  - Prefers residential > datacenter proxies
```

#### 2. User-Agent Rotation

```
Library: fake-useragent
Strategy:
  - Rotate per session (not per request)
  - Use only modern browser UAs (Chrome 120+, Firefox 120+)
  - Match UA with browser fingerprint
  - Avoid bot-like UAs (Python-requests, curl, etc.)
```

#### 3. Browser Fingerprint Randomization

```
Using playwright-stealth:
  - Randomize viewport size (1280-1920 x 720-1080)
  - Randomize timezone (Moscow, Saint Petersburg)
  - Randomize language headers (ru-RU, ru)
  - Disable WebDriver flag
  - Randomize canvas fingerprint
  - Randomize WebGL fingerprint
  - Fake plugins list
  - Fake screen resolution
```

#### 4. Request Timing

```
Delays:
  - Between page loads: 3-8 seconds (random)
  - Between scroll actions: 1-3 seconds (random)
  - Between category searches: 10-30 seconds (random)
  - Between cities: 60-120 seconds (random)
  - Human-like mouse movements: enabled
  - Random scroll patterns: enabled
```

#### 5. Session Management

```
- New browser context per city/category combination
- Clear cookies between sessions
- Rotate IP before starting new session
- Simulate human browsing: visit homepage first, then search
- Use search bar instead of direct URL when possible
```

### Yandex Maps Parser

```
Target Data:
  - Place name
  - Category/type
  - Address
  - Rating (1-5)
  - Review count
  - Phone number
  - Website
  - Working hours
  - Price range (₽, ₽₽, ₽₽₽)
  - Photos (up to 10)
  - Coordinates (lat/lon)
  - Place URL

Scraping Strategy:
  1. Navigate to maps.yandex.ru
  2. Search for category + city (e.g., "кофейни Москва")
  3. Scroll through results list
  4. Click each place card
  5. Extract data from place detail panel
  6. Download photos
  7. Paginate through all results

Selectors (CSS/XPath):
  - Place cards: .search-list-item
  - Place name: .orgpage-header-view__name
  - Rating: .business-rating-badge-view__rating
  - Address: .orgpage-addresses-view__address
  - Phone: .orgpage-phones-view__phone-number
  - Photos: .photo-album-view__photo img
```

### 2GIS Parser

```
Target Data:
  - Same fields as Yandex Maps
  - Additional: rubrics/tags, social links

Scraping Strategy:
  1. Navigate to 2gis.ru
  2. Search for category + city
  3. Scroll through results
  4. Extract data from cards and detail pages
  5. Download photos

Selectors:
  - Place cards: ._1h3cgic
  - Place name: ._oqoid
  - Rating: .z8gi8o
  - Address: ._er2xx9
```

### Data Normalization Pipeline

```mermaid
graph LR
    RAW[Raw Scraped Data] --> CLEAN[Clean HTML/Text]
    CLEAN --> VALIDATE[Validate Required Fields]
    VALIDATE --> DEDUP[Check Duplicates by name+address]
    DEDUP --> NORMALIZE[Normalize Fields]
    NORMALIZE --> GEOCODE[Verify Coordinates]
    GEOCODE --> PHOTOS[Download and Store Photos]
    PHOTOS --> AI_DESC[Generate AI Description]
    AI_DESC --> SAVE[Save to PostgreSQL]

    VALIDATE -->|Missing required| SKIP_LOG[Log and Skip]
    DEDUP -->|Duplicate found| UPDATE[Update Existing Record]
```

### Scheduling

```
Celery Beat Schedule:
  - Full parse (all cities, all categories): Monthly (1st of month, 02:00 MSK)
  - Incremental parse (top cities): Bi-weekly (1st and 15th, 03:00 MSK)
  - Proxy pool refresh: Every hour
  - Photo re-download (failed): Daily at 04:00 MSK
  - AI description generation (new places): Daily at 05:00 MSK

Task Priority Queue:
  - HIGH: Moscow, Saint Petersburg
  - MEDIUM: Cities with 1M+ population
  - LOW: Other cities
```

### Fallback Strategies

```
Level 1: Retry with same proxy (3 attempts, exponential backoff)
Level 2: Retry with different proxy from pool
Level 3: Retry with residential proxy (if configured)
Level 4: Skip place, log for manual review
Level 5: Pause city parsing for 24 hours, alert admin

Block Detection:
  - HTTP 403/429 responses
  - CAPTCHA page detected
  - Empty results when results expected
  - Redirect to anti-bot page
  - Response time > 30 seconds
```

---

## 6. Bot Flow Architecture

### Main Flow Diagram

```mermaid
stateDiagram-v2
    [*] --> Start: /start command

    Start --> CitySelection: New user
    Start --> MainMenu: Returning user

    CitySelection --> MainMenu: City selected

    MainMenu --> CategoryList: Browse places
    MainMenu --> Favorites: My favorites
    MainMenu --> History: Visit history
    MainMenu --> Profile: My profile
    MainMenu --> Search: Search places

    CategoryList --> PlaceList: Category selected
    PlaceList --> PlaceCard: Place selected
    PlaceList --> PlaceList: Next/Prev page

    PlaceCard --> PlaceCard: Next photo
    PlaceCard --> PlaceCard: Prev photo
    PlaceCard --> PlaceDetails: Details button
    PlaceCard --> AddFavorite: Add to favorites
    PlaceCard --> BookPlace: Book button
    PlaceCard --> YandexMaps: Find on Yandex Maps
    PlaceCard --> RatePlace: Rate this place

    RatePlace --> LeaveComment: Rating given
    LeaveComment --> PlaceCard: Comment saved

    AddFavorite --> PlaceCard: Added confirmation

    Favorites --> PlaceCard: Place selected
    Favorites --> RemoveFavorite: Remove button

    History --> HistoryByDay: View by day
    HistoryByDay --> PlaceCard: Place selected

    Search --> SearchResults: Query entered
    SearchResults --> PlaceCard: Place selected

    Profile --> CitySelection: Change city
    Profile --> Preferences: Edit preferences
    Profile --> Statistics: My statistics
```

### Inline Keyboard Layout

#### Main Menu
```
┌─────────────────────────────────┐
│  🍽️ Поесть    ☕ Завтрак        │
│  💻 Поработать  🌿 Террасы      │
│  ☕ Спешелти   💑 Свидание      │
│  🥂 С друзьями  💃 Потанцевать  │
│  🍸 Выпить    💅 Красота        │
│  🌲 За городом                  │
│  ─────────────────────────────  │
│  ❤️ Избранное  📋 История        │
│  🔍 Поиск     👤 Профиль        │
└─────────────────────────────────┘
```

#### Place Card
```
┌─────────────────────────────────┐
│  📸 [Photo 1/5]                 │
│  ◀️ Prev Photo    Next Photo ▶️  │
│  ─────────────────────────────  │
│  🏠 Place Name                  │
│  ⭐ 4.7 (234 reviews)           │
│  📍 Address                     │
│  💰 ₽₽                          │
│  ─────────────────────────────  │
│  📖 Details    ❤️ Favorites      │
│  📅 Book       🗺️ Yandex Maps   │
│  ⭐ Rate       💬 Reviews        │
│  ─────────────────────────────  │
│  ◀️ Back to list                 │
└─────────────────────────────────┘
```

#### Rating Flow
```
┌─────────────────────────────────┐
│  Rate this place:               │
│  ⭐ 1  ⭐⭐ 2  ⭐⭐⭐ 3          │
│  ⭐⭐⭐⭐ 4  ⭐⭐⭐⭐⭐ 5         │
└─────────────────────────────────┘
```

### FSM States

```python
class BotStates(StatesGroup):
    # Onboarding
    selecting_city = State()

    # Main navigation
    main_menu = State()

    # Place browsing
    browsing_category = State()
    viewing_place_list = State()
    viewing_place_card = State()
    viewing_place_details = State()

    # Favorites
    viewing_favorites = State()

    # History
    viewing_history = State()
    viewing_history_day = State()

    # Rating flow
    rating_place = State()
    leaving_comment = State()

    # Search
    entering_search_query = State()
    viewing_search_results = State()

    # Profile
    viewing_profile = State()
    editing_preferences = State()
```

### Middleware Stack

```
1. ThrottlingMiddleware     — Rate limiting per user (5 req/sec)
2. UserMiddleware           — Load/create user from DB
3. CityMiddleware           — Ensure user has selected city
4. LoggingMiddleware        — Log all interactions
5. MetricsMiddleware        — Prometheus metrics
6. ErrorHandlerMiddleware   — Catch and handle errors gracefully
```

---

## 7. AI Integration

### AI Architecture

```mermaid
graph TB
    subgraph Input Sources
        USER_HIST[User History]
        USER_FAV[User Favorites]
        USER_RATINGS[User Ratings]
        USER_QUERY[Natural Language Query]
        PLACE_DATA[Place Data]
    end

    subgraph AI Engine
        CONTEXT_BUILDER[Context Builder]
        PROMPT_MANAGER[Prompt Manager]
        LLM_ROUTER[LLM Router]
        OPENAI_CLIENT[OpenAI GPT-4o]
        LOCAL_LLM[Ollama Mistral]
        RESPONSE_PARSER[Response Parser]
    end

    subgraph Outputs
        RECOMMENDATIONS[Personalized Recommendations]
        DESCRIPTIONS[Place Descriptions]
        SEARCH_RESULTS[NL Search Results]
        INSIGHTS[User Insights]
    end

    USER_HIST --> CONTEXT_BUILDER
    USER_FAV --> CONTEXT_BUILDER
    USER_RATINGS --> CONTEXT_BUILDER
    USER_QUERY --> CONTEXT_BUILDER
    PLACE_DATA --> CONTEXT_BUILDER

    CONTEXT_BUILDER --> PROMPT_MANAGER
    PROMPT_MANAGER --> LLM_ROUTER

    LLM_ROUTER -->|Primary| OPENAI_CLIENT
    LLM_ROUTER -->|Fallback| LOCAL_LLM

    OPENAI_CLIENT --> RESPONSE_PARSER
    LOCAL_LLM --> RESPONSE_PARSER

    RESPONSE_PARSER --> RECOMMENDATIONS
    RESPONSE_PARSER --> DESCRIPTIONS
    RESPONSE_PARSER --> SEARCH_RESULTS
    RESPONSE_PARSER --> INSIGHTS
```

### AI Use Cases

#### 1. Personalized Recommendations

```
Trigger: User opens main menu or requests recommendations
Input:
  - User's last 20 visited places
  - User's favorites list
  - User's ratings (1-5 stars)
  - User's preferred categories
  - Current time of day / day of week
  - User's city

Prompt Template:
  "You are a Moscow/Saint Petersburg city guide expert.
   Based on this user's history: {history}
   Their favorites: {favorites}
   Their ratings: {ratings}
   Current time: {time}
   Recommend 5 places from this list: {available_places}
   Return JSON: [{place_id, score, reason_ru}]"

Output: Ranked list of place IDs with scores and Russian explanations
Caching: Cache recommendations for 6 hours per user
```

#### 2. Place Description Generation

```
Trigger: New place added without AI description, or monthly refresh
Input:
  - Place name, category, address
  - Raw description from source
  - User reviews (if any)
  - Rating and review count

Prompt Template:
  "Write an engaging 2-3 sentence description in Russian for this place:
   Name: {name}
   Category: {category}
   Address: {address}
   Source description: {raw_description}
   Make it warm, inviting, and highlight what makes it special."

Output: 2-3 sentence Russian description
Batch processing: 50 places per batch, run nightly
```

#### 3. Natural Language Search

```
Trigger: User types search query in natural language
Input: User's text query + city

Examples:
  "уютное кафе с хорошим кофе рядом с центром"
  "где поработать с ноутбуком в тишине"
  "романтический ресторан для свидания"

Process:
  1. Extract intent and filters from query using LLM
  2. Convert to structured search parameters
  3. Query PostgreSQL with extracted filters
  4. Re-rank results using LLM

Output: Ranked list of matching places
```

#### 4. Weekly Trend Analysis

```
Trigger: Weekly Celery Beat task (Monday 06:00 MSK)
Input:
  - New places added this week
  - Most favorited places this week
  - Highest rated new places
  - User activity patterns

Output:
  - "Trending this week" collection
  - "New and noteworthy" collection
  - Admin report with insights
```

### LLM Router Logic

```python
class LLMRouter:
    """
    Routes requests to appropriate LLM based on:
    - Task complexity
    - Cost budget
    - Availability
    - Response time requirements
    """

    ROUTING_RULES = {
        "recommendations": "openai",      # Complex, needs quality
        "description_generation": "local", # Batch, cost-sensitive
        "nl_search": "openai",            # Real-time, needs quality
        "trend_analysis": "openai",       # Weekly, quality matters
        "simple_classification": "local", # Fast, simple task
    }

    async def route(self, task_type: str, prompt: str) -> str:
        provider = self.ROUTING_RULES.get(task_type, "openai")
        if provider == "openai":
            return await self.call_openai(prompt)
        else:
            return await self.call_local_llm(prompt)
```

---

## 8. Admin Panel

### Features

```
Dashboard:
  - Total places count by city/category
  - New places added this week
  - Active users count
  - Parse job status
  - Recent errors

Places Management:
  - List/search/filter places
  - Edit place details
  - Upload/manage photos
  - Activate/deactivate places
  - Trigger manual re-parse
  - Verify places

Users Management:
  - List users
  - View user activity
  - Block/unblock users
  - View user favorites and history

Parse Jobs:
  - View parse job history
  - Trigger manual parse
  - View parse logs
  - Configure schedule

Categories Management:
  - Add/edit/reorder categories
  - Toggle category visibility

Cities Management:
  - Add new cities
  - Activate/deactivate cities
  - Configure parse settings per city

Reviews Moderation:
  - View pending reviews
  - Approve/reject reviews
  - Flag inappropriate content
```

### Admin Panel Tech Stack

```
Backend: FastAPI
Frontend: Jinja2 templates + Bootstrap 5 + HTMX
Auth: JWT tokens + bcrypt passwords
Access: Restricted to admin IPs or VPN
```

---

## 9. Infrastructure & Deployment

### Docker Compose Architecture

```mermaid
graph TB
    subgraph docker-compose
        NGINX[nginx:alpine]
        BOT[bot service]
        ADMIN[admin service]
        WORKER[celery-worker x3]
        BEAT[celery-beat]
        PG[postgres:15]
        REDIS[redis:7-alpine]
        MINIO[minio/minio]
        FLOWER[flower - Celery monitor]
        PROMETHEUS[prom/prometheus]
        GRAFANA[grafana/grafana]
        LOKI[grafana/loki]
    end

    NGINX --> BOT
    NGINX --> ADMIN
    NGINX --> FLOWER
    NGINX --> GRAFANA

    BOT --> PG
    BOT --> REDIS
    BOT --> MINIO

    ADMIN --> PG
    ADMIN --> REDIS
    ADMIN --> MINIO

    WORKER --> PG
    WORKER --> REDIS
    WORKER --> MINIO

    BEAT --> REDIS

    PROMETHEUS --> BOT
    PROMETHEUS --> WORKER
    GRAFANA --> PROMETHEUS
    GRAFANA --> LOKI
```

### docker-compose.yml Structure

```yaml
version: "3.9"

services:
  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on: [bot, admin]

  bot:
    build: .
    command: python -m bot.main
    env_file: .env
    depends_on: [postgres, redis, minio]
    restart: unless-stopped

  admin:
    build:
      context: .
      dockerfile: Dockerfile.admin
    command: uvicorn admin.main:app --host 0.0.0.0 --port 8000
    env_file: .env
    depends_on: [postgres, redis]
    restart: unless-stopped

  celery-worker:
    build: .
    command: celery -A tasks.celery_app worker --loglevel=info --concurrency=3
    env_file: .env
    depends_on: [postgres, redis]
    restart: unless-stopped
    deploy:
      replicas: 3

  celery-beat:
    build: .
    command: celery -A tasks.celery_app beat --loglevel=info
    env_file: .env
    depends_on: [redis]
    restart: unless-stopped

  flower:
    build: .
    command: celery -A tasks.celery_app flower --port=5555
    env_file: .env
    depends_on: [redis]

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: jambot
      POSTGRES_USER: jambot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY}
    volumes:
      - minio_data:/data
    restart: unless-stopped

  prometheus:
    image: prom/prometheus
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

  grafana:
    image: grafana/grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped

  loki:
    image: grafana/loki
    volumes:
      - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  minio_data:
  grafana_data:
```

### Environment Variables

```bash
# Bot
BOT_TOKEN=your_telegram_bot_token
WEBHOOK_URL=https://yourdomain.com/webhook
WEBHOOK_SECRET=random_secret_string

# Database
DATABASE_URL=postgresql+asyncpg://jambot:password@postgres:5432/jambot
DATABASE_POOL_SIZE=20
DB_PASSWORD=your_db_password

# Redis
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_PHOTOS=jambot-photos

# AI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=mistral

# Admin
ADMIN_SECRET_KEY=random_admin_secret
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=bcrypt_hashed_password

# Parsing
PROXY_LIST_URL=https://proxy-list.download/api/v1/get?type=https
MAX_CONCURRENT_PARSERS=3
PARSE_DELAY_MIN=3
PARSE_DELAY_MAX=8

# Monitoring
PROMETHEUS_PORT=9090
```

### Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/yourorg/jambot.git && cd jambot

# 2. Configure environment
cp .env.example .env
# Edit .env with your values

# 3. Start infrastructure services
docker-compose up -d postgres redis minio

# 4. Run database migrations
docker-compose run --rm bot alembic upgrade head

# 5. Seed initial data (cities, categories)
docker-compose run --rm bot python -m scripts.seed_data

# 6. Start all services
docker-compose up -d

# 7. Configure Telegram webhook
curl -X POST "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -d "url=https://yourdomain.com/webhook" \
  -d "secret_token=${WEBHOOK_SECRET}"

# 8. Verify webhook
curl "https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo"
```

---

## 10. Project File Structure

```
jambot/
├── .env.example                    # Environment variables template
├── .gitignore
├── docker-compose.yml              # Main compose file
├── docker-compose.dev.yml          # Development overrides
├── Dockerfile                      # Bot/worker image
├── Dockerfile.admin                # Admin panel image
├── ARCHITECTURE.md                 # This document
├── README.md
├── requirements.txt
├── requirements-dev.txt
│
├── alembic/                        # Database migrations
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_initial_schema.py
│       ├── 002_add_ai_recommendations.py
│       └── ...
│
├── bot/                            # Main bot application
│   ├── __init__.py
│   ├── main.py                     # Bot entry point, webhook setup
│   ├── config.py                   # Settings via pydantic-settings
│   │
│   ├── handlers/                   # aiogram message/callback handlers
│   │   ├── __init__.py
│   │   ├── start.py                # /start, onboarding
│   │   ├── menu.py                 # Main menu
│   │   ├── categories.py           # Category browsing
│   │   ├── places.py               # Place list and cards
│   │   ├── favorites.py            # Favorites management
│   │   ├── history.py              # Visit history
│   │   ├── search.py               # Natural language search
│   │   ├── profile.py              # User profile
│   │   ├── rating.py               # Rating and review flow
│   │   └── admin.py                # Admin commands (/admin)
│   │
│   ├── keyboards/                  # Inline and reply keyboards
│   │   ├── __init__.py
│   │   ├── main_menu.py
│   │   ├── categories.py
│   │   ├── place_card.py
│   │   ├── favorites.py
│   │   ├── history.py
│   │   ├── rating.py
│   │   └── profile.py
│   │
│   ├── states/                     # FSM state groups
│   │   ├── __init__.py
│   │   └── bot_states.py
│   │
│   ├── middlewares/                # aiogram middlewares
│   │   ├── __init__.py
│   │   ├── throttling.py
│   │   ├── user.py
│   │   ├── city.py
│   │   ├── logging.py
│   │   └── metrics.py
│   │
│   ├── services/                   # Business logic services
│   │   ├── __init__.py
│   │   ├── place_service.py        # Place queries and logic
│   │   ├── user_service.py         # User management
│   │   ├── favorites_service.py    # Favorites logic
│   │   ├── history_service.py      # Visit history logic
│   │   ├── review_service.py       # Reviews and ratings
│   │   ├── search_service.py       # Search logic
│   │   └── recommendation_service.py # AI recommendations
│   │
│   ├── utils/                      # Utility functions
│   │   ├── __init__.py
│   │   ├── formatters.py           # Message text formatters
│   │   ├── photo_utils.py          # Photo handling
│   │   └── pagination.py           # Pagination helpers
│   │
│   └── templates/                  # Message text templates (Jinja2)
│       ├── place_card.j2
│       ├── place_details.j2
│       ├── welcome.j2
│       └── ...
│
├── db/                             # Database layer
│   ├── __init__.py
│   ├── base.py                     # SQLAlchemy base, engine, session
│   ├── models/                     # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── city.py
│   │   ├── category.py
│   │   ├── place.py
│   │   ├── place_photo.py
│   │   ├── place_tag.py
│   │   ├── user.py
│   │   ├── user_favorite.py
│   │   ├── visit_history.py
│   │   ├── place_review.py
│   │   ├── parse_job.py
│   │   └── ai_recommendation.py
│   │
│   └── repositories/               # Data access layer (Repository pattern)
│       ├── __init__.py
│       ├── base_repository.py
│       ├── place_repository.py
│       ├── user_repository.py
│       ├── favorites_repository.py
│       ├── history_repository.py
│       ├── review_repository.py
│       └── city_repository.py
│
├── parser/                         # Web scraping system
│   ├── __init__.py
│   ├── base_parser.py              # Abstract base parser
│   │
│   ├── sources/                    # Source-specific parsers
│   │   ├── __init__.py
│   │   ├── yandex_maps.py          # Yandex Maps scraper
│   │   └── twogis.py               # 2GIS scraper
│   │
│   ├── anti_detection/             # Anti-detection components
│   │   ├── __init__.py
│   │   ├── proxy_manager.py        # Proxy pool management
│   │   ├── user_agent_rotator.py   # UA rotation
│   │   ├── browser_fingerprint.py  # Fingerprint randomization
│   │   └── delay_engine.py         # Random delay logic
│   │
│   ├── pipeline/                   # Data processing pipeline
│   │   ├── __init__.py
│   │   ├── extractor.py            # Raw data extraction
│   │   ├── validator.py            # Data validation
│   │   ├── deduplicator.py         # Duplicate detection
│   │   ├── normalizer.py           # Data normalization
│   │   └── photo_downloader.py     # Photo download and storage
│   │
│   └── browser/                    # Browser management
│       ├── __init__.py
│       ├── browser_pool.py         # Playwright browser pool
│       └── stealth_config.py       # Stealth plugin configuration
│
├── tasks/                          # Celery tasks
│   ├── __init__.py
│   ├── celery_app.py               # Celery app configuration
│   ├── beat_schedule.py            # Celery Beat schedule
│   ├── parse_tasks.py              # Parsing tasks
│   ├── ai_tasks.py                 # AI processing tasks
│   └── maintenance_tasks.py        # Cleanup, health checks
│
├── ai/                             # AI integration
│   ├── __init__.py
│   ├── llm_router.py               # Route to OpenAI or local LLM
│   ├── openai_client.py            # OpenAI API client
│   ├── ollama_client.py            # Ollama local LLM client
│   ├── recommendation_engine.py    # Recommendation logic
│   ├── description_generator.py    # Place description generation
│   ├── nl_search.py                # Natural language search
│   └── prompts/                    # Prompt templates
│       ├── recommendations.py
│       ├── description.py
│       ├── search.py
│       └── analysis.py
│
├── admin/                          # Admin panel (FastAPI)
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry point
│   ├── auth.py                     # JWT authentication
│   ├── routers/                    # FastAPI routers
│   │   ├── __init__.py
│   │   ├── dashboard.py
│   │   ├── places.py
│   │   ├── users.py
│   │   ├── parse_jobs.py
│   │   ├── categories.py
│   │   ├── cities.py
│   │   └── reviews.py
│   │
│   └── templates/                  # Jinja2 HTML templates
│       ├── base.html
│       ├── dashboard.html
│       ├── places/
│       │   ├── list.html
│       │   ├── detail.html
│       │   └── edit.html
│       └── users/
│           ├── list.html
│           └── detail.html
│
├── storage/                        # File storage (MinIO client)
│   ├── __init__.py
│   ├── minio_client.py
│   └── photo_storage.py
│
├── monitoring/                     # Monitoring configuration
│   ├── prometheus.yml
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   ├── bot_metrics.json
│   │   │   └── parser_metrics.json
│   │   └── datasources/
│   │       └── prometheus.yml
│   └── loki/
│       └── loki-config.yml
│
├── nginx/                          # Nginx configuration
│   ├── nginx.conf
│   └── ssl/
│
├── scripts/                        # Utility scripts
│   ├── seed_data.py                # Seed initial cities and categories
│   ├── import_places.py            # Manual place import from CSV
│   ├── export_places.py            # Export places to CSV
│   └── health_check.py             # System health check
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── conftest.py
    ├── test_bot/
    │   ├── test_handlers.py
    │   └── test_services.py
    ├── test_parser/
    │   ├── test_yandex_parser.py
    │   ├── test_twogis_parser.py
    │   └── test_pipeline.py
    ├── test_ai/
    │   └── test_recommendations.py
    └── test_db/
        └── test_repositories.py
```

---

## 11. Security Considerations

### Bot Security

```
1. Webhook secret token validation (X-Telegram-Bot-Api-Secret-Token header)
2. Rate limiting per user (5 requests/second via Redis)
3. Input sanitization for all user text inputs
4. SQL injection prevention via SQLAlchemy ORM (parameterized queries)
5. Admin commands restricted to admin user IDs (whitelist in config)
6. No sensitive data in bot messages or logs
```

### Parser Security

```
1. Proxy credentials stored in environment variables only
2. Browser sessions isolated per task
3. No personal data collected from scraped pages
4. Respect robots.txt where legally required
5. Rate limiting to avoid overloading target servers
6. User-agent strings represent real browsers only
```

### Infrastructure Security

```
1. All services in private Docker network (no direct external access)
2. Only Nginx exposed to internet (ports 80, 443)
3. PostgreSQL not exposed externally
4. Redis not exposed externally
5. MinIO admin not exposed externally
6. Admin panel behind additional HTTP basic auth
7. SSL/TLS for all external connections
8. Secrets via environment variables (never in code)
9. Regular dependency updates (Dependabot)
```

---

## 12. Scaling Strategy

### Phase 1: Moscow + Saint Petersburg (Launch)

```
Infrastructure:
  - Single VPS: 4 CPU, 8GB RAM, 100GB SSD
  - Single PostgreSQL instance
  - Single Redis instance
  - 2-3 Celery workers
  - Estimated capacity: 10,000 users, 5,000 places
```

### Phase 2: Top 10 Russian Cities

```
Infrastructure:
  - Upgrade to 8 CPU, 16GB RAM, 200GB SSD
  - PostgreSQL with read replica
  - Redis Sentinel for HA
  - 5-10 Celery workers
  - Estimated capacity: 50,000 users, 25,000 places
```

### Phase 3: All Russian Regions

```
Infrastructure:
  - Multiple VPS or Kubernetes cluster
  - PostgreSQL with sharding by city
  - Redis Cluster
  - Auto-scaling Celery workers
  - CDN for photos (Cloudflare or Yandex CDN)
  - Estimated capacity: 500,000+ users, 200,000+ places

Database Sharding Strategy:
  - Shard by city_id
  - Moscow + SPb on dedicated shard (highest traffic)
  - Other cities grouped by region
  - Cross-shard queries via application layer
```

### Performance Targets

| Metric | Target |
|---|---|
| Bot response time | < 500ms (p95) |
| Place card load time | < 1 second |
| Search response time | < 2 seconds |
| AI recommendation time | < 3 seconds (cached) |
| Parser throughput | 100 places/hour per worker |
| Database query time | < 50ms (p95) |
| Uptime | 99.9% |

---

## Appendix: Initial Data Seed

### Cities (Phase 1)

```sql
INSERT INTO cities (name, region, timezone, is_active) VALUES
('Москва', 'Московская область', 'Europe/Moscow', true),
('Санкт-Петербург', 'Ленинградская область', 'Europe/Moscow', true);
```

### Categories

```sql
INSERT INTO categories (slug, name_ru, emoji, sort_order) VALUES
('eat', 'Поесть', '🍽️', 1),
('breakfast', 'Завтрак', '☕', 2),
('work', 'Поработать с ноутбуком', '💻', 3),
('terrace', 'Погреться на террасах', '🌿', 4),
('specialty_coffee', 'Спешелти кофе', '☕', 5),
('date', 'Свидание', '💑', 6),
('friends', 'Вечер с друзьями', '🥂', 7),
('dance', 'Потанцевать', '💃', 8),
('drink', 'Выпить', '🍸', 9),
('beauty', 'Красота', '💅', 10),
('countryside', 'За городом', '🌲', 11);
```

---

*Document version: 1.0*
*Last updated: 2026-02-27*
*Status: Blueprint — Ready for Implementation*
