from apscheduler.schedulers.blocking import BlockingScheduler
from batch_recommendation.service.als_trainer import train_als
from batch_recommendation.service.recommendation_writer import extract_top20
from batch_recommendation.repository.recommendation_repo import save_recommendations


def run_batch():
    print("배치 시작")
    spark, model = train_als()
    if model is None:
        print("배치 종료 (학습 데이터 없음)")
        return
    rows = extract_top20(spark, model)
    save_recommendations(rows)
    spark.stop()
    print("배치 완료")


scheduler = BlockingScheduler()
scheduler.add_job(run_batch, 'interval', hours=1)

print("배치 스케줄러 시작 (1시간 주기)")
run_batch()
scheduler.start()