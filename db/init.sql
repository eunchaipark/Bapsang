-- =============================================
-- Bapsang init.sql
-- PostgreSQL + pgvector
-- =============================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ---------------------------------------------
-- 1. users
-- ---------------------------------------------
CREATE TABLE users (
    user_id    SERIAL       PRIMARY KEY,
    username   VARCHAR(50)  NOT NULL UNIQUE,
    password   VARCHAR(255) NOT NULL,
    created_at TIMESTAMP    DEFAULT NOW()
);

-- ---------------------------------------------
-- 2. foods
-- ---------------------------------------------
CREATE TABLE foods (
    food_id       SERIAL       PRIMARY KEY,
    food_code     VARCHAR(20)  NOT NULL UNIQUE,
    food_name     VARCHAR(200) NOT NULL,
    category_code INT          NOT NULL,
    category_name VARCHAR(50)  NOT NULL,
    click_count   INT          DEFAULT 0,
    search_text   TEXT,
    embedding     vector(384),
    created_at    TIMESTAMP    DEFAULT NOW()
);

CREATE INDEX idx_foods_fulltext
    ON foods USING GIN (to_tsvector('simple', food_name));

CREATE INDEX idx_foods_category_click
    ON foods (category_code, click_count DESC);

-- ivfflat 인덱스는 embedding 적재 완료 후 별도 실행
-- CREATE INDEX idx_foods_embedding
--     ON foods USING ivfflat (embedding vector_cosine_ops)
--     WITH (lists = 100);

-- ---------------------------------------------
-- 3. user_click_logs
-- ---------------------------------------------
CREATE TABLE user_click_logs (
    log_id        BIGSERIAL    PRIMARY KEY,
    user_id       INT          NOT NULL REFERENCES users(user_id),
    food_id       INT          NOT NULL REFERENCES foods(food_id),
    action_type   VARCHAR(10)  NOT NULL CHECK (action_type IN ('CLICK', 'LIKE')),
    category_name VARCHAR(50)  NOT NULL,
    logged_at     TIMESTAMP(3) DEFAULT NOW()
);

CREATE INDEX idx_click_logs_user_time
    ON user_click_logs (user_id, logged_at);

-- ---------------------------------------------
-- 4. streaming_offsets (1행 고정)
-- ---------------------------------------------
CREATE TABLE streaming_offsets (
    id          INT          PRIMARY KEY DEFAULT 1,
    last_log_id BIGINT       NOT NULL DEFAULT 0,
    updated_at  TIMESTAMP(3) DEFAULT NOW(),
    CONSTRAINT single_row CHECK (id = 1)
);

INSERT INTO streaming_offsets (id, last_log_id) VALUES (1, 0);

-- ---------------------------------------------
-- 5. user_category_weights
-- ---------------------------------------------
CREATE TABLE user_category_weights (
    id            BIGSERIAL    PRIMARY KEY,
    user_id       INT          NOT NULL REFERENCES users(user_id),
    category_name VARCHAR(50)  NOT NULL,
    weight        FLOAT        DEFAULT 0.0,
    updated_at    TIMESTAMP(3) DEFAULT NOW(),
    UNIQUE (user_id, category_name)
);

-- ---------------------------------------------
-- 6. recommendations
-- ---------------------------------------------
CREATE TABLE recommendations (
    rec_id       BIGSERIAL  PRIMARY KEY,
    user_id      INT        NOT NULL REFERENCES users(user_id),
    food_id      INT        NOT NULL REFERENCES foods(food_id),
    score        FLOAT      NOT NULL,
    rank         INT        NOT NULL,
    batch_run_at TIMESTAMP  NOT NULL
);

CREATE INDEX idx_recommendations_user_rank
    ON recommendations (user_id, rank);

CREATE INDEX idx_recommendations_user_batch
    ON recommendations (user_id, batch_run_at DESC);