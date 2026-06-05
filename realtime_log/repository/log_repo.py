from db import get_connection


async def insert_log(payload):

    conn = get_connection()

    cursor = conn.cursor()
    
    sql = """
    INSERT INTO user_click_logs
    (
        user_id,
        food_id,
        category_name,
        action_type
    )
    VALUES (%s,%s,%s,%s)
    """

    cursor.execute(
        sql,
        (
            payload["user_id"],
            payload["food_id"],
            payload["category_name"],
            payload["action_type"]
        )
    )

    conn.commit()

    cursor.close()
    conn.close()