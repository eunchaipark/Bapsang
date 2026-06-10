import streamlit as st
import streamlit.components.v1 as components
import os
import requests
from db import get_connection
from dashboard.components.search_box import send_interaction_log

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


def fetch_popular_fallback(limit=20):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT food_id, food_name, category_name, click_count
            FROM foods
            ORDER BY click_count DESC, food_name ASC
            LIMIT %s
        """, (limit,))
        return [
            {
                "food_id": row[0],
                "food_name": row[1],
                "category_name": row[2],
                "score": 0.0,
                "rank": idx + 1
            }
            for idx, row in enumerate(cur.fetchall())
        ]
    except Exception as e:
        print(f"Error fetching fallback: {e}")
        return []
    finally:
        cur.close()
        conn.close()


@st.dialog("음식 상세")
def food_detail_dialog(food_id: int, food_name: str, category_name: str):
    st.markdown(f"### {food_name}")
    st.markdown(f"**카테고리:** {category_name}")
    st.markdown("---")

    naver_url = f"https://map.naver.com/v5/search/{food_name} 맛집"
    google_url = f"https://www.google.com/search?q={food_name} 레시피"

    col1, col2 = st.columns(2)
    with col1:
        st.link_button("🗺️ 맛집 찾기", naver_url, use_container_width=True)
    with col2:
        st.link_button("🍳 레시피 찾기", google_url, use_container_width=True)

    st.markdown("---")
    if st.button("찜하기 ❤️", use_container_width=True, key=f"dialog_like_{food_id}"):
        send_interaction_log(st.session_state.user_id, food_id, category_name, "LIKE")
        st.success("찜 목록에 추가됐어요!")


def render_recommendation_panel():
    components.html("""
    <style>
        body { margin:0; padding:0; background:transparent; }
        .section-title { font-size:1.4rem; font-weight:700; color:#f39c12; border-left:4px solid #e67e22; padding-left:10px; margin:0 0 4px 0; font-family:'Pretendard','Noto Sans KR',sans-serif; }
        .section-desc { color:#a0aec0; font-size:0.88rem; margin:4px 0 0 0; font-family:'Pretendard','Noto Sans KR',sans-serif; }
    </style>
    <p class="section-title">나만을 위한 추천 메뉴</p>
    <p class="section-desc">ALS 배치 알고리즘으로 계산된 개인화 추천 목록입니다. 카드를 클릭해 맛집이나 레시피를 찾아보세요.</p>
    """, height=70, scrolling=False)

    user_id = st.session_state.user_id
    recommendations = []
    is_fallback = False

    try:
        response = requests.get(f"{FASTAPI_URL}/recommendations/{user_id}", timeout=3)
        if response.status_code == 200:
            recommendations = response.json().get("recommendations", [])
        else:
            is_fallback = True
            recommendations = fetch_popular_fallback(20)
    except Exception:
        is_fallback = True
        recommendations = fetch_popular_fallback(20)

    col_title, col_btn = st.columns([8, 2])
    with col_btn:
        if st.button("새로고침", key="rec_refresh", use_container_width=True):
            st.rerun()

    if is_fallback:
        st.caption("아직 개인 추천 데이터가 없어 인기 메뉴를 보여드립니다. 클릭/찜을 쌓으면 개인 맞춤으로 전환됩니다.")

    if not recommendations:
        st.info("표시할 추천 음식이 없습니다.")
        return

    # 가로 스크롤 카드 HTML
    cards_html = '<div style="display:flex; gap:12px; overflow-x:auto; padding:8px 0 16px 0; scrollbar-width:thin; scrollbar-color:#e67e22 #1a1d23;">'
    for rec in recommendations:
        score = rec.get("score", 0.0)
        score_text = f"선호도 {score:.2f}" if score > 0 else "인기순"
        cards_html += f"""
        <div style="
            min-width:160px; max-width:160px;
            background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;
            padding:16px 14px;
            cursor:pointer;
            transition:border-color 0.2s;
            flex-shrink:0;
        "
        onmouseover="this.style.borderColor='rgba(230,126,34,0.5)'"
        onmouseout="this.style.borderColor='rgba(255,255,255,0.07)'"
        >
            <div style="font-weight:700; color:#e67e22; font-size:0.8rem; margin-bottom:6px;">#{rec.get('rank', '')}</div>
            <div style="font-weight:600; color:#f7fafc; font-size:0.95rem; margin-bottom:6px; line-height:1.3;">{rec.get('food_name', '')}</div>
            <div style="background:rgba(230,126,34,0.15); color:#e67e22; padding:2px 8px; border-radius:6px; font-size:0.72rem; font-weight:600; display:inline-block; margin-bottom:8px;">{rec.get('category_name', '')}</div>
            <div style="color:#718096; font-size:0.75rem;">{score_text}</div>
        </div>
        """
    cards_html += '</div>'
    components.html(f"""
    <style>
        body {{ margin:0; padding:0; background:transparent; }}
        ::-webkit-scrollbar {{ height:4px; }}
        ::-webkit-scrollbar-track {{ background:#1a1d23; }}
        ::-webkit-scrollbar-thumb {{ background:#e67e22; border-radius:4px; }}
    </style>
    {cards_html}
    """, height=200, scrolling=False)

    # 카드 클릭 버튼 (Streamlit 이벤트용)
    cols = st.columns(min(len(recommendations), 5))
    for idx, rec in enumerate(recommendations[:10]):
        food_id = rec.get("food_id")
        food_name = rec.get("food_name")
        category_name = rec.get("category_name")
        col_idx = idx % 5
        with cols[col_idx]:
            if st.button(food_name[:6], key=f"r_open_{food_id}_{idx}", use_container_width=True):
                send_interaction_log(user_id, food_id, category_name, "CLICK")
                food_detail_dialog(food_id, food_name, category_name)