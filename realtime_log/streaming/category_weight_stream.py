from time import sleep
from realtime_log.repository.offset_repo import get_last_offset, update_offset, get_current_max_id, load_logs_spark
from realtime_log.repository.weight_repo import aggregate_spark, upsert_weights
from pyspark.sql import SparkSession


while True:
    try:
        last_offset = get_last_offset()

        max_log_id = get_current_max_id()

        if max_log_id <= last_offset:
            print("no new logs")
            sleep(20)
            continue
        
        #새로 입력된 데이터 있는지 확인
        df = load_logs_spark(last_offset, max_log_id)

        if df.rdd.isEmpty():
            print("no new logs")
            sleep(20)
            continue

        #가중치 부여
        result_df = aggregate_spark(df)

        upsert_weights(result_df)
        
        update_offset(max_log_id)
        
        print(f"processed {max_log_id} logs")

    except Exception as e:
        print(f"[STREAM ERROR] : {e}")
    
    sleep(20)
