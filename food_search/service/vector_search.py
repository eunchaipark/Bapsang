from sentence_transformers import SentenceTransformer
from food_search.repository.food_repo import search_vector

# 모델 로드 (모듈 로딩 시 1회 수행하여 캐싱)
print("Loading multilingual sentence transformer model...")
model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
print("Model loaded successfully.")

def get_vector_search_results(query_str: str, limit: int = 20) -> list:
    """
    사용자의 자연어 검색어를 384차원 벡터로 변환한 후 pgvector 유사도 조회를 호출합니다.
    """
    if not query_str:
        return []
    
    # 문장 임베딩 생성
    query_vector = model.encode(query_str).tolist()
    
    # 리포지토리 호출
    return search_vector(query_vector, limit)
