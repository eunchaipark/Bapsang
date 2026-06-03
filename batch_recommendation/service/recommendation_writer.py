from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALSModel


def extract_top20(spark: SparkSession, model: ALSModel):
    users_df = model.userFactors.select("id").withColumnRenamed("id", "user_id")
    recommendations = model.recommendForUserSubset(users_df, 20)

    rows = []
    batch_run_at = datetime.now()

    for row in recommendations.collect():
        user_id = row["user_id"]
        for rank, rec in enumerate(row["recommendations"], start=1):
            rows.append((
                user_id,
                int(rec["food_id"]),
                float(rec["rating"]),
                rank,
                batch_run_at,
            ))

    print(f"Top 20 추출 완료: {len(rows)}건")
    return rows