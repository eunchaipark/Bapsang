import streamlit as st
import os
import requests

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


def send_interaction_log(user_id: int, food_id: int, category_name: str, action_type: str):
    """
    유저의 클릭/찜 행동 로그를 FastAPI /logs 엔드포인트로 전송합니다.
    """
    try:
        payload = {
            "user_id": user_id,
            "food_id": food_id,
            "category_name": category_name,
            "action_type": action_type
        }
        res = requests.post(f"{FASTAPI_URL}/logs", json=payload, timeout=3)
        if res.status_code == 200:
            st.toast(f"✅ {action_type} 로그 전송 성공! (파이프라인 반영 중)", icon="🚀")
        else:
            st.toast(f"❌ 로그 전송 실패 (상태 코드: {res.status_code})", icon="⚠️")
    except Exception as e:
        st.toast(f"❌ API 서버 연결 실패: {str(e)}", icon="⚠️")

def render_search_box():
    """
    하이브리드 음식 검색창 및 결과를 렌더링합니다.
    """
    st.markdown('<div class="section-title">🔍 하이브리드 음식 검색</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#a0aec0; font-size:0.9rem; margin-top:-10px;">키워드 매칭과 벡터 의미론적 매칭(RRF 결합)으로 최적의 음식을 찾아냅니다.</p>', unsafe_allow_html=True)

    # 검색어 입력
    search_query = st.text_input(
        "음식명, 또는 찾고 싶은 분위기/맛을 설명해 보세요",
        placeholder="예: 얼큰한 김치찌개, 달콤한 초콜릿 케이크, 비 오는 날 찌개",
        key="search_input"
    )

    if search_query:
        try:
            with st.spinner("하이브리드 검색 엔진 탐색 중..."):
                response = requests.get(
                    f"{FASTAPI_URL}/api/search",
                    params={"q": search_query, "limit": 6},
                    timeout=5
                )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    st.info("검색 결과가 없습니다.")
                else:
                    st.markdown(f"**'{search_query}'** 검색 결과 ({data.get('count')}개):")
                    
                    for idx, result in enumerate(results):
                        food_id = result.get("food_id")
                        food_name = result.get("food_name")
                        category_name = result.get("category_name")
                        rrf_score = result.get("rrf_score", 0.0)
                        
                        # 카드 컴포넌트 HTML 구조
                        card_html = f"""
                        <div class="food-card">
                            <div>
                                <span class="food-name">{food_name}</span>
                                <span class="category-badge">{category_name}</span>
                                <span style="font-size:0.8rem; color:#718096; margin-left:10px;">RRF: {rrf_score:.5f}</span>
                            </div>
                        </div>
                        """
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # 액션 버튼들을 한 줄로 나열하기 위해 streamlit columns 사용
                        btn_col1, btn_col2, btn_spacer = st.columns([1, 1.2, 4])
                        with btn_col1:
                            if st.button("🖱️ 클릭", key=f"search_click_{food_id}_{idx}"):
                                send_interaction_log(st.session_state.user_id, food_id, category_name, "CLICK")
                        with btn_col2:
                            if st.button("❤️ 찜하기", key=f"search_like_{food_id}_{idx}"):
                                send_interaction_log(st.session_state.user_id, food_id, category_name, "LIKE")
                        
                        st.write("---")
            else:
                st.error(f"검색 API 실패 (코드: {response.status_code})")
                
        except requests.exceptions.RequestException:
            st.error("🔌 FastAPI API 서버가 실행 중이 아닙니다. Docker 또는 로컬 FastAPI 기동 상태를 확인해 주세요.")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
