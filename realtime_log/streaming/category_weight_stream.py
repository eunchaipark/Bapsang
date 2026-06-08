from time import sleep
from realtime_log.repository.offset_repo import get_last_offset, update_offset, load_logs
from realtime_log.repository.weight_repo import aggregate, upsert_weights


while True:
    try:
        last_offset = get_last_offset()

        logs = load_logs(last_offset)
        if not logs:
            print("[STREAM] no new logs")
            sleep(20)
            continue

        weights = aggregate(logs)

        upsert_weights(weights)

        max_log_id = max(
            log["log_id"]
            for log in logs
        )
        update_offset(max_log_id)
        
        print(f"[STREAM] processed {len(logs)} logs")

    except Exception as e:
        print(f"[STREAM ERROR] : {e}")
    
    sleep(20)