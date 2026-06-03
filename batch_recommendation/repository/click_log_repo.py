from db import get_connection

def fetch_als_input():
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                user_id,
                food_id,
                MAX(CASE action_type
                    WHEN 'CLICK' THEN 1
                    WHEN 'LIKE'  THEN 5
                END) AS rating
            FROM user_click_logs
            GROUP BY user_id, food_id
        """)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()