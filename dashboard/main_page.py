import streamlit as st
import sys
import os

# PYTHONPATH에 /app이 들어가 있지만 로컬 구동 시를 대비해 프로젝트 루트를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.auth.login import get_user_by_nickname, create_user_with_categories, get_all_categories
from dashboard.components.search_box import render_search_box
from dashboard.components.recommendation_panel import render_recommendation_panel
from dashboard.components.popular_panel import render_popular_panel

# 1. Page Configuration & Setup
st.set_page_config(
    page_title="Bapsang - 개인화 음식 추천 & 검색 대시보드",
    page_icon="🍚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Premium Custom CSS Styles
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&family=Noto+Sans+KR:wght@300;400;700&display=swap" rel="stylesheet">
<style>
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', 'Noto Sans KR', sans-serif;
    }
    
    .stApp {
        background-color: #0b0d10;
        background-image: radial-gradient(circle at 10% 20%, rgba(230, 126, 34, 0.05) 0%, transparent 40%),
                          radial-gradient(circle at 90% 80%, rgba(142, 68, 173, 0.05) 0%, transparent 40%);
        color: #e2e8f0;
    }
    
    /* Title Gradient styling */
    .title-gradient {
        background: linear-gradient(135deg, #f39c12 0%, #e67e22 50%, #d35400 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-align: center;
        letter-spacing: -1px;
    }
    
    .subtitle-text {
        color: #a0aec0;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    
    /* Card Glassmorphism Design */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease, border-color 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(230, 126, 34, 0.3);
    }
    
    /* Food Card Item styling */
    .food-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        transition: all 0.2s ease;
    }
    .food-card:hover {
        background: rgba(255, 255, 255, 0.05);
        border-color: rgba(255, 255, 255, 0.1);
    }
    .food-name {
        font-size: 1.1rem;
        font-weight: 600;
        color: #f7fafc;
    }
    .category-badge {
        background: rgba(230, 126, 34, 0.15);
        color: #e67e22;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-left: 8px;
    }
    
    /* Streamlit Input & Button Tweaks */
    div.stButton > button {
        background: linear-gradient(135deg, #e67e22 0%, #d35400 100%) !important;
        color: white !important;
        border-radius: 24px !important;
        border: none !important;
        padding: 8px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        box-shadow: 0 4px 15px rgba(230, 126, 34, 0.2) !important;
    }
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(230, 126, 34, 0.4) !important;
        filter: brightness(1.1) !important;
    }
    div.stButton > button:active {
        transform: translateY(0px) !important;
    }
    
    /* Subtitle block */
    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #f39c12;
        margin-bottom: 1rem;
        border-left: 4px solid #e67e22;
        padding-left: 10px;
        letter-spacing: -0.5px;
    }
    
    /* Profile header styling */
    .profile-banner {
        background: linear-gradient(90deg, rgba(230, 126, 34, 0.1) 0%, rgba(142, 68, 173, 0.1) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 16px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 30px;
    }
    
    /* Toast styles override */
    [data-testid="stNotificationContentSuccess"] {
        background-color: rgba(46, 204, 113, 0.2) !important;
        border: 1px solid #2ecc71 !important;
        color: #eafeed !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. Session State Initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "need_preference_setup" not in st.session_state:
    st.session_state.need_preference_setup = False
if "temp_username" not in st.session_state:
    st.session_state.temp_username = None

# 4. App Routing Control
if not st.session_state.logged_in:
    # ─── 닉네임 기반 프로필 로그인/생성 화면 ───
    st.markdown('<div class="title-gradient">Bapsang</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">실시간 데이터 파이프라인 기반 음식 추천 & 검색 대시보드</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<h3 style="text-align: center; margin-top: 0; color: #f39c12;">😋 테스트 프로필 입장</h3>', unsafe_allow_html=True)
        st.markdown('<p style="text-align: center; color: #a0aec0; font-size: 0.9rem; margin-bottom: 24px;">패스워드 없이 닉네임만으로 간편하게 시작하세요.</p>', unsafe_allow_html=True)
        
        # 닉네임 입력 (선호 카테고리 설정 모드가 아닐 때)
        if not st.session_state.need_preference_setup:
            nickname = st.text_input("닉네임(닉네임이 식별자가 됩니다)", placeholder="예: 철수, bapsang_test", key="nickname_input").strip()
            
            if st.button("입장하기"):
                if not nickname:
                    st.warning("닉네임을 입력해 주세요!")
                else:
                    user = get_user_by_nickname(nickname)
                    if user:
                        # 기존 유저 존재: 즉시 로그인
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.logged_in = True
                        st.success(f"반가워요, {nickname}님! 대시보드로 입장합니다.")
                        st.rerun()
                    else:
                        # 신규 유저: 선호 카테고리 설정 화면 유도
                        st.session_state.temp_username = nickname
                        st.session_state.need_preference_setup = True
                        st.rerun()
        
        # 신규 유저 선호 카테고리 설정 모드
        else:
            st.info(f"✨ '{st.session_state.temp_username}'님은 처음 방문하셨네요! 취향에 맞춰 첫 추천을 준비하기 위해 선호 카테고리를 선택해 주세요.")
            
            all_cats = get_all_categories()
            selected_cats = st.multiselect(
                "선호하는 카테고리 2~3개를 골라주세요 (필수)",
                options=all_cats,
                max_selections=5
            )
            
            sub_col1, sub_col2 = st.columns([1, 1])
            with sub_col1:
                if st.button("돌아가기"):
                    st.session_state.need_preference_setup = False
                    st.session_state.temp_username = None
                    st.rerun()
            with sub_col2:
                if st.button("프로필 생성 & 로그인"):
                    if len(selected_cats) < 2 or len(selected_cats) > 3:
                        st.error("카테고리는 반드시 2~3개 선택하셔야 합니다.")
                    else:
                        user_id = create_user_with_categories(st.session_state.temp_username, selected_cats)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = st.session_state.temp_username
                            st.session_state.logged_in = True
                            st.session_state.need_preference_setup = False
                            st.session_state.temp_username = None
                            st.success(f"프로필이 생성되었습니다. 환영합니다, {st.session_state.username}님!")
                            st.rerun()
                        else:
                            st.error("프로필 생성 중 오류가 발생했습니다. 다시 시도해 주세요.")
        
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # ─── 메인 대시보드 화면 ───
    
    # 1. 탑 네비게이션 / 프로필 바
    st.markdown(f"""
    <div class="profile-banner">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 1.8rem;">🍚</span>
            <div>
                <h4 style="margin: 0; color: #f39c12;">Bapsang Dashboard</h4>
                <p style="margin: 0; font-size: 0.85rem; color: #a0aec0;">프로필: <strong>{st.session_state.username}</strong> (ID: {st.session_state.user_id})</p>
            </div>
        </div>
        <div>
            <!-- 로그아웃 버튼은 streamlit 네이티브 사용 -->
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 헤더에 로그아웃 버튼 배치
    col_banner_left, col_banner_right = st.columns([8.5, 1.5])
    with col_banner_right:
        if st.button("다른 프로필로 전환 (로그아웃)", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.success("로그아웃 되었습니다.")
            st.rerun()
            
    # 2. 메인 바디 레이아웃
    # 왼쪽: 검색창 및 결과, 카테고리/인기 랭킹
    # 오른쪽: 개인화 추천 영역
    col_left, col_right = st.columns([1.2, 1])
    
    with col_left:
        # 하이브리드 검색창 컴포넌트 호출
        render_search_box()
        
        # 인기 음식 & 카테고리별 랭킹 컴포넌트 호출
        render_popular_panel()
        
    with col_right:
        # 개인화 추천 (ALS + Fallback) 컴포넌트 호출
        render_recommendation_panel()
