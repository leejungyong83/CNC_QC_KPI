import streamlit as st
from datetime import datetime

# 기본 페이지 설정
st.set_page_config(
    page_title="품질검사 KPI 관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state['page'] = 'dashboard'

# 사이드바 생성 함수
def create_sidebar():
    with st.sidebar:
        # 현재 시간
        st.write(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # KPI 관리 메뉴
        st.markdown("## KPI 관리 메뉴")
        
        menu_items = {
            "📊 관리자": "admin",
            "📈 대시보드": "dashboard",
            "📝 일일 성과 입력": "daily_input",
            "👥 검사원 관리": "inspector_manage",
            "📊 리포트": "report"
        }
        
        for label, page in menu_items.items():
            if st.button(label, key=f"btn_{page}", use_container_width=True):
                st.session_state.page = page
        
        # 관리자 메뉴
        st.markdown("## 관리자 메뉴")
        
        admin_items = {
            "👥 사용인원 현황": "user_status",
            "✏️ 사용자 관리": "user_manage",
            "📱 로그아웃": "logout"
        }
        
        for label, page in admin_items.items():
            if st.button(label, key=f"btn_{page}", use_container_width=True):
                st.session_state.page = page

# 메인 페이지 컨텐츠
def main_content():
    if st.session_state.page == "dashboard":
        st.title("대시보드")
    elif st.session_state.page == "daily_input":
        st.title("일일 성과 입력")
    elif st.session_state.page == "inspector_manage":
        st.title("검사원 관리")
    elif st.session_state.page == "report":
        st.title("리포트")
    elif st.session_state.page == "user_status":
        st.title("사용인원 현황")
    elif st.session_state.page == "user_manage":
        st.title("사용자 관리")
    elif st.session_state.page == "logout":
        st.title("로그아웃")

# 스타일 설정
st.markdown("""
<style>
        .stButton > button {
        width: 100%;
        text-align: left;
        background-color: white;
            color: black;
            border: 1px solid #ddd;
        padding: 10px;
            border-radius: 5px;
            margin-bottom: 5px;
        }
        .stButton > button:hover {
            background-color: #f0f2f6;
        }
        .sidebar .sidebar-content {
            background-color: #f0f2f6;
    }
</style>
""", unsafe_allow_html=True)

# 앱 실행
def main():
    create_sidebar()
    main_content()

if __name__ == "__main__":
    main() 