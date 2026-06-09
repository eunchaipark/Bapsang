import streamlit as st
from db import get_connection
from dashboard.components.search_box import send_interaction_log
from dashboard.auth.login import get_all_categories

def fetch_popular_overall(limit=10):
    """
    전체 클릭 수 기준 인기 음식 Top 10을 가져옵니다.
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
        return cur.fetchall()
    except Exception as e:
        print(f"Error fetching popular overall: {e}")
        return []
    finally:
        cur.close()
        conn.close()

def fetch_popular_by_category(category_name: str, limit=10):
    """
    특정 카테고리 내 클릭 수 기준 인기 음식을 가져옵니다.
    """
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

def render_popular_panel():
    """
    인기 메뉴 및 카테고리별 인기 랭킹 패널을 렌더링합니다.
    """
    st.markdown('<div class="section-title">🔥 인기 메뉴 트렌드</div>', unsafe_allow_html=True)
    
    # 탭으로 분리하여 깔끔하게 제공
    tab1, tab2 = st.tabs(["전체 실시간 인기 Top 10", "카테고리별 인기 탐색"])
    
    user_id = st.session_state.user_id
    
    with tab1:
        st.markdown('<p style="color:#a0aec0; font-size:0.9rem;">유저들이 실시간으로 가장 많이 클릭하고 찜한 요리들입니다.</p>', unsafe_allow_html=True)
        popular_foods = fetch_popular_overall(10)
        
        if not popular_foods:
            st.info("데이터를 불러오는 중입니다.")
        else:
            for idx, row in enumerate(popular_foods):
                food_id, food_name, category_name, click_count = row
                
                card_html = f"""
                <div class="food-card">
                    <div>
                        <span style="font-weight: 700; color: #ff7e5f; margin-right: 8px;">{idx+1}</span>
                        <span class="food-name">{food_name}</span>
                        <span class="category-badge">{category_name}</span>
                        <span style="font-size:0.8rem; color:#718096; margin-left:10px;">누적 클릭: {click_count}회</span>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                btn_col1, btn_col2, btn_spacer = st.columns([1, 1.2, 4])
                with btn_col1:
                    if st.button("🖱️ 클릭", key=f"overall_click_{food_id}_{idx}"):
                        send_interaction_log(user_id, food_id, category_name, "CLICK")
                with btn_col2:
                    if st.button("❤️ 찜하기", key=f"overall_like_{food_id}_{idx}"):
                        send_interaction_log(user_id, food_id, category_name, "LIKE")
                
                st.write("---")
                
    with tab2:
        st.markdown('<p style="color:#a0aec0; font-size:0.9rem;">원하는 카테고리를 선택해 해당 분류에서 가장 핫한 요리를 확인해 보세요.</p>', unsafe_allow_html=True)
        
        categories = get_all_categories()
        selected_category = st.selectbox("음식 카테고리 선택", options=categories, key="popular_cat_select")
        
        if selected_category:
            cat_foods = fetch_popular_by_category(selected_category, 10)
            
            if not cat_foods:
                st.info(f"'{selected_category}' 카테고리에 등록된 인기 음식이 아직 없습니다.")
            else:
                for idx, row in enumerate(cat_foods):
                    food_id, food_name, category_name, click_count = row
                    
                    card_html = f"""
                    <div class="food-card">
                        <div>
                            <span style="font-weight: 700; color: #9b59b6; margin-right: 8px;">{idx+1}</span>
                            <span class="food-name">{food_name}</span>
                            <span class="category-badge" style="background: rgba(155, 89, 182, 0.15); color: #9b59b6;">{category_name}</span>
                            <span style="font-size:0.8rem; color:#718096; margin-left:10px;">누적 클릭: {click_count}회</span>
                        </div>
                    </div>
                    """
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    btn_col1, btn_col2, btn_spacer = st.columns([1, 1.2, 4])
                    with btn_col1:
                        if st.button("🖱️ 클릭", key=f"cat_click_{food_id}_{idx}"):
                            send_interaction_log(user_id, food_id, category_name, "CLICK")
                    with btn_col2:
                        if st.button("❤️ 찜하기", key=f"cat_like_{food_id}_{idx}"):
                            send_interaction_log(user_id, food_id, category_name, "LIKE")
                    
                    st.write("---")
