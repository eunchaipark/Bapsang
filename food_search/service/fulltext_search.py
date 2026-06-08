from food_search.repository.food_repo import search_fulltext

def get_fulltext_search_results(query_str: str, limit: int = 20) -> list:
    """
    사용자의 검색어를 데이터베이스 Full-Text Search를 통해 키워드 매칭합니다.
    """
    if not query_str:
        return []
        
    return search_fulltext(query_str, limit)
