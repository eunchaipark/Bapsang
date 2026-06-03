from psycopg2.extras import execute_values
from db import get_connection


def save_recommendations(rows: list):
    if not rows:
        print("저장할 추천 데이터 없음")
        return

    conn = get_connection()
    try:
        cur = conn.cursor()

        batch_run_at = rows[0][4]
        user_ids = list(set(r[0] for r in rows))
        food_ids = list(set(r[1] for r in rows))

        # 새 배치 INSERT
        execute_values(cur, """
            INSERT INTO recommendations (user_id, food_id, score, rank, batch_run_at)
            VALUES %s
        """, rows)

        # 이전 배치 DELETE
        cur.execute("""
            DELETE FROM recommendations
            WHERE user_id = ANY(%s)
            AND batch_run_at < %s
        """, (user_ids, batch_run_at))

        # click_count 갱신
        cur.execute("""
            UPDATE foods
            SET click_count = sub.cnt
            FROM (
                SELECT food_id, COUNT(*) AS cnt
                FROM user_click_logs
                GROUP BY food_id
            ) sub
            WHERE foods.food_id = sub.food_id
        """)

        conn.commit()
        print(f"recommendations 저장 완료: {len(rows)}건")
        print(f"click_count 갱신 완료: {len(food_ids)}개 음식")

    finally:
        cur.close()
        conn.close()


def fetch_recommendations(user_id: int):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.food_id, f.food_name, f.category_name, r.score, r.rank
            FROM recommendations r
            JOIN foods f ON r.food_id = f.food_id
            WHERE r.user_id = %s
            AND r.batch_run_at = (
                SELECT MAX(batch_run_at)
                FROM recommendations
                WHERE user_id = %s
            )
            ORDER BY r.rank
        """, (user_id, user_id))
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()