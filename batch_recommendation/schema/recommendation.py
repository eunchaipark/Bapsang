from pydantic import BaseModel

class RecommendationItem(BaseModel):
    food_id: int
    food_name: str
    category_name: str
    score: float
    rank: int

class RecommendationResponse(BaseModel):
    user_id: int
    recommendations: list[RecommendationItem]