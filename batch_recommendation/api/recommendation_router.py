from fastapi import APIRouter, HTTPException
from batch_recommendation.repository.recommendation_repo import fetch_recommendations
from batch_recommendation.schema.recommendation import RecommendationItem, RecommendationResponse

router = APIRouter()

@router.get("/{user_id}", response_model=RecommendationResponse)
def get_recommendations(user_id: int):
    rows = fetch_recommendations(user_id)
    if not rows:
        raise HTTPException(status_code=404, detail="추천 결과가 없습니다.")
    return RecommendationResponse(
        user_id=user_id,
        recommendations=[
            RecommendationItem(
                food_id=row[0],
                food_name=row[1],
                category_name=row[2],
                score=row[3],
                rank=row[4],
            )
            for row in rows
        ]
    )