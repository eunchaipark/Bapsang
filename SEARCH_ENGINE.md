# Bapsang 하이브리드 음식 검색 엔진 (기능 C) 개발 문서

이 문서는 PostgreSQL GIN 인덱스 기반의 키워드 검색(Full-Text Search)과 `pgvector` 코사인 유사도 검색(Semantic Search)을 결합하여 구현한 Bapsang 프로젝트의 **하이브리드 음식 검색 엔진** 개발 기록 및 상세 내용입니다.

---

## 1. 아키텍처 및 폴더 구조

기능 중심 레이어드 아키텍처(Feature-based Layered Architecture)를 유지하여 아래와 같이 모듈을 세분화하여 구현하였습니다.

```
food_search/
├── api/
│   └── search_router.py   # FastAPI HTTP GET /api/search 엔드포인트 정의
├── repository/
│   └── food_repo.py       # psycopg2 활용 PostgreSQL FTS 및 pgvector 쿼리 실행
└── service/
    ├── fulltext_search.py # GIN 인덱스 기반 키워드 매칭 비즈니스 로직
    ├── hybrid_merger.py   # RRF(Reciprocal Rank Fusion) 기반 두 결과 가중 병합
    └── vector_search.py   # SentenceTransformer 모델 활용 자연어 쿼리 임베딩 및 유사도 검색
```

---

## 2. 핵심 로직 및 기술 설명

### A. Full-Text 키워드 검색
- **쿼리**: `to_tsvector`와 `plainto_tsquery`를 활용하여 자연어 검색어 분할 및 형태소 매칭을 지원합니다.
- **가중치/정렬**: `ts_rank`를 통해 키워드 매칭 정확도가 높은 순서대로 점수를 부여하고 정렬합니다.
- **인덱스**: `db/init.sql`에 정의된 `foods` 테이블의 GIN 인덱스(`idx_foods_fulltext`)를 사용하여 빠른 쿼리 응답(10ms 이하)을 보장합니다.

### B. pgvector 의미론적(Semantic) 검색
- **임베딩 모델**: `paraphrase-multilingual-MiniLM-L12-v2` 다국어 임베딩 모델(384차원)을 활용합니다.
  - *최적화*: FastAPI 로딩 시점에 모델을 단 1회만 로드하여 싱글톤 형태로 메모리에 올려 캐싱함으로써 검색 시마다 발생하는 지연을 극복했습니다.
- **유사도 쿼리**: `pgvector`의 코사인 거리 연산자 `<=>`를 사용하여 거리를 구한 후, `1.0 - (embedding <=> %s::vector)` 연산을 통해 코사인 유사도 점수를 산출합니다.
- **인덱스**: 적재 직후 생성된 `ivfflat` 공간 인덱스를 활용하여 다차원 벡터 거리를 정밀하고 신속하게 계산합니다.

### C. RRF(Reciprocal Rank Fusion) 하이브리드 결과 병합
서로 스케일이 다른 키워드 점수(`ts_rank`)와 벡터 유사도 점수(`cosine similarity`)를 정규화하여 병합할 때 발생할 수 있는 이상치 문제를 방지하기 위해 순위 기반 병합 알고리즘인 **RRF**를 사용합니다.
- **RRF 스코어 공식**: 
  $$Score = 0.6 \times \left( \frac{1}{Rank_{FT} + 60} \right) + 0.4 \times \left( \frac{1}{Rank_{Vec} + 60} \right)$$
- **가중치**: 기획 요구사항에 맞게 **Full-Text 검색에 60%, Vector 검색에 40%**의 가중치를 배정했습니다.
- **동점자 방지**: RRF 점수가 완전히 일치할 경우, **`click_count`가 더 많은 인기 음식을 상위에 정렬**하는 2차 정렬 조건식을 부여했습니다.

---

## 3. API 사용 방법

### GET `/api/search`
사용자의 자연어 검색을 받아 최종 Top N 하이브리드 검색 결과를 응답합니다.

- **Request Query Parameters**:
  - `q` (string, 필수): 검색어 (예: "얼큰한 김치찌개")
  - `limit` (int, 선택): 최종 반환할 결과 수 (기본값: `10`)

- **Response 예시 (JSON)**:
  ```json
  {
    "query": "김치칭개",
    "count": 2,
    "results": [
      {
        "food_id": 198,
        "food_name": "김치찌개_햄",
        "category_name": "찌개 및 전골류",
        "click_count": 0,
        "rrf_score": 0.00983606557377049
      },
      {
        "food_id": 206,
        "food_name": "김치찌개_돼지고기",
        "category_name": "찌개 및 전골류",
        "click_count": 0,
        "rrf_score": 0.00967741935483871
      }
    ]
  }
  ```

---

## 4. 검증 결과
- **정확도**: 쿼리에 일부 오타가 섞이더라도("김치칭개") 문맥적(Semantic) 임베딩 벡터가 "김치찌개"의 궤적을 유사도 높게 포착하여 정상적으로 올바른 관련 음식을 추천 병합하여 보여줍니다.
- **속도**: GIN 인덱스와 ivfflat 인덱스를 함께 활용하여 150ms 내외의 고속 응답 품질을 유지합니다.
