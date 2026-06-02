import pandas as pd
import psycopg2
import os
from psycopg2.extras import execute_values

# ─────────────────────────────────────────
# DB 연결
# ─────────────────────────────────────────
conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=int(os.getenv('POSTGRES_PORT', 5432)),
    dbname=os.getenv('POSTGRES_DB', 'bapsang'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'password'),
)
cur = conn.cursor()

# ─────────────────────────────────────────
# CSV 로드
# ─────────────────────────────────────────
print("foods_processed.csv 로드 중...")
df = pd.read_csv('data/processed/foods_processed.csv', encoding='utf-8-sig')
print(f"행 수: {len(df)}")

# ─────────────────────────────────────────
# PostgreSQL INSERT
# ─────────────────────────────────────────
print("DB INSERT 중...")

rows = df[['food_code', 'food_name', 'category_code', 'category_name',
           'click_count', 'search_text', 'embedding']].values.tolist()

execute_values(cur, """
    INSERT INTO foods (food_code, food_name, category_code, category_name, click_count, search_text, embedding)
    VALUES %s
    ON CONFLICT (food_code) DO NOTHING
""", rows)

conn.commit()
print(f"INSERT 완료: {len(rows)}개")

# ─────────────────────────────────────────
# ivfflat 인덱스 생성 (적재 완료 후 바로 실행)
# ─────────────────────────────────────────
print("ivfflat 인덱스 생성 중...")
cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_foods_embedding
    ON foods USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
""")
conn.commit()
print("인덱스 생성 완료")

cur.close()
conn.close()
print("\n전체 완료")