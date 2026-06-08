from db import get_connection


def get_last_offset():

    conn = get_connection()
    
    try:
        cur = conn.cursor()
        
        cur.execute("""
                SELECT last_log_id
                FROM streaming_offsets
                WHERE id = 1
            """)
        
        row = cur.fetchone()
        
        if row:
            return row[0]

        return 0

    finally:
        cur.close()
        conn.close()


def update_offset(last_log_id):

    conn = get_connection()

    try:
        cur = conn.cursor()
        cur.execute("""
                UPDATE streaming_offsets
                SET
                    last_log_id = %s,
                    updated_at = NOW()
                WHERE id = 1
            """,(last_log_id, )
            )
        
        conn.commit()

    finally:
        cur.close()
        conn.close()


def load_logs(last_offset):

    conn = get_connection()

    try:
        cur = conn.cursor()
        cur.execute("""
                SELECT
                    log_id,
                    user_id,
                    food_id,
                    action_type,
                    category_name
                FROM user_click_logs
                WHERE log_id > %s
                ORDER BY log_id
            """,(last_offset, )
            )

        rows = cur.fetchall()

        return [
            {
            "log_id":r[0],
            "user_id":r[1],
            "food_id":r[2],
            "action_type":r[3],
            "category_name":r[4]
            }
            for r in rows
        ]

    finally:
        cur.close()
        conn.close()
