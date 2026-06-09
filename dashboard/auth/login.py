import sys
import os
# PYTHONPATH에 /app이 들어가 있지만 로컬 구동 시를 대비해 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db import get_connection

def get_user_by_nickname(username: str):
    """
    닉네임으로 사용자를 조회합니다.
    존재하는 경우 (user_id, username) 튜플을 반환하고, 없으면 None을 반환합니다.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        return row
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def create_user_with_categories(username: str, selected_categories: list):
    """
    새로운 사용자 프로필을 생성하고 선호 카테고리의 초기 가중치를 데이터베이스에 등록합니다.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 1. users 테이블에 등록 (비밀번호는 임시 더미 해시값 사용)
        dummy_password = "dummy_pbkdf2_sha256$260000$dummy_salt$dummy_hash"
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING user_id",
            (username, dummy_password)
        )
        user_id = cur.fetchone()[0]

        # 2. 선호 카테고리 가중치 초기 등록 (각 카테고리별 초기값 5.0)
        if selected_categories:
            insert_weights = []
            for category in selected_categories:
                insert_weights.append((user_id, category, 5.0))
            
            # UNIQUE (user_id, category_name) 제약조건에 맞춰 Upsert 수행
            from psycopg2.extras import execute_values
            execute_values(cur, """
                INSERT INTO user_category_weights (user_id, category_name, weight)
                VALUES %s
                ON CONFLICT (user_id, category_name) DO UPDATE SET weight = EXCLUDED.weight
            """, insert_weights)

        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        print(f"Error creating user with categories: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_all_categories():
    """
    foods 테이블에서 고유한 식품대분류명 목록을 조회하여 반환합니다.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category_name FROM foods ORDER BY category_name")
        rows = cur.fetchall()
        return [row[0] for row in rows]
    except Exception as e:
        print(f"Error fetching categories: {e}")
        # DB 연결이 안 되었거나 데이터가 없을 때를 대비한 기본 카테고리 리스트 fallback
        return [
            "밥류", "면 및 만두류", "국 및 탕류", "찌개 및 전골류", "볶음류",
            "조림류", "구이류", "전·적 및 부침류", "찜류", "생채·무침류",
            "김치류", "튀김류", "장아찌·젓갈류", "단독반찬류", "죽 및 스프류",
            "곡류 및 서류", "빵 및 과자류", "떡류", "만두류", "음료 및 차류",
            "유제품류", "과일류", "채소류", "수산물류", "육류"
        ]
    finally:
        cur.close()
        conn.close()
