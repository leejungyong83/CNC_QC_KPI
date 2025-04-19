import streamlit as st

# 앱 설정
st.set_page_config(page_title="CNC 품질관리 시스템", layout="wide")

# 로그인 UI
st.title("CNC 품질관리 시스템")
st.subheader("로그인")

# 기본 관리자 계정 안내
st.info("기본 계정: admin / admin123", icon="ℹ️")

# 로그인 입력 필드
username = st.text_input("아이디", key="login_username")
password = st.text_input("비밀번호", type="password", key="login_password")

# 로그인 버튼
if st.button("로그인", key="login_button"):
    if not username:
        st.error("아이디를 입력하세요.")
    elif not password:
        st.error("비밀번호를 입력하세요.")
    elif username == "admin" and password == "admin123":
        st.success("로그인 성공!")
        st.session_state.logged_in = True
        st.rerun()
    else:
        st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

# 로그인 성공 시 표시할 내용
if st.session_state.get("logged_in", False):
    st.sidebar.success(f"{username}님 환영합니다!")
    st.sidebar.write("역할: 관리자")
    
    # 로그아웃 버튼
    if st.sidebar.button("로그아웃", key="sidebar_logout_btn"):
        st.session_state.logged_in = False
        st.rerun()
    
    # 언어 선택
    lang_col1, lang_col2 = st.sidebar.columns(2)
    with lang_col1:
        if st.button("한국어", key="sidebar_lang_ko_btn"):
            st.session_state.language = 'ko'
            st.rerun()
    with lang_col2:
        if st.button("Tiếng Việt", key="sidebar_lang_vi_btn"):
            st.session_state.language = 'vi'
            st.rerun()
    
    # 메인 컨텐츠
    st.title("대시보드")
    st.write("이 부분에 대시보드 내용이 표시됩니다.")
    
    # 각 메뉴 항목
    st.sidebar.markdown("### 관리자 메뉴")
    admin_menu = {
        "manager_auth": "👥 관리자 및 사용자 통합 관리",
        "inspection_data": "📊 검사실적 관리"
    }
    
    selected_admin = st.sidebar.radio(
        label="",
        options=list(admin_menu.keys()),
        format_func=lambda x: admin_menu[x],
        key="sidebar_admin_menu_radio", 
        index=0
    )
    
    st.sidebar.markdown("### 리포트 메뉴")
    report_menu = {
        "total_dashboard": "📈 종합 대시보드",
        "daily_report": "📊 일간 리포트",
        "weekly_report": "📅 주간 리포트",
        "monthly_report": "📆 월간 리포트",
        "quality_report": "⭐ 월간 품질 리포트"
    }
    
    selected_report = st.sidebar.radio(
        label="",
        options=list(report_menu.keys()),
        format_func=lambda x: report_menu[x],
        key="sidebar_report_menu_radio",
        index=0
    ) 