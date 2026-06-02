import time
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=1)
def run_batch():
    print("배치 실행 - 아직 미구현")

print("배치 스케줄러 시작")
scheduler.start()