import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.auth.login import get_user_by_nickname, create_user_with_categories, get_all_categories
from dashboard.components.search_box import render_search_box
from dashboard.components.recommendation_panel import render_recommendation_panel
from dashboard.components.popular_panel import render_popular_panel

st.set_page_config(
    page_title="Bapsang",
    page_icon="🍚",
    layout="centered",
    initial_sidebar_state="collapsed"
)

def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "static", "style.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

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

if not st.session_state.logged_in:
    st.markdown('<div class="title-gradient">Bapsang</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">실시간 데이터 파이프라인 기반 음식 추천 & 검색 대시보드</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        if not st.session_state.need_preference_setup:
            st.markdown('<h3 style="text-align:center; margin-top:0; color:#f39c12;">테스트 프로필 입장</h3>', unsafe_allow_html=True)
            st.markdown('<p style="text-align:center; color:#a0aec0; font-size:0.88rem; margin-bottom:20px;">닉네임만으로 간편하게 시작하세요.</p>', unsafe_allow_html=True)

            nickname = st.text_input("닉네임", placeholder="예: 철수, bapsang_test", key="nickname_input").strip()

            if st.button("입장하기", use_container_width=True):
                if not nickname:
                    st.warning("닉네임을 입력해 주세요.")
                else:
                    user = get_user_by_nickname(nickname)
                    if user:
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.logged_in = True
                        st.rerun()
                    else:
                        st.session_state.temp_username = nickname
                        st.session_state.need_preference_setup = True
                        st.rerun()
        else:
            st.markdown(f'<p style="color:#a0aec0; font-size:0.9rem;"><b style="color:#f39c12;">{st.session_state.temp_username}</b>님은 처음 방문하셨네요.<br>취향에 맞는 첫 추천을 위해 선호 카테고리를 골라주세요.</p>', unsafe_allow_html=True)

            all_cats = get_all_categories()
            if not all_cats:
                st.error("카테고리를 불러올 수 없습니다. DB 연결을 확인해 주세요.")
                st.stop()

            selected_cats = st.multiselect(
                "선호 카테고리 2~3개 선택 (필수)",
                options=all_cats,
                max_selections=3
            )

            c1, c2 = st.columns(2)
            with c1:
                if st.button("돌아가기", use_container_width=True):
                    st.session_state.need_preference_setup = False
                    st.session_state.temp_username = None
                    st.rerun()
            with c2:
                if st.button("시작하기", use_container_width=True):
                    if len(selected_cats) < 2:
                        st.error("카테고리를 2개 이상 선택해 주세요.")
                    else:
                        user_id = create_user_with_categories(st.session_state.temp_username, selected_cats)
                        if user_id:
                            st.session_state.user_id = user_id
                            st.session_state.username = st.session_state.temp_username
                            st.session_state.logged_in = True
                            st.session_state.need_preference_setup = False
                            st.session_state.temp_username = None
                            st.rerun()
                        else:
                            st.error("프로필 생성 중 오류가 발생했습니다.")

        st.markdown('</div>', unsafe_allow_html=True)

else:
    col_l, col_r = st.columns([7, 3])
    with col_l:
        st.markdown(f"""
        <div class="profile-banner">
            <span style="font-size:1.5rem;">🍚</span>
            <span style="color:#f39c12; font-weight:700;">Bapsang</span>
            <span style="color:#a0aec0; font-size:0.85rem;">
                {st.session_state.username} (ID: {st.session_state.user_id})
            </span>
        </div>
        """, unsafe_allow_html=True)
    with col_r:
        if st.button("다른 프로필로 전환", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()

    render_search_box()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    render_recommendation_panel()

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)

    render_popular_panel()