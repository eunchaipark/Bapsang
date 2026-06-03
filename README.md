
# 프로젝트 개요서 v5.4
## 실시간 데이터 파이프라인 기반 음식 추천 & 검색 대시보드

- 팀 규모: 4명
- 기간: 4주
- Core 기능: A (배치 추천) + B (실시간 스트리밍) + C (하이브리드 검색)
- Extension 기능: D (RAG 챗봇) — 시간 여유 시만 진행
- 데이터셋: 전국통합식품영양성분정보(음식) 표준데이터 (공공데이터포털, 식품의약품안전처)
- 아키텍처: 기능 중심 레이어드 아키텍처 (Feature-based Layered Architecture)

---

## 1. 프로젝트 정의

Apache Spark(분산 처리)와 FastAPI(비동기 백엔드)를 결합하여, 유저의 장기 취향(배치)과 실시간 행동 로그(스트리밍)를 동시에 반영하는 음식 추천 파이프라인을 구현합니다.

데이터는 식품의약품안전처에서 제공하는 공공데이터(전국통합식품영양성분정보 음식 표준데이터, data.go.kr/data/15100070)를 활용합니다. 한국 음식 15,568개의 식품명과 대분류(밥류/면류/국류 등 25개)를 기반으로 추천과 검색을 수행합니다.

프론트엔드는 Streamlit으로 경량화하여 데이터 파이프라인 완성도와 Locust 성능 검증에 집중합니다. 로그인 기능을 붙여 테스트 계정 몇 개로 직접 클릭/찜 행동을 발생시키며, 부하 테스트 시에는 Python 로그 시뮬레이터로 대량 로그를 생성합니다.

> 데이터 수집 리스크 Zero: 공공데이터포털에서 CSV로 직접 다운로드. 외부 크롤링 없음.

---

## 2. 데이터셋 상세

### 2.1 원본 데이터 정보

- 파일명: 전국통합식품영양성분정보_음식_표준데이터.csv
- 인코딩: cp949
- 원본 행 수: 19,495개
- 원본 컬럼 수: 52개

### 2.2 컬럼별 사용 여부 판단

| 컬럼명 | 판단 | 이유 |
|---|---|---|
| 식품코드 | ✅ 사용 | food_code (PK 역할) |
| 식품명 | ✅ 사용 | Full-Text 검색 + 벡터 임베딩 대상 |
| 식품대분류코드 | ✅ 사용 | 카테고리 코드 |
| 식품대분류명 | ✅ 사용 | 카테고리명 (밥류/면류 등 25개) |
| 식품중분류코드/명 | ❌ 버림 | 85% 이상 "해당없음" |
| 식품소분류코드/명 | ❌ 버림 | 99% 이상 "해당없음" |
| 식품세분류코드/명 | ❌ 버림 | 99% 이상 "해당없음" |
| 에너지(kcal) | ❌ 버림 | 영양성분 미사용 |
| 단백질(g) | ❌ 버림 | null 다수, 영양성분 미사용 |
| 지방(g) | ❌ 버림 | null 68%, 영양성분 미사용 |
| 탄수화물(g) | ❌ 버림 | null 65%, 영양성분 미사용 |
| 나트륨(mg) | ❌ 버림 | 영양성분 미사용 |
| 수분/회분/당류/식이섬유 등 | ❌ 버림 | null 65~94%, 영양성분 미사용 |
| 비타민류 전체 | ❌ 버림 | null 78~86% |
| 포화지방산/트랜스지방산 | ❌ 버림 | null 다수 |
| 1인(회)분량 참고량 | ❌ 버림 | null 100% |
| 출처코드/명 | ❌ 버림 | 파이프라인 불필요 |
| 업체명 | ❌ 버림 | 파이프라인 불필요 |
| 데이터생성방법/일자 등 | ❌ 버림 | 파이프라인 불필요 |
| 제공기관코드/명 | ❌ 버림 | 파이프라인 불필요 |
| 데이터구분코드/명 | ❌ 버림 | 파이프라인 불필요 |
| 식품기원코드/명 | ❌ 버림 | 파이프라인 불필요 |
| 대표식품코드/명 | ❌ 버림 | 파이프라인 불필요 |
| 영양성분함량기준량 | ❌ 버림 | 파이프라인 불필요 |
| 식품중량 | ❌ 버림 | 파이프라인 불필요 |

### 2.3 전처리 결과

전처리 단계에서 아래 작업을 수행합니다. **전처리와 임베딩은 Google Colab에서 1회 실행 후 CSV로 저장합니다.**

1. 필요한 컬럼 4개만 추출 (식품코드, 식품명, 식품대분류코드, 식품대분류명)
2. 식품명 기준 중복 제거
3. search_text 컬럼 생성 (식품명 + 대분류명 합치기)
4. click_count 초기값 0으로 설정
5. embedding 컬럼 생성 (paraphrase-multilingual-MiniLM-L12-v2로 search_text 임베딩, float32, 384차원)
6. foods_processed.csv로 저장 → `data/processed/` 에 배치

> **모델 일관성 필수**: Colab 전처리 시 임베딩 모델과 FastAPI 검색 시 쿼리 임베딩 모델이 `paraphrase-multilingual-MiniLM-L12-v2`로 동일해야 코사인 유사도 비교가 의미 있습니다.

전처리 후 최종 데이터:
- 총 음식 수: 15,568개
- 대분류 수: 25개
- 주요 대분류 분포: 빵 및 과자류 약 8,600개, 음료 및 차류 약 5,776개, 국 및 탕류 506개, 생채무침류 501개, 볶음류 495개, 밥류 421개, 면 및 만두류 341개, 찌개 및 전골류 339개 등

> **데이터 편향 인지**: 빵/과자류(55%)와 음료/차류(37%)가 전체의 92%를 차지합니다. 클릭 로그와 ALS 추천 결과가 이 두 카테고리로 쏠릴 수 있으나, 현재 스코프에서는 허용합니다. 파이프라인 동작 증명이 우선이며, 카테고리 다양성 보정(추천 결과 카테고리별 상한선)은 Phase 2 이후 고려합니다.

### 2.4 유저 데이터 생성 방식

가상 유저 대량 생성 없이, 로그인 기능을 통해 테스트 계정을 직접 생성하여 운영합니다.

- 회원가입 시 카테고리 2~3개 선택 → `user_category_weights` 초기값 즉시 삽입 (콜드스타트 해결)
- 이후 클릭/찜 행동이 쌓이면 Spark Streaming이 가중치를 누적 갱신
- ALS 학습 입력: `user_click_logs` (CLICK=1점, LIKE=5점 암묵적 평점 변환)
- `ratings` 테이블 없음 — 명시적 평점 불필요, 행동 로그가 평점을 대체

### 2.5 DB 초기 적재 방식

`docker-compose up` 시 자동으로 foods 데이터가 적재됩니다.

```
docker-compose up --build
        ↓
postgresql 컨테이너 기동 → init.sql 실행 (스키마 생성)
        ↓
data_loader 컨테이너 기동 → db/load_foods.py 실행
        ↓
data/processed/foods_processed.csv → foods 테이블 INSERT (15,568개)
        ↓
ivfflat 인덱스 자동 생성 후 컨테이너 종료
```

> **주의**: `docker-compose down -v` 로 볼륨까지 삭제해야 재적재 시 `init.sql`이 재실행됩니다. `-v` 없이 내리면 기존 데이터가 유지됩니다.

---

## 3. 개발 범위 (Scope)

### Phase 1 — Core (1~3주차, 필수)

이 세 가지가 완성되면 프로젝트는 성공입니다. A/B/C를 각각 1명씩 담당하여 독립 개발합니다.

- 기능 A (1명 담당): Spark MLlib ALS 배치 추천 → recommendations 테이블 적재 → Streamlit 서빙
- 기능 B (1명 담당): FastAPI 로그 수집 + Spark Streaming 카테고리 가중치 갱신
- 기능 C (1명 담당): PostgreSQL Full-Text + pgvector 하이브리드 검색
- 공통 (1명 담당): Docker 환경, DB 스키마, 전처리, Streamlit UI (로그인/회원가입 포함), 로그 시뮬레이터 (Locust 부하 테스트용)

### Phase 2 — Extension (4주차, 조기 완성 시만 진행)

- 기능 D: A/B/C 데이터를 LLM 프롬프트에 주입 → Streamlit 챗봇 UI (st.chat_message)로 자연어 추천

> RAG(기능 D)는 챗봇 인터페이스가 반드시 있어야 의미가 있습니다. C 기능은 챗봇 없이 단독으로 완결된 기능이며 D는 그 위에 자연어 설명 레이어를 추가하는 것입니다. Phase 1 미완성 시 과감히 생략합니다.

---

## 4. 핵심 기능 상세

### 기능 A — 개인화 배치 추천 (Batch Loop)
담당: 1명 / 핵심 기술: Spark MLlib ALS

**역할 범위**

ratings 테이블을 읽어 Spark MLlib ALS 알고리즘으로 유저-음식 잠재 요인 행렬을 분해합니다. "이 유저가 아직 접하지 않은 음식 중 좋아할 확률이 높은 것"을 계산하여 유저별 Top 20을 recommendations 테이블에 주기적으로 적재합니다.

**읽는 테이블 및 컬럼**

user_click_logs 테이블:
- user_id: ALS 유저 행렬 구성
- food_id: ALS 아이템 행렬 구성
- action_type: CLICK=1, LIKE=5로 암묵적 평점 변환 후 ALS 학습 입력값

**쓰는 테이블 및 컬럼**

recommendations 테이블:
- user_id: 유저 ID
- food_id: 추천 음식 ID
- score: ALS 예측 점수
- rank: 유저별 순위 (1~20)
- batch_run_at: 배치 실행 시각

foods 테이블:
- click_count: 배치 실행 시 전체 클릭 수 집계값으로 갱신

**신규 유저 처리**

recommendations에 해당 유저 행이 없으면 Streamlit이 foods.click_count 높은 순으로 자동 fallback 표시합니다. 기능 A는 이 fallback 로직을 구현하지 않습니다.

- 기술: Spark MLlib ALS (local[2], driver.memory 2g), PostgreSQL, Python
- ALS 입력 변환: `action_type` 컬럼 기준 CLICK → 1, LIKE → 5 매핑 후 학습

---

### 기능 B — 실시간 행동 로그 수집 & 카테고리 가중치 갱신 (Streaming Loop)
담당: 1명 / 핵심 기술: FastAPI + Spark Structured Streaming

**역할 범위**

두 가지 독립 작업으로 구성됩니다.

B-1. 로그 수집 (FastAPI)
유저가 Streamlit 화면에서 음식을 클릭하거나 찜할 때 Streamlit이 FastAPI 엔드포인트를 호출합니다. FastAPI는 해당 이벤트를 user_click_logs 테이블에 비동기 INSERT합니다.

action_type은 CLICK과 LIKE 두 가지만 존재합니다. VIEW는 한 화면에 여러 음식이 동시에 노출되므로 명시적 행동으로 볼 수 없어 제외합니다.

B-2. 가중치 집계 (Spark Streaming)
Spark Structured Streaming이 20초 마이크로배치 단위로 user_click_logs의 신규 로그를 읽어 유저별 카테고리 클릭 횟수를 집계합니다. 집계 결과를 user_category_weights 테이블에 Upsert합니다.

화면은 유저가 새로고침할 때만 갱신되어 UX를 해치지 않습니다.

> **⚠️ Spark Streaming JDBC 소스 특성 및 오프셋 관리**
>
> Spark Structured Streaming의 JDBC 소스는 Kafka와 달리 **자체 오프셋을 관리하지 않습니다.** 내부적으로는 20초마다 `SELECT ... WHERE log_id > last_offset` 형태의 폴링 쿼리를 실행하는 마이크로배치 방식입니다.
>
> 따라서 오프셋(마지막으로 읽은 log_id)을 직접 관리해야 합니다. 구현 방식은 다음과 같습니다.
>
> **streaming_offsets 테이블 (오프셋 전용, 1행 고정)**
> ```sql
> CREATE TABLE streaming_offsets (
>     id         INT PRIMARY KEY DEFAULT 1,
>     last_log_id BIGINT NOT NULL DEFAULT 0,
>     updated_at  TIMESTAMP(3) DEFAULT NOW()
> );
> INSERT INTO streaming_offsets VALUES (1, 0, NOW());
> ```
>
> **Spark 마이크로배치 루프 (의사 코드)**
> ```python
> while True:
>     # 1. 현재 오프셋 읽기
>     last_id = read_offset_from_db()  # streaming_offsets.last_log_id
>
>     # 2. 신규 로그만 조회
>     df = spark.read.jdbc(
>         query=f"SELECT * FROM user_click_logs WHERE log_id > {last_id}",
>         ...
>     )
>
>     if df.count() == 0:
>         sleep(20)
>         continue
>
>     # 3. 카테고리별 클릭 수 집계
>     agg = df.groupBy("user_id", "category_name").count()
>
>     # 4. user_category_weights Upsert
>     upsert_weights(agg)
>
>     # 5. 오프셋 갱신 (처리한 최대 log_id로 업데이트)
>     new_offset = df.agg({"log_id": "max"}).collect()[0][0]
>     update_offset_in_db(new_offset)  # streaming_offsets 갱신
>
>     sleep(20)
> ```
>
> 이 패턴은 **중복 처리 없음** (log_id > last_id 조건), **누락 없음** (오프셋을 처리 완료 후 갱신)을 보장합니다. Spark 재시작 시에도 streaming_offsets에서 오프셋을 복구하므로 데이터 유실이 없습니다.

**쓰는 테이블 및 컬럼 (FastAPI)**

user_click_logs 테이블:
- user_id: 유저 ID
- food_id: 클릭한 음식 ID
- action_type: CLICK 또는 LIKE
- category_name: 클릭한 음식의 대분류명 (Streaming 집계용 비정규화, foods 테이블 JOIN 없이 바로 집계 가능)
- logged_at: 이벤트 시각 (밀리초 단위)

**읽는 테이블 및 컬럼 (Spark Streaming)**

user_click_logs 테이블:
- log_id: 오프셋 기준 (last_log_id 초과분만 읽기)
- user_id: 집계 기준
- category_name: 카테고리별 클릭 수 집계
- logged_at: 20초 윈도우 기준

streaming_offsets 테이블:
- last_log_id: 마지막으로 처리한 log_id (마이크로배치 시작 시 읽고, 종료 시 갱신)

**쓰는 테이블 및 컬럼 (Spark Streaming)**

user_category_weights 테이블:
- user_id: 유저 ID
- category_name: 카테고리명
- weight: 클릭 횟수 기반 누적 가중치 (ON CONFLICT DO UPDATE SET weight = weight + 1)
- updated_at: 마지막 갱신 시각

기능 B는 recommendations 테이블을 건드리지 않습니다. user_category_weights는 다음 번 기능 A 배치 실행 시 보정 참고 데이터로 활용될 예정이며, 구체적인 반영 로직(ALS 입력 보정 vs 결과 reranking)은 Phase 1 완성 후 별도 설계합니다.

- 기술: FastAPI (비동기), Spark Structured Streaming (local[2], driver.memory 2g), PostgreSQL

---

### 기능 C — 하이브리드 음식 검색
담당: 1명 / 핵심 기술: pgvector + PostgreSQL Full-Text

**역할 범위**

두 가지 검색 방식을 결합하여 검색창 하나로 키워드 검색과 문맥 검색을 동시에 처리합니다. 모든 검색은 foods 테이블 하나에서 처리됩니다. 별도 벡터 DB 없음.

C-1. Full-Text 검색 (PostgreSQL to_tsvector)
정확한 키워드 입력 시 빠르게 매칭합니다.
```sql
SELECT food_id, food_name, category_name
FROM foods
WHERE to_tsvector('simple', food_name) @@ to_tsquery('김치찌개')
LIMIT 20;
```

C-2. 벡터 유사도 검색 (pgvector)
감정/문맥 쿼리를 의미론적으로 처리합니다.
```sql
SELECT food_id, food_name, category_name,
       embedding <=> '[쿼리 벡터]' AS distance
FROM foods
ORDER BY distance
LIMIT 20;
```

사용자 쿼리 임베딩 처리:
- 사용자 입력 1개를 multilingual-MiniLM으로 벡터 변환 (50~100ms)
- foods.embedding 컬럼과 코사인 유사도 계산 (10~50ms)
- 총 검색 시간 약 150ms 이하

C-3. 결과 병합
Full-Text 결과 60% + 벡터 결과 40% 가중 결합 후 최종 Top 10 반환합니다.

**읽는 테이블 및 컬럼**

foods 테이블:
- food_id: 결과 식별
- food_name: Full-Text 검색 대상 (to_tsvector 인덱스)
- category_name: 결과 표시용
- embedding: pgvector 코사인 유사도 검색 대상 (vector(384))
- click_count: 동점 시 정렬 기준

기능 C는 user_click_logs, recommendations, user_category_weights 테이블을 전혀 건드리지 않습니다. 추천과 완전히 독립된 기능입니다.

- 기술: FastAPI, PostgreSQL Full-Text (to_tsvector, GIN 인덱스), pgvector (ivfflat 인덱스, embedding <=> query_vec), multilingual-MiniLM-L12-v2 (로컬 무료 모델)

---

## 5. 기능 간 역할 분리 요약

| | 기능 A | 기능 B | 기능 C |
|--|--|--|--|
| 담당 기술 | Spark ALS | FastAPI + Spark Streaming | pgvector + Full-Text |
| 입력 소스 | user_click_logs (암묵적 평점) | 유저 클릭 이벤트 | 검색 쿼리 텍스트 |
| 출력 결과 | recommendations | user_category_weights | 검색 결과 Top 10 |
| 실행 주기 | 주기적 배치 | 실시간 (20초) | 요청 시 즉시 |
| 읽는 테이블 | user_click_logs | user_click_logs | foods |
| 쓰는 테이블 | recommendations, foods.click_count | user_click_logs, user_category_weights | 없음 (읽기 전용) |
| 연관성 | B 가중치를 다음 배치에 반영 | A 배치의 보조 데이터 생성 | A/B와 완전 독립 |

---

## 6. 대시보드 화면 구성 (Streamlit)

```
┌─────────────────────────────────────────────┐
│  검색창 (한국어 키워드 or 문맥 쿼리 입력)     │  ← C기능
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  나의 추천 Top 20                             │  ← A기능
│  - ALS 배치 결과 반영                         │
│  - 신규 유저 → click_count 인기순 fallback    │
│  - 새로고침 버튼 클릭 시 갱신                 │
└─────────────────────────────────────────────┘

┌─────────────────┬───────────────┬────────────┐
│  인기 Top 10    │  카테고리별   │  빠른 음식  │
│  click_count 순 │  밥류/면류/   │  간편식류  │
│  (항상 표시)    │  국류/찌개류  │  필터       │
└─────────────────┴───────────────┴────────────┘
```

### 콜드스타트 → 개인화 전환 흐름

1. 회원가입 → 카테고리 2~3개 선택 → `user_category_weights` 초기값 삽입
2. 첫 접속 → recommendations 행 없음 → click_count 인기순 표시
3. 클릭/찜 시작 → user_click_logs에 카테고리 기록 (FastAPI)
4. 20초마다 → Spark Streaming이 user_category_weights 갱신
5. ALS 배치 실행 → recommendations 갱신 (개인화 추천으로 전환)
6. 유저가 새로고침 → 최신 recommendations 반영

---

## 7. DB 설계 (PostgreSQL + pgvector)

### 테이블 목록 (총 6개)

| 테이블명 | 데이터 출처 | 역할 | 관련 기능 |
|---|---|---|---|
| foods | 공공데이터 전처리 | 음식 정보 + 벡터 임베딩 | A, C |
| users | 회원가입으로 생성 | 로그인 유저 | A, B |
| user_click_logs | 유저 실시간 행동 | Streaming 입력 + ALS 학습 입력 | A, B |
| streaming_offsets | 초기화 스크립트 생성 (1행 고정) | Spark 마이크로배치 오프셋 관리 | B |
| user_category_weights | Spark Streaming 출력 | 실시간 카테고리 가중치 | B → A |
| recommendations | Spark ALS 출력 | 최종 추천 결과 | A |

### foods 테이블 컬럼 상세

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| food_id | SERIAL | PK | 음식 고유 ID |
| food_code | VARCHAR(20) | UNIQUE, NOT NULL | 공공데이터 원본 식품코드 |
| food_name | VARCHAR(200) | NOT NULL | 식품명 (Full-Text 검색 대상) |
| category_code | INT | NOT NULL | 식품대분류코드 |
| category_name | VARCHAR(50) | NOT NULL | 식품대분류명 (25개) |
| click_count | INT | DEFAULT 0 | 전체 클릭 수 (콜드스타트 인기순 정렬용) |
| search_text | TEXT | NULL | food_name + category_name 합친 텍스트 |
| embedding | vector(384) | NULL | multilingual-MiniLM 벡터 (pgvector) |
| created_at | TIMESTAMP | DEFAULT NOW() | 적재 시각 |

- CREATE EXTENSION vector
- CREATE INDEX ON foods USING ivfflat (embedding vector_cosine_ops) — 벡터 검색 (embedding 적재 완료 후 생성)
- CREATE INDEX ON foods USING GIN (to_tsvector('simple', food_name)) — Full-Text
- INDEX(category_code, click_count DESC) — 카테고리별 인기순

### users 테이블 컬럼 상세

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| user_id | SERIAL | PK | 유저 고유 ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 유저명 |
| password | VARCHAR(255) | NOT NULL | 비밀번호 (해시 저장) |
| created_at | TIMESTAMP | DEFAULT NOW() | 가입 시각 |

### user_click_logs 테이블 컬럼 상세

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| log_id | BIGSERIAL | PK | 로그 고유 ID |
| user_id | INT | FK → users.user_id | 유저 ID |
| food_id | INT | FK → foods.food_id | 음식 ID |
| action_type | VARCHAR(10) | NOT NULL | CLICK 또는 LIKE |
| category_name | VARCHAR(50) | NOT NULL | 클릭 음식 대분류명 (비정규화) |
| logged_at | TIMESTAMP(3) | DEFAULT NOW() | 이벤트 시각 (밀리초) |

인덱스:
- INDEX(user_id, logged_at) — Streaming 20초 윈도우 쿼리 최적화
- INDEX(log_id) — Spark 오프셋 폴링 쿼리 (`WHERE log_id > last_id`) 최적화 (BIGSERIAL PK이므로 자동 생성됨)

### streaming_offsets 테이블 컬럼 상세

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| id | INT | PK DEFAULT 1 | 항상 1행만 존재 |
| last_log_id | BIGINT | NOT NULL DEFAULT 0 | 마지막으로 처리 완료한 log_id |
| updated_at | TIMESTAMP(3) | DEFAULT NOW() | 오프셋 갱신 시각 |

초기값: `INSERT INTO streaming_offsets VALUES (1, 0, NOW());`
갱신 패턴: `UPDATE streaming_offsets SET last_log_id = ?, updated_at = NOW() WHERE id = 1;`

### user_category_weights 테이블 컬럼 상세

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| id | BIGSERIAL | PK | 고유 ID |
| user_id | INT | FK → users.user_id | 유저 ID |
| category_name | VARCHAR(50) | NOT NULL | 카테고리명 |
| weight | FLOAT | DEFAULT 0.0 | 클릭 횟수 기반 누적 가중치 |
| updated_at | TIMESTAMP(3) | DEFAULT NOW() | 마지막 갱신 시각 |

인덱스:
- UNIQUE(user_id, category_name) — Upsert 중복 방지
- Upsert 패턴: INSERT ... ON CONFLICT (user_id, category_name) DO UPDATE SET weight = weight + 1

### recommendations 테이블 컬럼 상세

| 컬럼명 | 타입 | 제약조건 | 설명 |
|---|---|---|---|
| rec_id | BIGSERIAL | PK | 추천 레코드 ID |
| user_id | INT | FK → users.user_id | 유저 ID |
| food_id | INT | FK → foods.food_id | 추천 음식 ID |
| score | FLOAT | NOT NULL | ALS 예측 점수 |
| rank | INT | NOT NULL | 유저별 순위 (1~20) |
| batch_run_at | TIMESTAMP | NOT NULL | 배치 실행 시각 |

인덱스:
- INDEX(user_id, rank) — 메인 화면 Top 20 조회 최적화
- INDEX(user_id, batch_run_at DESC) — 최신 배치 기준 SELECT 최적화

배치 갱신 패턴 (무중단):
```
1. 새 배치 결과 INSERT (batch_run_at = 현재 시각)
2. Streamlit은 MAX(batch_run_at) 기준으로 항상 최신 배치만 SELECT
3. INSERT 완료 후 이전 batch_run_at 데이터 DELETE
```
→ DELETE + INSERT 순서였던 기존 방식 대비, Streamlit이 빈 결과를 읽는 타이밍 문제 없음

---

## 8. 기술 스택 & 선택 근거

| 기술 | 상태 | 역할 | 선택 근거 |
|---|---|---|---|
| FastAPI | 확정 | 비동기 API 서버 | 비동기 이벤트 루프로 대량 클릭 로그 병목 없이 수집 |
| Spark Streaming | 확정 | 실시간 카테고리 가중치 연산 | RDB 직접 집계 시 부하 폭발 → In-Memory 분산 처리. local[2] 모드로 경량화 |
| Spark MLlib | 확정 | ALS 배치 추천 | 유저-음식 평점 행렬 ALS 분산 연산. local[2] 모드로 경량화 |
| APScheduler | 확정 | 배치 스케줄러 | batch_runner.py 내부에서 1시간 주기 실행. 별도 컨테이너/cron 불필요 |
| PostgreSQL + pgvector | 확정 | 정형 데이터 + 벡터 검색 통합 | 단일 DB로 Full-Text + 벡터 유사도 검색 동시 처리. 별도 벡터 DB 컨테이너 불필요 |
| multilingual-MiniLM | 확정 | 다국어 텍스트 임베딩 | 한국어 쿼리 → 한국어 데이터 직접 코사인 유사도 매칭. 로컬 무료 모델, 인터넷 불필요. 모델명: paraphrase-multilingual-MiniLM-L12-v2 |
| Streamlit | 확정 | 경량 UI | 프론트 공수 제로화. 4인 팀이 파이프라인에만 집중 가능 |
| Docker | 확정 | 환경 통일 & 배포 | 팀원 환경 차이 제거. 4개 컨테이너로 재현 가능한 환경 보장 |
| Redis | 보류 | 선택적 캐싱 | B 파이프라인 병목 발생 시 투입. 처음부터 포함하지 않음 |

---

## 9. Docker 구성 (총 5개 컨테이너)

```
docker-compose.yml
├── postgresql    ankane/pgvector:latest         포트 5432
├── data_loader   python:3.11-slim 기반 빌드     1회 실행 후 종료 (foods 적재)
├── fastapi       python:3.11-slim 기반 빌드     포트 8000
├── spark         apache/spark:3.5.1-python3     포트 4040 (Spark UI)
└── streamlit     python:3.11-slim 기반 빌드     포트 8501
```

Dockerfile 및 requirements는 `docker/` 폴더에 통합 관리:
```
docker/
├── Dockerfile.fastapi
├── Dockerfile.dashboard
├── Dockerfile.spark
├── requirements.fastapi.txt
├── requirements.dashboard.txt
└── requirements.spark.txt
```

Spark 설정:
```python
spark = SparkSession.builder \
    .master("local[2]") \
    .appName("Bapsang") \
    .config("spark.driver.memory", "2g") \
    .config("spark.sql.shuffle.partitions", "4") \
    .getOrCreate()
```

배치 스케줄러 (APScheduler):
```python
# batch_recommendation/batch_runner.py
from apscheduler.schedulers.blocking import BlockingScheduler

scheduler = BlockingScheduler()

@scheduler.scheduled_job('interval', hours=1)
def run_batch():
    # ALS 학습 → recommendations 갱신

scheduler.start()
```

Spark 컨테이너 실행 구조:
```
category_weight_stream.py  (백그라운드, 20초 마이크로배치)
batch_runner.py            (포그라운드, APScheduler 1시간 주기)
```

---

## 10. 4주 로드맵

| 1주차 | 2주차 | 3주차 | 4주차 |
|---|---|---|---|
| Docker 환경 세팅 완료 | 기능 A — ALS 배치 | 기능 B — Streaming | Locust 부하 테스트 |
| DB 스키마 확정 | Spark MLlib 연동 | 기능 C — 검색 엔진 | 성능 지표 측정 |
| 공공데이터 전처리 | PostgreSQL 적재 | Full-Text + 벡터 결합 | 문서화 & 발표 준비 |
| 로그인/회원가입 UI | Streamlit 메인 화면 | FastAPI 엔드포인트 완성 | 기능 D (여유 시) |
| 임베딩 전처리 (foods.embedding 생성) | | | |

> 주의: 1주차에 임베딩 전처리를 확보하지 못하면 C가 2주차에 막힙니다. 킥오프 직후 최우선 착수 필요.

---

## 11. 최종 검증 목표

> "우리 대시보드는 초당 N건의 클릭 로그가 발생해도 응답 지연이 Xms 이하로 유지된다"

Locust 부하 테스트를 통해 정량 수치를 포트폴리오에 기재합니다.

- 기능 B: Spark Streaming 20초 마이크로배치 → PostgreSQL Upsert 지연 측정
- 기능 C: 하이브리드 검색 응답시간 vs Full-Text 단독 비교 (목표 150ms 이하)
- 기능 A: ALS 배치 실행 시간 측정 (유저 500명 × 음식 15,568개 기준)

현업(넷플릭스/유튜브)의 2-Stage 추천 구조(배치 후보군 추출 → 실시간 스코어링)를 충실히 구현하여 기술적 타당성을 증명합니다. 기능 D(RAG 챗봇)는 정량 성능 지표보다 구현 완성도로 평가되므로 Locust 측정 대상에서 제외합니다.

---

