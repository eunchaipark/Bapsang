import os
from db import get_connection

from pyspark.sql import SparkSession

spark = (
        SparkSession.builder \
        .appName("Bapsang") \
        .master("local[2]") \
        .config("spark.driver.memory", "2g") \
        .config("spark.sql.shuffle.partitions", "4") \
        .getOrCreate()
    )


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


def get_current_max_id():
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            SELECT COALESCE(MAX(log_id), 0)
            FROM user_click_logs
        """)

        return cur.fetchone()[0]

    finally:
        cur.close()
        conn.close()



DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'password')
JDBC_URL = "jdbc:postgresql://postgresql:5432/bapsang"

def load_logs_spark(last_offset, max_log_id):
    return (
        spark.read
        .format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", f"""
            (
                SELECT
                    log_id,
                    user_id,
                    action_type,
                    category_name
                FROM user_click_logs
                WHERE log_id > {last_offset}
                  AND log_id <= {max_log_id}
            ) t
        """)
        .option("user", DB_USER)
        .option("password", DB_PASSWORD)
        .option(
            "driver",
            "org.postgresql.Driver"
        )
        .load()
    )


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