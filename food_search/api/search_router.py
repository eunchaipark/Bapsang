from fastapi import APIRouter, Query, HTTPException
from food_search.service.fulltext_search import get_fulltext_search_results
from food_search.service.vector_search import get_vector_search_results
from food_search.service.hybrid_merger import merge_results

router = APIRouter()

@router.get("/api/search")
async def search_foods(q: str = Query(..., description="검색어"), limit: int = 10):
    """
    Full-Text 키워드 검색과 pgvector 의미론적 검색 결과를 병합한 하이브리드 검색 결과를 반환합니다.
    """
    try:
        # 1. GIN 인덱스 기반 Full-Text 검색 결과 (Top 20 후보군)
        ft_results = get_fulltext_search_results(q, limit=20)
        
        # 2. pgvector 기반 코사인 유사도 검색 결과 (Top 20 후보군)
        vec_results = get_vector_search_results(q, limit=20)
        
        # 3. RRF(Reciprocal Rank Fusion) 기반 하이브리드 병합 및 최종 정렬
        merged = merge_results(ft_results, vec_results, limit=limit)
        
        return {
            "query": q,
            "count": len(merged),
            "results": merged
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
