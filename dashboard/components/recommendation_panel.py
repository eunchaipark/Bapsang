import streamlit as st
import os
import requests
from db import get_connection
from dashboard.components.search_box import send_interaction_log

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


def fetch_popular_fallback(limit=10):
    """
    ALS 추천 결과가 없을 때 사용되는 폴백 목록으로 전체 인기 순위(click_count 높은 순)를 가져옵니다.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT food_id, food_name, category_name, click_count
            FROM foods
            ORDER BY click_count DESC, food_name ASC
            LIMIT %s
        """, (limit,))
        rows = cur.fetchall()
        return [
            {
                "food_id": row[0],
                "food_name": row[1],
                "category_name": row[2],
                "click_count": row[3],
                "score": 0.0,
                "rank": idx + 1
            }
            for idx, row in enumerate(rows)
        ]
    except Exception as e:
        print(f"Error fetching popular fallback: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def render_recommendation_panel():
    """
    개인화 추천 목록 패널을 렌더링합니다.
    """
    st.markdown('<div class="section-title">⭐ 나만을 위한 추천 메뉴</div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#a0aec0; font-size:0.9rem; margin-top:-10px;">ALS 배치 알고리즘을 통해 계산된 개인 취향 저격 음식 목록입니다.</p>', unsafe_allow_html=True)
    
    user_id = st.session_state.user_id
    recommendations = []
    is_fallback = False
    
    # API 호출을 통한 ALS 추천 리스트 조회
    try:
        response = requests.get(f"{FASTAPI_URL}/recommendations/{user_id}", timeout=3)
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get("recommendations", [])
        elif response.status_code == 404:
            # 404: 추천 결과가 없음 (신규 가입 유저 등) -> 인기순 폴백 작동
            is_fallback = True
            recommendations = fetch_popular_fallback(10)
        else:
            st.warning(f"추천 서버 경고 (코드: {response.status_code}) - 인기 순으로 대체합니다.")
            is_fallback = True
            recommendations = fetch_popular_fallback(10)
            
    except requests.exceptions.RequestException:
        # API 서버가 다운된 경우도 인기순 폴백으로 안전하게 대응
        is_fallback = True
        recommendations = fetch_popular_fallback(10)
        
    # 새로고침 버튼 배치
    ref_col1, ref_col2 = st.columns([8, 2])
    with ref_col2:
        if st.button("🔄 새로고침", key="rec_refresh"):
            st.rerun()

    # 결과 출력
    if not recommendations:
        st.info("표시할 추천 음식이 없습니다.")
    else:
        if is_fallback:
            st.caption("ℹ️ 아직 개인 추천 데이터가 완성되지 않아 인기 메뉴(click_count 순)를 추천 중입니다. (배치 러너가 갱신되면 개인 맞춤으로 전환됩니다)")
            
        for idx, rec in enumerate(recommendations):
            food_id = rec.get("food_id")
            food_name = rec.get("food_name")
            category_name = rec.get("category_name")
            score = rec.get("score", 0.0)
            rank = rec.get("rank", idx + 1)
            
            # 카드 컴포넌트 HTML 구조
            score_text = f"예측 선호도: {score:.3f}" if score > 0 else ""
            card_html = f"""
            <div class="food-card">
                <div>
                    <span style="font-weight: 700; color: #e67e22; margin-right: 8px;">#{rank}</span>
                    <span class="food-name">{food_name}</span>
                    <span class="category-badge">{category_name}</span>
                    <span style="font-size:0.8rem; color:#718096; margin-left:10px;">{score_text}</span>
                </div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            btn_col1, btn_col2, btn_spacer = st.columns([1, 1.2, 4])
            with btn_col1:
                if st.button("🖱️ 클릭", key=f"rec_click_{food_id}_{idx}"):
                    send_interaction_log(user_id, food_id, category_name, "CLICK")
            with btn_col2:
                if st.button("❤️ 찜하기", key=f"rec_like_{food_id}_{idx}"):
                    send_interaction_log(user_id, food_id, category_name, "LIKE")
            
            st.write("---")
