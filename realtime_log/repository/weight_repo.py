from db import get_connection
from collections import defaultdict


def aggregate(logs):
    print(f"aggregate loge check : {logs}")
    print("type = ",type(logs))
    result = defaultdict(int)

    for log in logs:

        score = 1

        if log["action_type"] == "LIKE":
            score = 3

        key = (
            log["user_id"],
            log["category_name"]
        )

        result[key] += score

    return result


def upsert_weights(weights):

    conn = get_connection()

    try:
        cur = conn.cursor()

        for (user_id, category_name), weight in weights.items():

            cur.execute("""
                INSERT INTO user_category_weights (
                    user_id,
                    category_name,
                    weight,
                    updated_at
                )
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id, category_name)
                DO UPDATE SET
                    weight = user_category_weights.weight + EXCLUDED.weight,
                    updated_at = NOW()
            """, (
                user_id,
                category_name,
                weight
            ))

        conn.commit()

    finally:
        cur.close()
        conn.close()
