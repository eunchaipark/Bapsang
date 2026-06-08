from db import get_connection

def search_fulltext(query_str: str, limit: int = 20) -> list:
    """
    to_tsvector와 plainto_tsquery를 사용하여 GIN 인덱스 기반 키워드 검색을 수행합니다.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # ts_rank를 사용하여 매칭 스코어를 계산하고 정렬합니다.
        sql = """
            SELECT food_id, food_name, category_name, click_count,
                   ts_rank(to_tsvector('simple', food_name), plainto_tsquery('simple', %s)) AS score
            FROM foods
            WHERE to_tsvector('simple', food_name) @@ plainto_tsquery('simple', %s)
            ORDER BY score DESC
            LIMIT %s;
        """
        cur.execute(sql, (query_str, query_str, limit))
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "food_id": r[0],
                "food_name": r[1],
                "category_name": r[2],
                "click_count": r[3],
                "score": float(r[4])
            })
        return results
    finally:
        cur.close()
        conn.close()

def search_vector(embedding_vector: list, limit: int = 20) -> list:
    """
    pgvector의 <=> (cosine distance) 연산자를 사용하여 문맥적 유사성 검색을 수행합니다.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        # list를 '[0.1, 0.2, ...]' 포맷의 문자열로 변환하여 캐스팅합니다.
        vector_str = "[" + ",".join(str(x) for x in embedding_vector) + "]"
        
        # 1.0 - Cosine Distance = Cosine Similarity
        sql = """
            SELECT food_id, food_name, category_name, click_count,
                   (1.0 - (embedding <=> %s::vector)) AS score
            FROM foods
            ORDER BY embedding <=> %s::vector
            LIMIT %s;
        """
        cur.execute(sql, (vector_str, vector_str, limit))
        rows = cur.fetchall()
        
        results = []
        for r in rows:
            results.append({
                "food_id": r[0],
                "food_name": r[1],
                "category_name": r[2],
                "click_count": r[3],
                "score": float(r[4])
            })
        return results
    finally:
        cur.close()
        conn.close()
