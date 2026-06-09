from db import get_connection
from collections import defaultdict

from pyspark.sql.functions import when, sum as spark_sum

def aggregate_spark(df):
    return (
        df.withColumn(
            "score",
            when(df.action_type == "LIKE", 3).otherwise(1)
        ).groupBy(
            "user_id",
            "category_name"
        ).agg(
            spark_sum("score").alias("weight")
        )
    )


def upsert_weights(df):
    rows = df.collect()
    conn = get_connection()

    try:
        cur = conn.cursor()

        for row in rows:
            cur.execute("""
                INSERT INTO user_category_weights
                (
                    user_id,
                    category_name,
                    weight,
                    updated_at
                )
                VALUES (%s,%s,%s,NOW())

                ON CONFLICT(user_id, category_name)
                DO UPDATE SET
                    weight =
                        user_category_weights.weight
                        + EXCLUDED.weight,
                    updated_at = NOW()
            """,
            (
                row["user_id"],
                row["category_name"],
                row["weight"]
            ))

        conn.commit()

    finally:
        cur.close()
        conn.close()
