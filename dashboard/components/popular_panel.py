import streamlit as st
import streamlit.components.v1 as components
from db import get_connection
from dashboard.components.search_box import send_interaction_log
from dashboard.auth.login import get_all_categories


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
    if st.button("찜하기 ❤️", use_container_width=True, key=f"dialog_like_pop_{food_id}"):
        send_interaction_log(st.session_state.user_id, food_id, category_name, "LIKE")
        st.success("찜 목록에 추가됐어요!")


def fetch_popular_overall(limit=10):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT food_id, food_name, category_name, click_count
            FROM foods
            ORDER BY click_count DESC, food_name ASC
            LIMIT %s
        """, (limit,))
        return cur.fetchall()
    except Exception as e:
        print(f"Error fetching popular: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def fetch_popular_by_category(category_name: str, limit=10):
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT food_id, food_name, category_name, click_count
            FROM foods
            WHERE category_name = %s
            ORDER BY click_count DESC, food_name ASC
            LIMIT %s
        """, (category_name, limit))
        return cur.fetchall()
    except Exception as e:
        print(f"Error fetching popular by category: {e}")
        return []
    finally:
        cur.close()
        conn.close()


def render_cards(foods: list, key_prefix: str):
    user_id = st.session_state.user_id

    if not foods:
        st.info("데이터가 없습니다.")
        return

    # 가로 스크롤 카드 HTML
    cards_html = '<div style="display:flex; gap:12px; overflow-x:auto; padding:8px 0 16px 0; scrollbar-width:thin; scrollbar-color:#e67e22 #1a1d23;">'
    for idx, row in enumerate(foods):
        food_id, food_name, category_name, click_count = row
        cards_html += f"""
        <div style="
            min-width:160px; max-width:160px;
            background:rgba(255,255,255,0.03);
            border:1px solid rgba(255,255,255,0.07);
            border-radius:12px;
            padding:16px 14px;
            cursor:pointer;
            flex-shrink:0;
        "
        onmouseover="this.style.borderColor='rgba(230,126,34,0.5)'"
        onmouseout="this.style.borderColor='rgba(255,255,255,0.07)'"
        >
            <div style="font-weight:700; color:#ff7e5f; font-size:0.8rem; margin-bottom:6px;">#{idx+1}</div>
            <div style="font-weight:600; color:#f7fafc; font-size:0.95rem; margin-bottom:6px; line-height:1.3;">{food_name}</div>
            <div style="background:rgba(230,126,34,0.15); color:#e67e22; padding:2px 8px; border-radius:6px; font-size:0.72rem; font-weight:600; display:inline-block; margin-bottom:8px;">{category_name}</div>
            <div style="color:#718096; font-size:0.75rem;">클릭 {click_count}회</div>
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

    # Streamlit 이벤트 버튼
    cols = st.columns(min(len(foods), 5))
    for idx, row in enumerate(foods):
        food_id, food_name, category_name, click_count = row
        col_idx = idx % 5
        with cols[col_idx]:
            if st.button(food_name[:6], key=f"{key_prefix}_open_{food_id}_{idx}", use_container_width=True):
                send_interaction_log(user_id, food_id, category_name, "CLICK")
                food_detail_dialog(food_id, food_name, category_name)


def render_popular_panel():
    components.html("""
    <style>
        body { margin:0; padding:0; background:transparent; }
        .section-title { font-size:1.4rem; font-weight:700; color:#f39c12; border-left:4px solid #e67e22; padding-left:10px; margin:0 0 4px 0; font-family:'Pretendard','Noto Sans KR',sans-serif; }
        .section-desc { color:#a0aec0; font-size:0.88rem; margin:4px 0 0 0; font-family:'Pretendard','Noto Sans KR',sans-serif; }
    </style>
    <p class="section-title">인기 메뉴 트렌드</p>
    <p class="section-desc">유저들이 가장 많이 클릭하고 찜한 요리들입니다. 카드를 클릭해 맛집이나 레시피를 찾아보세요.</p>
    """, height=70, scrolling=False)

    tab1, tab2 = st.tabs(["전체 인기 Top 10", "카테고리별 탐색"])

    with tab1:
        popular_foods = fetch_popular_overall(10)
        render_cards(popular_foods, key_prefix="p")

    with tab2:
        categories = get_all_categories()
        if not categories:
            st.error("카테고리를 불러올 수 없습니다.")
            return

        selected_category = st.selectbox("카테고리 선택", options=categories, key="popular_cat_select")
        if selected_category:
            cat_foods = fetch_popular_by_category(selected_category, 10)
            render_cards(cat_foods, key_prefix="pc")