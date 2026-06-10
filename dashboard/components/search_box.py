import streamlit as st
import streamlit.components.v1 as components
import os
import requests

FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


def send_interaction_log(user_id: int, food_id: int, category_name: str, action_type: str):
    try:
        payload = {
            "user_id": user_id,
            "food_id": food_id,
            "category_name": category_name,
            "action_type": action_type
        }
        endpoint = "click" if action_type == "CLICK" else "like"
        res = requests.post(f"{FASTAPI_URL}/logs/{endpoint}", json=payload, timeout=3)
        if res.status_code == 200:
            st.toast(f"{'클릭' if action_type == 'CLICK' else '찜'} 로그 전송 완료")
        else:
            st.toast(f"로그 전송 실패 (코드: {res.status_code})")
    except Exception as e:
        st.toast(f"API 연결 실패: {str(e)}")


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
    if st.button("찜하기 ❤️", use_container_width=True, key=f"dialog_like_search_{food_id}"):
        send_interaction_log(st.session_state.user_id, food_id, category_name, "LIKE")
        st.success("찜 목록에 추가됐어요!")


def render_search_box():
    components.html("""
    <style>
        body { margin:0; padding:0; background:transparent; }
        .section-title { font-size:1.4rem; font-weight:700; color:#f39c12; border-left:4px solid #e67e22; padding-left:10px; margin:0 0 4px 0; font-family:'Pretendard','Noto Sans KR',sans-serif; }
        .section-desc { color:#a0aec0; font-size:0.88rem; margin:4px 0 0 0; font-family:'Pretendard','Noto Sans KR',sans-serif; }
    </style>
    <p class="section-title">하이브리드 음식 검색</p>
    <p class="section-desc">키워드 매칭과 벡터 의미론적 검색을 결합해 최적의 음식을 찾아드립니다.</p>
    """, height=70, scrolling=False)

    search_query = st.text_input(
        "",
        placeholder="예: 얼큰한 김치찌개, 비 오는 날 먹고 싶은 음식",
        key="search_input",
        label_visibility="collapsed"
    )

    if not search_query:
        return

    try:
        with st.spinner("검색 중..."):
            response = requests.get(
                f"{FASTAPI_URL}/search",
                params={"q": search_query, "limit": 10},
                timeout=5
            )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])

            if not results:
                st.info("검색 결과가 없습니다.")
                return

            st.markdown(f'<p style="color:#a0aec0; font-size:0.85rem;">"{search_query}" 검색 결과 {data.get("count", 0)}개</p>', unsafe_allow_html=True)

            # 가로 스크롤 카드 HTML
            cards_html = '<div style="display:flex; gap:12px; overflow-x:auto; padding:8px 0 16px 0; scrollbar-width:thin; scrollbar-color:#e67e22 #1a1d23;">'
            for result in results:
                rrf_score = result.get("rrf_score", 0.0)
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
                    <div style="font-weight:600; color:#f7fafc; font-size:0.95rem; margin-bottom:6px; line-height:1.3;">{result.get('food_name', '')}</div>
                    <div style="background:rgba(230,126,34,0.15); color:#e67e22; padding:2px 8px; border-radius:6px; font-size:0.72rem; font-weight:600; display:inline-block; margin-bottom:8px;">{result.get('category_name', '')}</div>
                    <div style="color:#718096; font-size:0.75rem;">RRF: {rrf_score:.4f}</div>
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
            cols = st.columns(min(len(results), 5))
            for idx, result in enumerate(results):
                food_id = result.get("food_id")
                food_name = result.get("food_name")
                category_name = result.get("category_name")
                col_idx = idx % 5
                with cols[col_idx]:
                    if st.button(food_name[:6], key=f"s_open_{food_id}_{idx}", use_container_width=True):
                        send_interaction_log(st.session_state.user_id, food_id, category_name, "CLICK")
                        food_detail_dialog(food_id, food_name, category_name)

        else:
            st.error(f"검색 API 오류 (코드: {response.status_code})")

    except requests.exceptions.RequestException:
        st.error("FastAPI 서버에 연결할 수 없습니다.")
    except Exception as e:
        st.error(f"오류: {str(e)}")