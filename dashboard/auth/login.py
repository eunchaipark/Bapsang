import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from db import get_connection
from psycopg2.extras import execute_values
import hashlib

def get_user_by_nickname(username: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM users WHERE username = %s", (username,))
        return cur.fetchone()
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def create_user_with_categories(username: str, selected_categories: list):
    conn = get_connection()
    try:
        cur = conn.cursor()

        password_hash = hashlib.sha256(username.encode()).hexdigest()

        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING user_id",
            (username, password_hash)
        )
        user_id = cur.fetchone()[0]

        if selected_categories:
            execute_values(cur, """
                INSERT INTO user_category_weights (user_id, category_name, weight)
                VALUES %s
                ON CONFLICT (user_id, category_name) DO UPDATE SET weight = EXCLUDED.weight
            """, [(user_id, cat, 5.0) for cat in selected_categories])

        conn.commit()
        return user_id
    except Exception as e:
        conn.rollback()
        print(f"Error creating user: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def get_all_categories():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT category_name FROM foods ORDER BY category_name")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []
    finally:
        cur.close()
        conn.close()