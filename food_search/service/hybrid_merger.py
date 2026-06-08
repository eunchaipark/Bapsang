def merge_results(ft_results: list, vec_results: list, limit: int = 10) -> list:
    """
    RRF(Reciprocal Rank Fusion) 알고리즘을 사용하여 Full-Text 검색 결과와
    벡터 검색 결과를 가중 병합합니다. (Full-Text 가중치 60%, Vector 가중치 40%)
    점수가 동일한 경우에는 click_count가 높은 순서대로 2차 정렬합니다.
    """
    rrf_map = {}
    item_info = {}
    
    # 1. Full-Text 검색 결과 병합 (랭크 1부터 시작)
    for rank, item in enumerate(ft_results, start=1):
        food_id = item["food_id"]
        item_info[food_id] = {
            "food_id": food_id,
            "food_name": item["food_name"],
            "category_name": item["category_name"],
            "click_count": item["click_count"]
        }
        # RRF 공식: 가중치 * (1 / (rank + 60))
        rrf_map[food_id] = rrf_map.get(food_id, 0.0) + 0.6 * (1.0 / (rank + 60))
        
    # 2. Vector 검색 결과 병합
    for rank, item in enumerate(vec_results, start=1):
        food_id = item["food_id"]
        if food_id not in item_info:
            item_info[food_id] = {
                "food_id": food_id,
                "food_name": item["food_name"],
                "category_name": item["category_name"],
                "click_count": item["click_count"]
            }
        # RRF 공식: 가중치 * (1 / (rank + 60))
        rrf_map[food_id] = rrf_map.get(food_id, 0.0) + 0.4 * (1.0 / (rank + 60))
        
    # 3. RRF 점수 내림차순, 동점일 경우 click_count 내림차순 정렬
    sorted_food_ids = sorted(
        rrf_map.keys(),
        key=lambda fid: (rrf_map[fid], item_info[fid]["click_count"]),
        reverse=True
    )
    
    # 4. 결과 개수 제한하여 리턴 리스트 구성
    merged_results = []
    for fid in sorted_food_ids[:limit]:
        info = item_info[fid]
        merged_results.append({
            "food_id": info["food_id"],
            "food_name": info["food_name"],
            "category_name": info["category_name"],
            "click_count": info["click_count"],
            "rrf_score": rrf_map[fid]
        })
        
    return merged_results
