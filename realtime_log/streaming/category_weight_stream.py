'''
import time

print("스트리밍 시작 - 아직 미구현")
while True:
    time.sleep(20)
'''
from time import sleep
from realtime_log.repository.offset_repo import get_last_offset
from realtime_log.repository.offset_repo import update_offset
from realtime_log.repository.weight_repo import upsert_weights


from collections import defaultdict


def aggregate(logs):

    result = defaultdict(int)

    for log in logs:

        score = 1

        if log["action_type"] == "LIKE":
            score = 3

        key = (
            log["user_id"],
            log["category"]
        )

        result[key] += score

    return result


while True:

    last_offset = get_last_offset()

    logs = load_logs(last_offset)

    weights = aggregate(logs)

    upsert_weights(weights)

    update_offset(max_log_id)

    sleep(20)
    