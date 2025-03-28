import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
import json
from pathlib import Path
import os

try:
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from google.oauth2 import service_account
except ImportError:
    st.error("필요한 라이브러리가 설치되지 않았습니다. 'pip install gspread oauth2client google-auth-oauthlib google-auth-httplib2'를 실행해주세요.")

# 페이지 설정을 가장 먼저 실행
st.set_page_config(
    page_title="품질검사 KPI 관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 현재 스크립트의 디렉토리를 기준으로 경로 설정
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 데이터 파일 경로
INSPECTION_DATA_FILE = DATA_DIR / "inspection_data.json"
INSPECTOR_DATA_FILE = DATA_DIR / "inspector_data.json"
DEFECT_DATA_FILE = DATA_DIR / "defect_data.json"

# 데이터베이스 초기화
def init_db():
    """
    JSON 파일 기반 데이터베이스 초기화
    """
    try:
        # 검사원 데이터 초기화
        if not INSPECTOR_DATA_FILE.exists():
            with open(INSPECTOR_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"inspectors": []}, f, ensure_ascii=False, indent=2)
        
        # 검사 데이터 초기화
        if not INSPECTION_DATA_FILE.exists():
            with open(INSPECTION_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"inspections": []}, f, ensure_ascii=False, indent=2)
        
        # 불량 데이터 초기화
        if not DEFECT_DATA_FILE.exists():
            with open(DEFECT_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"defects": []}, f, ensure_ascii=False, indent=2)
        
        print("데이터베이스 초기화 완료!")
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

# 앱 시작 시 데이터베이스 초기화
init_db()

# 세션 상태 초기화 함수
def init_session_state():
    # 앱 시작 시 반드시 초기화할 항목들
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        
    if 'username' not in st.session_state:
        st.session_state.username = ""
        
    if 'user_role' not in st.session_state:
        st.session_state.user_role = "일반"  # 기본값은 일반 사용자
        
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
        
    if 'today_inspectors' not in st.session_state:
        st.session_state.today_inspectors = {
            "PQC_LINE": 5,
            "CNC_1": 3,
            "CNC_2": 2,
            "CDC": 4
        }
        
    if 'defect_types' not in st.session_state:
        st.session_state.defect_types = [
            "외관불량", "치수불량", "기능불량", "누락불량", "라벨불량", 
            "포장불량", "케이블불량", "조립불량", "기타불량"
        ]
        
    # 일일 성과 입력 폼 관련 상태 변수
    if 'basic_info_valid' not in st.session_state:
        st.session_state.basic_info_valid = False
        
    if 'registered_defects' not in st.session_state:
        st.session_state.registered_defects = []

# 세션 상태 초기화 실행
init_session_state()

# CSS 스타일
st.markdown("""
<style>
    /* 상단 불필요한 영역 제거 */
    #MainMenu, header, footer {display: none !important;}
    
    /* 메인 컨테이너 스타일 */
    .main .block-container {
        padding: 0.5rem 5rem !important;
        max-width: 100% !important;
    }
    
    /* 제목 중복 제거 */
    .main h1:first-of-type {
        display: none !important;
    }
    
    /* 제목 스타일 */
    h1 {
        font-size: 1.8rem !important;
        padding-top: 0 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 1.5rem !important;
    }
    
    /* 입력 폼 스타일 */
    .stForm {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 8px;
        border: 1px solid #e9ecef;
    }
    
    /* 입력 필드 레이블 스타일 */
    .stTextInput label, .stSelectbox label {
        font-weight: 500 !important;
        color: #333 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* 선택 박스 스타일 수정 */
    .stSelectbox > div {
        position: relative !important;
        z-index: 1 !important;
    }
    
    .stSelectbox > div > div {
        background: white !important;
        border: 1px solid #dee2e6 !important;
        border-radius: 4px !important;
        min-height: 38px !important;
    }
    
    /* 저장 버튼 스타일 */
    .stButton > button {
        width: 100% !important;
        background-color: #1976D2 !important;
        color: white !important;
        padding: 0.5rem 1rem !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        border: none !important;
        border-radius: 4px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        background-color: #1565C0 !important;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2) !important;
    }
    
    .stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* 성공 메시지 스타일 */
    .stSuccess {
        animation: fadeInUp 0.5s ease-out !important;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
</style>
""", unsafe_allow_html=True)

# 대시보드 스타일 추가
st.markdown("""
<style>
    .dashboard-container {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
    }
    
    .metric-title {
        color: #666;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    .metric-value {
        color: #1a1a1a;
        font-size: 1.8rem;
        font-weight: 600;
        margin: 0.5rem 0;
    }
    
    .chart-container {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin: 1rem 0;
        border: 1px solid #f0f0f0;
    }
    
    .status-indicator {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    
    .status-good {
        background-color: #10B981;
    }
    
    .status-warning {
        background-color: #F59E0B;
    }
    
    .status-bad {
        background-color: #EF4444;
    }
</style>
""", unsafe_allow_html=True)

# CSS 스타일 수정
st.markdown("""
<style>
    /* 사이드바 너비 및 스타일 수정 */
    [data-testid="stSidebar"] {
        width: 220px !important;
        background: linear-gradient(180deg, #2C3E50 0%, #3498DB 100%);
    }
    
    [data-testid="stSidebar"] > div:first-child {
        width: 220px !important;
        padding: 1rem 0.5rem;
    }
    
    /* 사이드바 헤더 스타일 */
    .sidebar-header {
        color: white;
        padding: 0.5rem;
        margin-bottom: 1rem;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    /* 메뉴 버튼 스타일 */
    .stButton button {
        width: 100%;
        background: rgba(255,255,255,0.1);
        color: white;
        border: none;
        text-align: left;
        padding: 0.7rem 1rem;
        margin: 0.2rem 0;
        border-radius: 4px;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: rgba(255,255,255,0.2);
        transform: translateX(5px);
    }
    
    /* 현재 시간 표시 스타일 */
    .current-time {
        color: rgba(255,255,255,0.7);
        font-size: 0.8rem;
        margin-top: 0.5rem;
    }
    
    /* 버전 정보 스타일 */
    .version-info {
        position: fixed;
        bottom: 1rem;
        color: rgba(255,255,255,0.5);
        font-size: 0.7rem;
        padding: 0.5rem;
    }
    
    /* 구분선 스타일 */
    hr {
        border: none;
        border-top: 1px solid rgba(255,255,255,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# CSS 스타일 적용
st.markdown("""
<style>
    /* 사이드바 스타일 */
    section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, #1a237e 0%, #1976D2 100%) !important;
        padding: 1rem 0.5rem;
    }
    
    /* 상단 불필요한 영역 제거 */
    section[data-testid="stSidebar"] > div:first-child,
    section[data-testid="stSidebar"] div[data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 상단 제목 스타일 */
    section[data-testid="stSidebar"] h3 {
        color: white !important;
        font-weight: 600;
        margin: 0 0 0.5rem 0.5rem;
        font-size: 1.1rem;
    }
    
    /* 현재 시간 표시 스타일 */
    section[data-testid="stSidebar"] p {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 0.85rem;
        margin: 0 0 1rem 0.5rem;
    }
    
    /* 사이드바 버튼 스타일 */
    section[data-testid="stSidebar"] button {
        width: calc(100% - 0.8rem) !important;
        background: rgba(255, 255, 255, 0.08) !important;
        color: white !important;
        padding: 0.4rem 0.8rem !important;
        margin: 0.15rem 0.4rem !important;
        border: none !important;
        border-radius: 4px !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        line-height: 1.2 !important;
        min-height: 36px !important;
    }
    
    /* 버튼 내부 컨테이너 정렬 */
    section[data-testid="stSidebar"] button > div {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        width: 100% !important;
    }
    
    /* 버튼 내부 텍스트 정렬 */
    section[data-testid="stSidebar"] button p {
        text-align: center !important;
        margin: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }
    
    /* 버튼 아이콘 정렬 */
    section[data-testid="stSidebar"] button svg {
        margin-right: 0.5rem !important;
    }
    
    /* 상단 툴바 완전 제거 */
    [data-testid="stToolbar"],
    [data-testid="baseButton-headerNoPadding"],
    div.stToolbar {
        display: none !important;
    }
    
    /* 헤더 영역 제거 */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    
    /* 상단 여백 제거 */
    .main .block-container {
        padding-top: 0 !important;
        padding-bottom: 1rem !important;
        margin-top: 0 !important;
    }
    
    /* 나머지 스타일은 동일하게 유지 */
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .stMetric:hover {
        box-shadow: 0 2px 5px rgba(0,0,0,0.15);
    }
    
    .stPlotlyChart {
        background-color: white;
        padding: 10px;
        border-radius: 4px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# 로그인 검증 함수 추가
def verify_login(username, password):
    """사용자 로그인 검증 함수"""
    # 관리자 계정
    if username == "dlwjddyd83@gmail.com" and password == "11112222":
        return True, "admin"
    # 일반 사용자 계정 (예시)
    elif username == "user" and password == "1234":
        return True, "user"
    return False, None

def check_password():
    """로그인 UI 및 인증 처리를 담당하는 함수"""
    
    # 세션 상태 초기화
    if 'login_attempts' not in st.session_state:
        st.session_state.login_attempts = 0
    
    # 카드 스타일의 로그인 UI
    st.markdown("""
    <style>
            .login-box {
            max-width: 400px;
            margin: 0 auto;
                padding: 2rem;
            background-color: white;
                border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-top: 15vh;
            }
            .login-title {
            text-align: center;
                font-size: 1.5rem;
                font-weight: 600;
            margin-bottom: 1.5rem;
            color: #1e3a8a;
        }
        .login-input {
            margin-bottom: 1rem;
        }
        .login-btn {
                width: 100%;
                margin-top: 1rem;
            }
            .login-footer {
            text-align: center;
            font-size: 0.8rem;
                margin-top: 1.5rem;
                color: #6b7280;
            }
        </style>
            <div class="login-box">
        <div class="login-title">KPI 관리 시스템</div>
    """, unsafe_allow_html=True)
    
    # 로그인 폼 생성
    with st.form("login_form"):
        username = st.text_input("아이디", placeholder="이메일 또는 사용자명", key="login_id")
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호", key="login_pw")
        
        # 로그인 버튼
        submitted = st.form_submit_button("로그인", use_container_width=True)
    
        st.markdown("""
        <div class="login-footer">
            Quality KPI Monitor v1.0.1
        </div>
            </div>
        """, unsafe_allow_html=True)
        
    # 입력값 검증
        if submitted:
        if not username:
            st.error("아이디를 입력하세요.")
            return False
        if not password:
            st.error("비밀번호를 입력하세요.")
            return False
        
            # 로그인 검증
        auth_success, user_role = verify_login(username, password)
        
        if auth_success:
            # 로그인 성공 처리
                st.session_state.logged_in = True
            st.session_state.user_role = user_role
            st.session_state.username = username
            st.session_state.login_attempts = 0
            st.session_state.show_welcome_popup = True
            
            # 로그인 시 기본 페이지 설정
                st.session_state.page = "dashboard"
            
            # 리디렉션
                st.rerun()
            
            return True
            else:
            # 로그인 실패 처리
            st.session_state.login_attempts += 1
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            if st.session_state.login_attempts >= 3:
                st.warning("로그인을 3회 이상 실패했습니다. 계정 정보를 확인하세요.")
            return False
        
    return False
    
def show_login_page():
    """로그인 페이지를 표시하는 함수"""
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    if check_password():
        return True
    return False

# 사이드바 함수 수정
def show_sidebar():
    """사이드바 메뉴를 표시하는 함수"""
    with st.sidebar:
        st.markdown("### KPI 관리 메뉴")
        st.markdown(f"현재 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        # 사용자 정보 표시
        st.markdown(f"""
            <div style="
                padding: 0.5rem;
                background-color: rgba(255,255,255,0.1);
                border-radius: 4px;
                margin-bottom: 1rem;
            ">
                <span style="color: #fff; font-size: 0.9rem;">
                    {'👑 관리자' if st.session_state.user_role == 'admin' else '👤 일반 사용자'}
                </span>
            </div>
        """, unsafe_allow_html=True)
        
        # 공통 메뉴
        if st.button("📊 대시보드", key="btn_dashboard", use_container_width=True):
            st.session_state.page = "dashboard"
            st.rerun()
            
        if st.button("📝 일일 성과 입력", key="btn_daily", use_container_width=True):
            st.session_state.page = "daily"
            st.rerun()
            
        if st.button("👥 검사원 관리", key="btn_inspectors", use_container_width=True):
            st.session_state.page = "inspectors"
            st.rerun()
            
        if st.button("📈 리포트", key="btn_report", use_container_width=True):
            st.session_state.page = "report"
            st.rerun()
        
        # 관리자 전용 메뉴
        if st.session_state.user_role == "admin":
            st.markdown("---")
            st.markdown("### 관리자 메뉴")
            
            if st.button("👨‍👩‍👦 사용인원 현황", key="btn_staff", use_container_width=True):
                st.session_state.page = "staff"
                st.rerun()
                
            if st.button("🔑 사용자 관리", key="btn_users", use_container_width=True):
                st.session_state.page = "users"
                st.rerun()
        
        # 구분선과 로그아웃
        st.markdown("---")
        if st.button("🚪 로그아웃", key="btn_logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.page = "login"
            st.rerun()

# 메인 앱 함수 수정
def main():
    # 세션 상태 초기화
    init_session_state()
    
    # 데이터베이스 초기화
    init_db()
    
    # 로그인 상태 확인
    if not st.session_state.logged_in:
        show_login_page()
    else:
        # CSS 스타일 적용
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 1rem;
                    padding-bottom: 1rem;
                }
                h1, h2, h3 {
                    margin-top: 0;
                }
                .main .block-container {
                    padding-left: 2rem;
                    padding-right: 2rem;
                    max-width: 100%;
                }
            </style>
        """, unsafe_allow_html=True)
        
        # 새로 로그인한 경우 환영 메시지 표시
        if st.session_state.show_welcome_popup:
            st.success(f"{st.session_state.username} 님, 환영합니다!")
            st.session_state.show_welcome_popup = False
        
        # 사이드바 표시
        show_sidebar()
        
        # 페이지 라우팅
        if st.session_state.page == "dashboard":
            show_dashboard()
        elif st.session_state.page == "inspectors":
            show_inspector_form()
        elif st.session_state.page == "daily":
            show_daily_performance()
        elif st.session_state.page == "report":
            show_report()
        elif st.session_state.page == "staff":
            show_staff_status()
        elif st.session_state.page == "users":
            show_user_management()
        # 기본 페이지 설정 (로그인 후 처음 보여줄 페이지)
        else:
            st.session_state.page = "dashboard"  # 기본 페이지를 대시보드로 설정
            show_dashboard()

# 대시보드 페이지
def show_dashboard():
    # 메트릭 카드 스타일 적용
    st.markdown("""
        <style>
            /* 메트릭 컨테이너 기본 스타일 */
            [data-testid="stMetric"] {
                background-color: white !important;
                padding: 1rem !important;
                border-radius: 8px !important;
                box-shadow: 0 2px 12px rgba(0,0,0,0.05) !important;
                border: 1px solid #e5e7eb !important;
                width: 100% !important;
                height: 140px !important;
                display: flex !important;
                flex-direction: column !important;
                justify-content: center !important;
            }
            
            /* 메트릭 컨테이너 내부 스타일 */
            [data-testid="stMetricLabel"] {
                display: flex !important;
                align-items: center !important;
                font-size: 0.9rem !important;
                color: #6B7280 !important;
                font-weight: 500 !important;
                padding: 0 !important;
                margin-bottom: 0.5rem !important;
            }
            
            [data-testid="stMetricValue"] {
                font-size: 1.8rem !important;
                font-weight: 600 !important;
                color: #1F2937 !important;
                padding: 0 !important;
                margin: 0.25rem 0 !important;
            }
            
            [data-testid="stMetricDelta"] {
                font-size: 0.8rem !important;
                padding: 0 !important;
                margin-top: 0.25rem !important;
            }
            
            /* 열 간격 조정 */
            [data-testid="column"] {
                padding: 0 0.5rem !important;
            }
            
            /* 첫 번째와 마지막 열의 패딩 조정 */
            [data-testid="column"]:first-child {
                padding-left: 0 !important;
            }
            
            [data-testid="column"]:last-child {
                padding-right: 0 !important;
            }
            
            /* 메트릭 컨테이너 내부 정렬 */
            [data-testid="stMetricValue"] > div {
                display: flex !important;
                justify-content: flex-start !important;
                align-items: center !important;
            }
            
            /* 메트릭 컨테이너 호버 효과 */
            [data-testid="stMetric"]:hover {
                box-shadow: 0 4px 16px rgba(0,0,0,0.1) !important;
                transform: translateY(-1px) !important;
                transition: all 0.2s ease !important;
            }
            
            /* 메트릭 컨테이너 내부 여백 조정 */
            [data-testid="stMetric"] > div {
                padding: 0 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # KPI 지표 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="🎯 검사 수량",
            value="1,234",
            delta="+5.2%",
            delta_color="inverse",
            help="금일 총 검사 수량"
        )
    
    with col2:
        st.metric(
            label="⚠️ 현재 불량률",
            value="2.3%",
            delta="-0.3%",
            delta_color="normal",
            help="현재 불량률 현황"
        )
    
    with col3:
        st.metric(
            label="⚡ 효율성",
            value="95.5%",
            delta="+2.1%",
            delta_color="inverse",
            help="검사 수량 / 작업 시간"
        )
    
    with col4:
        st.metric(
            label="⏱️ 작업 시간",
            value="390분",
            delta="+30분",
            delta_color="inverse",
            help="금일 총 작업 시간"
        )
    
    # 최고/최저 성과 검사원 섹션 추가
    st.markdown("### 👥 검사원 성과 현황")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
            <div style="
                background-color: #f8fafc;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1rem 0;
                border: 1px solid #e2e8f0;
            ">
                <h4 style="
                    color: #1e293b;
                    font-size: 1.1rem;
                    margin: 0 0 1rem 0;
                    display: flex;
                    align-items: center;
                ">
                    <span style="margin-right: 0.5rem;">🏆</span> Best 검사원
                </h4>
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 0.5rem;
                ">
                    <span style="
                        font-size: 1.2rem;
                        font-weight: 600;
                        color: #2563eb;
                        margin-right: 0.5rem;
                    ">홍길동</span>
                    <span style="
                        background-color: #dbeafe;
                        color: #1e40af;
                        padding: 0.2rem 0.5rem;
                        border-radius: 4px;
                        font-size: 0.8rem;
                        font-weight: 500;
                    ">PQC_LINE</span>
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.9rem;
                    color: #4b5563;
                ">
                    <span>검사량: 150개</span>
                    <span>불량률: 1.2%</span>
                    <span>효율성: 98%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div style="
                background-color: #f8fafc;
                padding: 1.5rem;
                border-radius: 8px;
                margin: 1rem 0;
                border: 1px solid #e2e8f0;
            ">
                <h4 style="
                    color: #1e293b;
                    font-size: 1.1rem;
                    margin: 0 0 1rem 0;
                    display: flex;
                    align-items: center;
                ">
                    <span style="margin-right: 0.5rem;">⚠️</span> Worst 검사원
                </h4>
                <div style="
                    display: flex;
                    align-items: center;
                    margin-bottom: 0.5rem;
                ">
                    <span style="
                        font-size: 1.2rem;
                        font-weight: 600;
                        color: #dc2626;
                        margin-right: 0.5rem;
                    ">김철수</span>
                    <span style="
                        background-color: #fee2e2;
                        color: #991b1b;
                        padding: 0.2rem 0.5rem;
                        border-radius: 4px;
                        font-size: 0.8rem;
                        font-weight: 500;
                    ">CNC_1</span>
                </div>
                <div style="
                    display: flex;
                    justify-content: space-between;
                    font-size: 0.9rem;
                    color: #4b5563;
                ">
                    <span>검사량: 120개</span>
                    <span>불량률: 3.1%</span>
                    <span>효율성: 96%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 📊 실시간 모니터링")
    
    # 차트 영역 - 컬럼 비율 조정
    col1, col2 = st.columns([1.6, 1])
    
    with col1:
        st.markdown("#### 📅 일별 검사현황 (최근 7일)")
        
        # 일별 데이터 생성 (실제로는 DB에서 가져올 데이터)
        days = pd.date_range(end=pd.Timestamp.today(), periods=7, freq='D')  # 최근 7일 데이터
        daily_data = pd.DataFrame({
            '날짜': days.strftime('%m/%d'),
            '요일': days.strftime('%a'),
            '검사량': np.random.randint(800, 1500, 7),
            '불량수량': np.random.randint(10, 30, 7)
        })
        
        # 불량률 계산
        daily_data['불량률'] = (daily_data['불량수량'] / daily_data['검사량'] * 100).round(2)
        
        # x축 날짜와 요일 표시 형식 변경
        daily_data['날짜_표시'] = daily_data.apply(lambda x: f"{x['날짜']}\n({x['요일']})", axis=1)
        
        # 차트 생성
        fig = go.Figure()
        
        # 검사량 바 차트
        fig.add_trace(go.Bar(
            x=daily_data['날짜_표시'],
            y=daily_data['검사량'],
            name='검사량',
            marker_color='#60A5FA',
            text=daily_data['검사량'].apply(lambda x: f'{x:,}'),
            textposition='outside',
            yaxis='y'
        ))
        
        # 불량률 라인 차트
        fig.add_trace(go.Scatter(
            x=daily_data['날짜_표시'],
            y=daily_data['불량률'],
            name='불량률',
            line=dict(color='#F87171', width=2),
            mode='lines+markers+text',
            text=daily_data['불량률'].apply(lambda x: f'{x:.1f}%'),
            textposition='top center',
            yaxis='y2'
        ))
        
        # 레이아웃 설정
        fig.update_layout(
            height=350,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(
                title='검사량(개)',
                titlefont=dict(color='#3B82F6'),
                tickfont=dict(color='#3B82F6'),
                gridcolor='rgba(0,0,0,0.1)',
                zeroline=False
            ),
            yaxis2=dict(
                title='불량률(%)',
                titlefont=dict(color='#EF4444'),
                tickfont=dict(color='#EF4444'),
                overlaying='y',
                side='right',
                zeroline=False
            ),
            xaxis=dict(
                tickangle=0,
                gridcolor='rgba(0,0,0,0.1)',
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=50, r=50, t=30, b=30),
            bargap=0.3,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 📈 불량유형 분포")
        
        # 불량유형 데이터
        defect_data = {
            '유형': ['치수', '외관', '기능', '기타'],
            '비율': [40, 30, 20, 10]
        }
        
        # 도넛 차트 생성
        fig = go.Figure(data=[go.Pie(
            labels=defect_data['유형'],
            values=defect_data['비율'],
            hole=.4,
            marker_colors=['#3B82F6', '#34D399', '#A78BFA', '#F59E0B'],
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(size=12),
            showlegend=False,
            pull=[0.05, 0.05, 0.05, 0.05]  # 조각을 약간 분리
        )])
        
        # 레이아웃 설정
        fig.update_layout(
            height=350,
            margin=dict(t=30, b=30, l=20, r=20),
            annotations=[dict(
                text='불량유형',
                x=0.5,
                y=0.5,
                font_size=14,
                font_family="Arial",
                showarrow=False
            )],
            paper_bgcolor='white',
            plot_bgcolor='white'
        )
        
        # 차트 표시
        st.plotly_chart(fig, use_container_width=True)

    # 3. 검사원 성과 현황 - 상세 정보 추가
    show_performance_table()

# 검사원 성과 현황 섹션 수정
def show_performance_table():
    st.markdown("""
        <div style="margin: 2rem 0 1rem 0">
            <h3 style="
                color: #1e293b;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
            ">
                👥 검사원 성과 현황
                <span style="
                    font-size: 0.8rem;
                    color: #6b7280;
                    margin-left: 0.5rem;
                    font-weight: normal;
                ">실시간 업데이트</span>
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    # 성과 데이터 준비
    performance_data = pd.DataFrame({
        '검사원': ['홍길동', '김철수', '이영희', '박민준'],
        '소속부서': ['PQC', 'CNC', 'PQC', 'CDC'],
        '담당공정': ['PQC_LINE', 'CNC_1', 'PQC_LINE', 'CDC_1'],
        '검사량': [150, 130, 140, 120],
        '불량수량': [3, 4, 2, 3],
        '불량률': [2.0, 3.1, 1.4, 2.5],
        '효율성': [98, 96, 97, 95],
        '작업시간': [7.5, 7.0, 7.2, 7.1]
    })
    
    # 각 행의 스타일을 동적으로 생성
    def get_row_style(row):
        # 효율성에 따른 배경색 설정
        if row['효율성'] >= 98:
            return 'background-color: rgba(34, 197, 94, 0.1)'
        elif row['효율성'] >= 96:
            return 'background-color: rgba(234, 179, 8, 0.1)'
        return ''
    
    # 불량률에 따른 색상 설정
    def color_defect_rate(val):
        if val < 2.0:
            return 'color: #059669; font-weight: 500'
        elif val < 3.0:
            return 'color: #B45309; font-weight: 500'
        return 'color: #DC2626; font-weight: 500'
    
    # 스타일이 적용된 데이터프레임 생성
    styled_df = performance_data.style\
        .apply(lambda x: [get_row_style(x)]*len(x), axis=1)\
        .format({
            '검사량': '{:,.0f}개',
            '불량수량': '{:,.0f}개',
            '불량률': '{:.1f}%',
            '효율성': '{:.0f}%',
            '작업시간': '{:.1f}h'
        })\
        .map(lambda x: color_defect_rate(x) if isinstance(x, (int, float)) and x < 5 else '', subset=['불량률'])\
        .set_properties(**{
            'font-size': '0.9rem',
            'text-align': 'center',
            'padding': '0.5rem'
        })
    
    # CSS 스타일 추가
    st.markdown("""
    <style>
        /* 데이터프레임 컨테이너 스타일 */
        [data-testid="stDataFrame"] {
            background: white;
            border-radius: 10px;
            padding: 1rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        }
        
        /* 테이블 헤더 스타일 */
        thead tr th {
            background-color: #f8fafc !important;
            padding: 0.75rem !important;
            font-weight: 600 !important;
            color: #1e293b !important;
            font-size: 0.9rem !important;
            text-align: center !important;
            border-bottom: 2px solid #e2e8f0 !important;
        }
        
        /* 테이블 셀 스타일 */
        tbody tr td {
            padding: 0.75rem !important;
            border-bottom: 1px solid #f1f5f9 !important;
            font-size: 0.9rem !important;
        }
        
        /* 행 호버 효과 */
        tbody tr:hover {
            background-color: #f8fafc !important;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # 데이터프레임 표시
    st.dataframe(
        styled_df,
        hide_index=True,
        column_config={
            "검사원": st.column_config.TextColumn(
                "검사원",
                width=100,
                help="검사원 이름"
            ),
            "소속부서": st.column_config.TextColumn(
                "소속부서",
                width=100
            ),
            "담당공정": st.column_config.TextColumn(
                "담당공정",
                width=120
            ),
            "검사량": st.column_config.NumberColumn(
                "검사량",
                width=100,
                help="금일 총 검사 수량"
            ),
            "불량수량": st.column_config.NumberColumn(
                "불량수량",
                width=100,
                help="발견된 불량 수량"
            ),
            "불량률": st.column_config.NumberColumn(
                "불량률(%)",
                width=100,
                help="불량률 = (불량수량/검사량) × 100"
            ),
            "효율성": st.column_config.NumberColumn(
                "효율성(%)",
                width=100,
                help="효율성 = (실제작업시간/계획작업시간) × 100"
            ),
            "작업시간": st.column_config.NumberColumn(
                "작업시간(h)",
                width=100,
                help="총 작업 시간"
            )
        }
    )

# 검사원 관리 페이지
def show_inspector_form():
    st.title("👥 검사원 관리")
    
    # 일별 검사원 출근 현황
    st.markdown("### 📊 금일 검사원 출근 현황")
    
    # 부서별 출근 현황 데이터 (예시)
    attendance_data = {
        'CNC_1': {'총원': 8, '출근': 7, '휴가': 1, '결근': 0},
        'CNC_2': {'총원': 6, '출근': 5, '휴가': 0, '결근': 1},
        'CDC': {'총원': 5, '출근': 5, '휴가': 0, '결근': 0},
        'PQC_LINE': {'총원': 7, '출근': 6, '휴가': 1, '결근': 0}
    }
    
    # 출근 현황 카드 표시
    cols = st.columns(len(attendance_data))
    for idx, (dept, data) in enumerate(attendance_data.items()):
        with cols[idx]:
            st.markdown(f"""
                <div style="
                    background-color: white;
                    padding: 1rem;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    text-align: center;
                ">
                    <h4 style="
                        color: #1e3a8a;
                        margin: 0 0 0.5rem 0;
                        font-size: 1rem;
                    ">{dept}</h4>
                    <div style="
                        font-size: 1.5rem;
                        font-weight: bold;
                        color: #2563eb;
                        margin-bottom: 0.5rem;
                    ">{data['출근']}/{data['총원']}명</div>
                    <div style="
                        display: flex;
                        justify-content: center;
                        gap: 0.5rem;
                        font-size: 0.8rem;
                    ">
                        <span style="color: #059669;">휴가 {data['휴가']}</span>
                        <span style="color: #dc2626;">결근 {data['결근']}</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    
    # 구분선
    st.markdown("---")
    
    # 부서별 출근율 차트
    st.markdown("#### 📈 부서별 출근율 추이 (최근 7일)")
    
    # 샘플 데이터 생성
    dates = pd.date_range(end=datetime.now(), periods=7, freq='D')
    attendance_history = pd.DataFrame({
        '날짜': dates.repeat(4),
        '부서': np.tile(['CNC_1', 'CNC_2', 'CDC', 'PQC_LINE'], 7),
        '출근율': np.random.uniform(0.8, 1.0, 28) * 100
    })
    
    # 차트 생성
    fig = px.line(attendance_history, 
                  x='날짜', 
                  y='출근율',
                  color='부서',
                  markers=True,
                  labels={'출근율': '출근율 (%)', '날짜': '날짜'},
                  title='부서별 출근율 추이')
    
    fig.update_layout(
        height=300,
        xaxis_title="날짜",
        yaxis_title="출근율 (%)",
        yaxis_range=[70, 100],
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 구분선
    st.markdown("---")
    
    # 탭 생성: 검사원 등록/목록/관리
    tab1, tab2, tab3 = st.tabs(["📝 검사원 등록", "📋 검사원 목록", "⚙️ 검사원 관리"])
    
    # 탭 1: 검사원 등록
    with tab1:
        st.markdown("### 📝 새 검사원 등록")
        
        with st.form("new_inspector_form", clear_on_submit=True):
        col1, col2 = st.columns([1,1])
        
        with col1:
            inspector_id = st.text_input("🆔 검사원 ID", 
                                       placeholder="검사원 ID를 입력하세요",
                                       help="예: INS001")
            
            name = st.text_input("👤 이름", 
                               placeholder="이름을 입력하세요")
            
            with col2:
            department = st.selectbox("🏢 소속부서", 
                                    options=["CNC_1", "CNC_2", "CDC", "PQC_LINE"],
                                       key="department_select_new")
        
                process = st.text_input("🔧 담당 공정", 
                                    placeholder="담당 공정을 입력하세요",
                                    value=department)
                
            months_of_service = st.number_input(
                "⏳ 근속개월수(M)",
                min_value=0,
                max_value=600,
                value=0,
                step=1,
                help="근속 개월수를 입력하세요"
            )
            
            if months_of_service > 0:
                years = months_of_service // 12
                months = months_of_service % 12
                
                if months_of_service >= 120:  # 10년 이상
                    grade = "🏆 수석"
                    grade_color = "#FFD700"
                elif months_of_service >= 60:  # 5년 이상
                    grade = "🥈 선임"
                    grade_color = "#C0C0C0"
                else:
                    grade = "🥉 사원"
                    grade_color = "#CD7F32"
                
                st.markdown(f"""
                    <div style="
                        background-color: rgba(255,255,255,0.1);
                        padding: 0.5rem;
                        border-radius: 4px;
                        margin-top: 0.5rem;
                    ">
                        <span style="color: {grade_color}; font-weight: bold;">{grade}</span>
                        <span style="color: #666; font-size: 0.9rem; margin-left: 0.5rem;">
                            ({years}년 {months}개월)
                        </span>
                    </div>
                """, unsafe_allow_html=True)
        
        # 저장 버튼
        cols = st.columns([3, 1, 3])
        with cols[1]:
                submitted = st.form_submit_button("💾 등록", type="primary")
        
        if submitted:
            if not inspector_id or not name:
                st.error("⚠️ 필수 항목을 모두 입력해주세요.")
            else:
                    success, message = add_inspector(
                        inspector_id, 
                        name, 
                        department, 
                        process, 
                        months_of_service
                    )
                    
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"⚠️ {message}")
    
    # 탭 2: 검사원 목록
    with tab2:
    st.markdown("### 📋 전체 검사원 목록")
    
        # 검색 기능
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 검사원 이름으로 검색", placeholder="검색어를 입력하세요")
        
        with col2:
            dept_filter = st.selectbox(
                "🏢 부서 필터",
                options=["전체", "CNC_1", "CNC_2", "CDC", "PQC_LINE"],
                index=0
            )
        
        # 검사원 데이터 가져오기
        if search_query:
            inspectors_df = search_inspectors_by_name(search_query)
            if dept_filter != "전체":
                inspectors_df = inspectors_df[inspectors_df['department'] == dept_filter]
        elif dept_filter != "전체":
            inspectors_df = get_inspectors_by_department(dept_filter)
        else:
            inspectors_df = get_inspectors()
        
        if len(inspectors_df) > 0:
            # 표시할 데이터 변환
            display_df = inspectors_df.copy()
            
            # 근속 개월수를 기준으로 등급 계산
            def get_grade(months):
                try:
                    months = float(months)
                    if months >= 120:
                        return "수석"
                    elif months >= 60:
                        return "선임"
                    else:
                        return "사원"
                except (ValueError, TypeError):
                    return "사원"  # 유효하지 않은 값의 경우 기본값 반환
            
            display_df['등급'] = display_df['years_of_service'].apply(get_grade)
            
            # 컬럼 이름 변경
            display_df = display_df.rename(columns={
                'id': '검사원 ID',
                'name': '이름',
                'department': '소속부서',
                'process': '담당공정',
                'years_of_service': '근속개월수'
    })
    
    # 등급별 스타일 적용
    def style_grade(val):
        if val == '수석':
            return 'background-color: #FFD70020; color: #1F2937; font-weight: 500'
        elif val == '선임':
            return 'background-color: #C0C0C020; color: #1F2937; font-weight: 500'
        return 'background-color: #CD7F3220; color: #374151; font-weight: 500'
    
    # 스타일이 적용된 데이터프레임 생성
            styled_df = display_df.style\
        .format({'근속개월수': '{:,.0f}개월'})\
                .applymap(style_grade, subset=['등급'])
    
    # 데이터프레임 표시
    st.dataframe(
        styled_df,
        hide_index=True,
                use_container_width=True,
        column_config={
            "검사원 ID": st.column_config.TextColumn(
                "🆔 검사원 ID",
                width=100,
                help="고유 검사원 식별자"
            ),
            "이름": st.column_config.TextColumn(
                "👤 이름",
                width=100
            ),
            "소속부서": st.column_config.TextColumn(
                "🏢 소속부서",
                width=120
            ),
                    "담당공정": st.column_config.TextColumn(
                        "🔧 담당공정",
                width=120
            ),
            "근속개월수": st.column_config.NumberColumn(
                "⏳ 근속개월수",
                width=100,
                help="검사원 근속 기간(개월)"
            ),
            "등급": st.column_config.TextColumn(
                "🏅 등급",
                width=100,
                help="근속기간 기반 등급"
            )
        }
    )
            
            st.info(f"총 {len(display_df)}명의 검사원이 있습니다.")
        else:
            st.info("💡 등록된 검사원이 없습니다.")
    
    # 탭 3: 검사원 관리
    with tab3:
        st.markdown("### ⚙️ 검사원 정보 수정/삭제")
        
        # 수정할 검사원 선택
        all_inspectors = get_inspectors()
        
        if len(all_inspectors) > 0:
            inspector_options = [f"{row['id']} - {row['name']}" for _, row in all_inspectors.iterrows()]
            inspector_options.insert(0, "검사원을 선택하세요")
            
            selected_inspector = st.selectbox(
                "🔍 수정할 검사원 선택",
                options=inspector_options,
                index=0,
                key="edit_inspector_select"
            )
            
            if selected_inspector != "검사원을 선택하세요":
                inspector_id = selected_inspector.split(" - ")[0]
                inspector_data = get_inspector(inspector_id)
                
                if inspector_data:
                    st.markdown("---")
                    
                    # 수정 폼
                    with st.form("edit_inspector_form"):
                        st.markdown(f"##### 🔄 검사원 ID: {inspector_id} 정보 수정")
                        
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            name = st.text_input(
                                "👤 이름", 
                                value=inspector_data['name'],
                                key="edit_name"
                            )
                            
                            department = st.selectbox(
                                "🏢 소속부서", 
                                options=["CNC_1", "CNC_2", "CDC", "PQC_LINE"],
                                index=["CNC_1", "CNC_2", "CDC", "PQC_LINE"].index(inspector_data['department']),
                                key="edit_department"
                            )
                        
                        with col2:
                            process = st.text_input(
                                "🔧 담당 공정", 
                                value=inspector_data['process'],
                                key="edit_process"
                            )
                            
                            years_of_service = st.number_input(
                                "⏳ 근속개월수(M)",
                                min_value=0,
                                max_value=600,
                                value=int(inspector_data['years_of_service']),
                                step=1,
                                key="edit_years"
                            )
                        
                        col_save, col_del = st.columns([1, 1])
                        with col_save:
                            update_btn = st.form_submit_button("💾 정보 업데이트", type="primary", use_container_width=True)
                        
                        with col_del:
                            delete_btn = st.form_submit_button("🗑️ 검사원 삭제", type="secondary", use_container_width=True)
                        
                        if update_btn:
                            if not name:
                                st.error("⚠️ 이름은 필수 입력 항목입니다.")
                            else:
                                success, message = update_inspector(
                                    inspector_id,
                                    name,
                                    department,
                                    process,
                                    years_of_service
                                )
                                
                                if success:
                                    st.success(f"✅ {message}")
                                    st.rerun()
                                else:
                                    st.error(f"⚠️ {message}")
                        
                        if delete_btn:
                            success, message = delete_inspector(inspector_id)
                            
                            if success:
                                st.success(f"✅ {message}")
                                st.rerun()
                            else:
                                st.error(f"⚠️ {message}")
                else:
                    st.error("⚠️ 검사원 정보를 불러올 수 없습니다.")
        else:
            st.info("💡 등록된 검사원이 없습니다. 먼저 검사원을 등록해주세요.")

# 일일 성과 입력 페이지
def show_daily_performance():
    st.title("📝 일일 성과 입력")
    
    # 공통 카드 스타일 CSS 추가
    st.markdown("""
        <style>
            .input-card {
                background-color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin: 0.8rem 0;
                border: 1px solid #e5e7eb;
                box-shadow: 0 1px 8px rgba(0,0,0,0.05);
                height: 100%;
                transition: all 0.2s ease;
            }
            .input-card:hover {
                box-shadow: 0 3px 12px rgba(0,0,0,0.08);
                transform: translateY(-2px);
            }
            .card-title {
                color: #1e293b;
                font-size: 1.1rem;
                font-weight: 600;
                margin: 0 0 1rem 0;
                display: flex;
                align-items: center;
                border-bottom: 1px solid #f1f5f9;
                padding-bottom: 0.8rem;
            }
            .card-title span {
                margin-right: 0.5rem;
            }
            .card-content {
                padding: 0.2rem 0;
            }
            .card-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
            }
            .card-row {
                margin-bottom: 1rem;
            }
            .disabled-card {
                opacity: 0.7;
                pointer-events: none;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # 기본 정보를 저장할 변수들 (폼 제출 후에도 값을 유지하기 위해)
    if 'temp_inspector_id' not in st.session_state:
        st.session_state.temp_inspector_id = ""
    if 'temp_inspector_name' not in st.session_state:
        st.session_state.temp_inspector_name = ""
    if 'temp_department' not in st.session_state:
        st.session_state.temp_department = "PQC_LINE"
    if 'temp_process' not in st.session_state:
        st.session_state.temp_process = "PQC_LINE"
    if 'temp_inspection_count' not in st.session_state:
        st.session_state.temp_inspection_count = 0
    if 'temp_work_minutes' not in st.session_state:
        st.session_state.temp_work_minutes = 0
    if 'temp_date' not in st.session_state:
        st.session_state.temp_date = datetime.now().date()
    
    # 기본 정보 입력 폼 - 독립 폼으로 분리
    with st.form("basic_info_form", clear_on_submit=False):
        st.markdown("""
            <div class="input-card">
                <h4 class="card-title">
                    <span>🧾</span> 기본 정보 입력
                </h4>
                <div class="card-content">
        """, unsafe_allow_html=True)
        
        # 날짜 선택
        date = st.date_input(
            "📅 날짜 선택", 
            value=st.session_state.temp_date,
            key="date_input",
            help="검사 실적 날짜"
        )
        
        # 검사원 선택 - 드롭다운으로 변경
        # 등록된 검사원 정보 가져오기
        inspectors_df = get_inspectors()
        
        if len(inspectors_df) > 0:
            # 선택 옵션 만들기
            inspector_options = [f"{row['id']} - {row['name']} ({row['department']})" for _, row in inspectors_df.iterrows()]
            inspector_options.insert(0, "검사원을 선택하세요")
            
            selected_inspector = st.selectbox(
                "👤 검사원 선택",
                options=inspector_options,
                index=0 if not st.session_state.temp_inspector_id else 
                     next((i for i, opt in enumerate(inspector_options) 
                          if st.session_state.temp_inspector_id in opt), 0),
                key="inspector_select"
            )
            
            # 선택한 검사원의 정보로 필드 채우기
            if selected_inspector != "검사원을 선택하세요":
                inspector_id = selected_inspector.split(" - ")[0]
                inspector_name = selected_inspector.split(" - ")[1].split(" (")[0]
                department = selected_inspector.split("(")[1].rstrip(")")
                
                # 선택한 검사원 정보 가져오기
                inspector_data = get_inspector(inspector_id)
                
                if inspector_data:
                    # 검사원 정보 표시
                    col1, col2 = st.columns(2)
                    
        with col1:
                        st.markdown(f"""
                            <div style="
                                border: 1px solid #e5e7eb;
                                border-radius: 4px;
                                padding: 0.5rem;
                                margin-bottom: 1rem;
                                background-color: #f8fafc;
                            ">
                                <p style="
                                    margin: 0;
                                    font-size: 0.85rem;
                                    color: #64748b;
                                ">🆔 검사원 ID</p>
                                <p style="
                                    margin: 0;
                                    font-weight: 500;
                                    font-size: 0.95rem;
                                ">{inspector_data['id']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        process = inspector_data['process']
        
        with col2:
                        st.markdown(f"""
                            <div style="
                                border: 1px solid #e5e7eb;
                                border-radius: 4px;
                                padding: 0.5rem;
                                margin-bottom: 1rem;
                                background-color: #f8fafc;
                            ">
                                <p style="
                                    margin: 0;
                                    font-size: 0.85rem;
                                    color: #64748b;
                                ">🏢 소속 부서</p>
                                <p style="
                                    margin: 0;
                                    font-weight: 500;
                                    font-size: 0.95rem;
                                ">{inspector_data['department']}</p>
                            </div>
                        """, unsafe_allow_html=True)
                
                # 세션 상태 업데이트
                st.session_state.temp_inspector_id = inspector_id
                st.session_state.temp_inspector_name = inspector_name
                st.session_state.temp_department = department
                st.session_state.temp_process = process
            else:
                st.session_state.temp_inspector_id = ""
                st.session_state.temp_inspector_name = ""
                st.session_state.temp_department = "PQC_LINE"
                st.session_state.temp_process = "PQC_LINE"
                
                # 검사원이 선택되지 않았을 때 경고 메시지
                st.warning("검사원을 선택해주세요.")
        else:
            st.error("등록된 검사원이 없습니다. 먼저 검사원 관리에서 검사원을 등록해주세요.")
            st.session_state.temp_inspector_id = ""
            st.session_state.temp_inspector_name = ""
        
        # 검사 수량 입력
        col1, col2 = st.columns(2)
        with col1:
        inspection_count = st.number_input(
            "📦 총 검사 수량", 
            min_value=0,
                value=st.session_state.temp_inspection_count,
            step=1,
                key="inspection_count_input",
                help="실시한 총 검사 수량"
            )
        
        with col2:
            work_minutes = st.number_input(
                "⏱️ 작업시간(분)",
                min_value=0,
                value=st.session_state.temp_work_minutes,
                step=5,
                help="총 작업 시간 (분 단위)",
                key="work_minutes_input"
            )
            
            # 시간 변환 표시 (분->시간)
            if work_minutes > 0:
                hours = work_minutes // 60
                mins = work_minutes % 60
                st.markdown(f"""
                    <div style="
                        font-size: 0.8rem; 
                        color: #4b5563;
                        margin-top: -1rem;
                    ">
                        ≈ {hours}시간 {mins}분
                    </div>
                """, unsafe_allow_html=True)
        
        st.markdown('</div></div>', unsafe_allow_html=True)
        
        # 저장 버튼
        submitted_basic = st.form_submit_button(
            "✅ 정보 확인",
            type="primary",
            use_container_width=True
        )
    
    # 입력값 임시 저장
    st.session_state.temp_date = date
    st.session_state.temp_inspection_count = inspection_count
    st.session_state.temp_work_minutes = work_minutes
    
    # 기본 정보 유효성 검사
    if submitted_basic:
        if not st.session_state.temp_inspector_id or not st.session_state.temp_inspector_name:
            st.error("⚠️ 검사원을 선택해주세요.")
        elif work_minutes <= 0:
            st.error("⚠️ 작업 시간을 입력해주세요.")
        elif inspection_count <= 0:
            st.error("⚠️ 검사 수량을 입력해주세요.")
        else:
            st.session_state.basic_info_valid = True
            st.success("✅ 기본 정보가 확인되었습니다. 이제 불량 정보를 등록해주세요.")
            
    # 불량 정보 입력 폼 - 기본 정보가 유효할 때만 활성화
    defect_info_disabled = not st.session_state.get('basic_info_valid', False)
    
    # 불량 등록 폼 - 별도의 폼으로 분리
    if not defect_info_disabled:
        st.markdown("""
            <div style="
                background-color: white;
                padding: 1.5rem;
                border-radius: 10px;
                margin: 1rem 0;
                border: 1px solid #e5e7eb;
                box-shadow: 0 1px 8px rgba(0,0,0,0.05);
            ">
                <h4 style="
                    color: #1e293b;
                    font-size: 1.1rem;
                    font-weight: 600;
                    margin: 0 0 1rem 0;
                    display: flex;
                    align-items: center;
                    border-bottom: 1px solid #f1f5f9;
                    padding-bottom: 0.8rem;
                ">
                    <span style="margin-right: 0.5rem;">🔍</span> 불량 정보 입력
                </h4>
            </div>
        """, unsafe_allow_html=True)
        
        # 불량 등록 성공 메시지 표시 (폼 외부)
        if 'defect_registered' in st.session_state and st.session_state.defect_registered:
            defect_type = st.session_state.last_defect_type
            defect_qty = st.session_state.last_defect_qty
            st.success(f"✅ {defect_type} {defect_qty}개가 불량 목록에 추가되었습니다.")
            # 메시지 표시 후 플래그 초기화
            st.session_state.defect_registered = False
        
        # 불량 유형 등록 폼
        with st.form("defect_register_form"):
            # 2열 그리드 레이아웃
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            new_defect_type = st.selectbox(
                "불량 유형 선택",
                options=["선택하세요"] + sorted(st.session_state.defect_types),
                    index=0,
                    key="new_defect_type_select"
            )
        
        with col2:
            new_defect_qty = st.number_input(
                "불량 수량",
                min_value=1,
                value=1,
                step=1,
                    key="new_defect_qty_input"
            )
        
        with col3:
                # 불량 등록 버튼 - form_submit_button 사용 (새로운 조건으로 활성화)
                # 불량 유형만 선택되면 활성화되도록 수정
                register_disabled = new_defect_type == "선택하세요"
                register_btn = st.form_submit_button(
                    "불량 등록",
                type="secondary",
                    disabled=register_disabled,
                use_container_width=True
                )
        
        # 폼 처리 로직 - 폼 외부에 위치
        if register_btn and new_defect_type != "선택하세요":
            # 불량 정보 등록
                    new_defect = {
                "불량유형": new_defect_type,
                        "수량": new_defect_qty
                    }
            
            # 등록된 불량 목록이 없으면 초기화
            if 'registered_defects' not in st.session_state:
                st.session_state.registered_defects = []
            
            # 불량 정보 등록
                    st.session_state.registered_defects.append(new_defect)
            
            # 성공 메시지 표시를 위한 상태 설정
            st.session_state.defect_registered = True
            st.session_state.last_defect_type = new_defect_type
            st.session_state.last_defect_qty = new_defect_qty
            
            # 페이지 새로고침
                    st.rerun()
        
        # 등록된 불량 목록 표시
        if 'registered_defects' in st.session_state and len(st.session_state.registered_defects) > 0:
            st.markdown("#### 📋 등록된 불량 목록")
            
            # 불량 정보를 데이터프레임으로 변환
            defects_df = pd.DataFrame(st.session_state.registered_defects)
            
            # 불량 유형별 합계 계산 (같은 유형의 불량이 여러 개 있을 경우 합산)
            defects_sum = defects_df.groupby('불량유형')['수량'].sum().reset_index()
            
            # 데이터프레임 표시
            st.dataframe(
                defects_sum,
                hide_index=True,
                use_container_width=True,
                height=200,
                column_config={
                    "불량유형": st.column_config.TextColumn("불량 유형", width=200),
                    "수량": st.column_config.NumberColumn("수량", width=100)
                }
            )
            
            # 전체 불량 수량
            total_defects = defects_sum["수량"].sum()
            
            # 불량률 계산
            inspection_count = st.session_state.temp_inspection_count
            defect_rate = (total_defects / inspection_count * 100) if inspection_count > 0 else 0
            
            # 불량률 표시
                st.markdown(f"""
                <div style="
                    background-color: #f8fafc;
                        border-radius: 5px;
                    padding: 1rem;
                    margin: 1rem 0;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    border: 1px solid #e5e7eb;
                ">
                    <div>
                        <span style="font-size: 0.9rem; color: #64748b;">총 불량 수량:</span>
                        <span style="font-weight: 600; margin-left: 0.5rem; font-size: 1.1rem;">{total_defects}</span>
                    </div>
                    <div>
                        <span style="font-size: 0.9rem; color: #64748b;">불량률:</span>
                        <span style="
                            font-weight: 600; 
                            margin-left: 0.5rem;
                            font-size: 1.1rem;
                            color: {'#059669' if defect_rate < 1 else '#ea580c' if defect_rate < 3 else '#dc2626'};
                        ">{defect_rate:.2f}%</span>
                    </div>
                    </div>
                """, unsafe_allow_html=True)
            
            # 불량 목록 초기화 버튼 - 폼 외부에 위치
            col1, col2 = st.columns([3, 1])
                with col2:
                if st.button("불량 목록 초기화", type="secondary", use_container_width=True):
                    st.session_state.registered_defects = []
                    st.rerun()
        else:
            st.info("등록된 불량이 없습니다. 위에서 불량 정보를 추가해주세요.")
        
        # 저장 폼
        with st.form("save_data_form"):
            st.markdown("### 💾 검사 데이터 저장")
            # 저장 버튼
            submit_disabled = len(st.session_state.get('registered_defects', [])) == 0
            submit_btn = st.form_submit_button(
                "검사 데이터 저장",
                type="primary",
                use_container_width=True,
                disabled=submit_disabled
            )
            
            # 폼 제출 시 동작
            if submit_btn and not submit_disabled:
                # 입력 데이터 수집
                inspector_id = st.session_state.temp_inspector_id
                date = st.session_state.temp_date
                department = st.session_state.temp_department
                process = st.session_state.temp_process
                inspection_count = st.session_state.temp_inspection_count
                work_minutes = st.session_state.temp_work_minutes
                
                # 불량 정보 수집
                defect_info = {}
                for defect in st.session_state.registered_defects:
                    defect_type = defect["불량유형"]
                    count = defect["수량"]
                    
                    if defect_type in defect_info:
                        defect_info[defect_type] += count
        else:
                        defect_info[defect_type] = count
                
                # 데이터 저장
                if add_daily_performance(
                    inspector_id, date, department, process, 
                    inspection_count, work_minutes, defect_info
                ):
                    # 저장 성공
                    st.success("✅ 일일 성과가 성공적으로 저장되었습니다!")
                    
                    # 입력 필드 초기화
                    st.session_state.basic_info_valid = False
                    st.session_state.temp_inspector_id = ""
                    st.session_state.temp_inspector_name = ""
                    st.session_state.temp_department = "PQC_LINE"
                    st.session_state.temp_process = "PQC_LINE"
                    st.session_state.temp_inspection_count = 0
                    st.session_state.temp_work_minutes = 0
            st.session_state.registered_defects = []
                        
                    # 페이지 새로고침
            st.rerun()
                else:
                    # 저장 실패
                    st.error("❌ 데이터 저장 중 오류가 발생했습니다. 다시 시도해주세요.")
                    
    else:
        st.info("📝 기본 정보를 먼저 입력하고 '정보 확인' 버튼을 눌러주세요.")

# 사용자 관리 페이지 추가
def show_user_management():
    if st.session_state.user_role != "admin":
        st.error("관리자 권한이 필요합니다.")
        return
        
    st.title("사용자 관리")
    
    # 새 사용자 등록 섹션
    st.markdown("""
        <div style="margin: 2rem 0 1rem 0">
            <h3 style="
                color: #1e293b;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
            ">
                👤 새 사용자 등록
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("new_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("이메일", placeholder="example@email.com")
            new_password = st.text_input("비밀번호", type="password")
        with col2:
            user_role = st.selectbox("권한", ["user", "admin"])
            user_name = st.text_input("이름", placeholder="사용자 이름")
        
        if st.form_submit_button("사용자 등록", use_container_width=True):
            if not new_username or not new_password or not user_name:
                st.error("모든 필드를 입력해주세요.")
            else:
                # 여기에 실제 사용자 등록 로직 추가
                st.success(f"✅ {user_name}님이 {user_role} 권한으로 등록되었습니다!")

    # 구분선
    st.markdown("---")
    
    # 사용자 목록 표시
    st.markdown("""
        <div style="margin: 2rem 0 1rem 0">
            <h3 style="
                color: #1e293b;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
            ">
                👥 사용자 목록
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    # 샘플 사용자 데이터
    users_data = {
        '이메일': ['dlwjddyd83@gmail.com', 'user@example.com', 'test@example.com'],
        '이름': ['관리자', '일반사용자1', '일반사용자2'],
        '권한': ['admin', 'user', 'user'],
        '등록일': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        '최근 접속': pd.to_datetime(['2024-01-15', '2024-01-14', '2024-01-13'])
    }
    df = pd.DataFrame(users_data)
    
    # 사용자 목록 표시
    edited_df = st.data_editor(
        df,
        hide_index=True,
        column_config={
            "이메일": st.column_config.TextColumn(
                "이메일",
                width=200,
                help="사용자 로그인 이메일"
            ),
            "이름": st.column_config.TextColumn(
                "이름",
                width=100
            ),
            "권한": st.column_config.SelectboxColumn(
                "권한",
                width=100,
                options=["admin", "user"],
                help="사용자 권한 레벨"
            ),
            "등록일": st.column_config.DatetimeColumn(
                "등록일",
                width=100,
                format="YYYY-MM-DD"
            ),
            "최근 접속": st.column_config.DatetimeColumn(
                "최근 접속",
                width=100,
                format="YYYY-MM-DD"
            )
        },
        num_rows="dynamic"
    )
    
    # 삭제 기능
    if st.button("선택된 사용자 삭제", type="primary"):
        st.warning("⚠️ 선택된 사용자를 삭제하시겠습니까?")
        col1, col2 = st.columns([1,4])
        with col1:
            if st.button("확인", type="primary"):
                st.success("✅ 선택된 사용자가 삭제되었습니다.")

# 사용자 관리 페이지 추가
def show_staff_status():
    if st.session_state.user_role != "admin":
        st.error("관리자 권한이 필요합니다.")
        return
        
    st.title("사용자 관리")
    
    # 새 사용자 등록 섹션
    st.markdown("""
        <div style="margin: 2rem 0 1rem 0">
            <h3 style="
                color: #1e293b;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
            ">
                👤 새 사용자 등록
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    with st.form("new_user_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_username = st.text_input("이메일", placeholder="example@email.com")
            new_password = st.text_input("비밀번호", type="password")
        with col2:
            user_role = st.selectbox("권한", ["user", "admin"])
            user_name = st.text_input("이름", placeholder="사용자 이름")
        
        if st.form_submit_button("사용자 등록", use_container_width=True):
            if not new_username or not new_password or not user_name:
                st.error("모든 필드를 입력해주세요.")
            else:
                # 여기에 실제 사용자 등록 로직 추가
                st.success(f"✅ {user_name}님이 {user_role} 권한으로 등록되었습니다!")

    # 구분선
    st.markdown("---")
    
    # 사용자 목록 표시
    st.markdown("""
        <div style="margin: 2rem 0 1rem 0">
            <h3 style="
                color: #1e293b;
                font-size: 1.2rem;
                font-weight: 600;
                margin-bottom: 1rem;
            ">
                👥 사용자 목록
            </h3>
        </div>
    """, unsafe_allow_html=True)
    
    # 샘플 사용자 데이터
    users_data = {
        '이메일': ['dlwjddyd83@gmail.com', 'user@example.com', 'test@example.com'],
        '이름': ['관리자', '일반사용자1', '일반사용자2'],
        '권한': ['admin', 'user', 'user'],
        '등록일': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03']),
        '최근 접속': pd.to_datetime(['2024-01-15', '2024-01-14', '2024-01-13'])
    }
    df = pd.DataFrame(users_data)
    
    # 사용자 목록 표시
    edited_df = st.data_editor(
        df,
        hide_index=True,
        column_config={
            "이메일": st.column_config.TextColumn(
                "이메일",
                width=200,
                help="사용자 로그인 이메일"
            ),
            "이름": st.column_config.TextColumn(
                "이름",
                width=100
            ),
            "권한": st.column_config.SelectboxColumn(
                "권한",
                width=100,
                options=["admin", "user"],
                help="사용자 권한 레벨"
            ),
            "등록일": st.column_config.DatetimeColumn(
                "등록일",
                width=100,
                format="YYYY-MM-DD"
            ),
            "최근 접속": st.column_config.DatetimeColumn(
                "최근 접속",
                width=100,
                format="YYYY-MM-DD"
            )
        },
        num_rows="dynamic"
    )
    
    # 삭제 기능
    if st.button("선택된 사용자 삭제", type="primary"):
        st.warning("⚠️ 선택된 사용자를 삭제하시겠습니까?")
        col1, col2 = st.columns([1,4])
        with col1:
            if st.button("확인", type="primary"):
                st.success("✅ 선택된 사용자가 삭제되었습니다.")

# 리포트 페이지
def show_report():
    st.title("📊 KPI 리포트")
    
    # 데이터 로드
    data = load_inspection_data()
    df = pd.DataFrame(data["inspections"])
    
    if df.empty:
        st.warning("⚠️ 저장된 검사 데이터가 없습니다.")
        return
    
    # 날짜 컬럼을 datetime으로 변환
    df['날짜'] = pd.to_datetime(df['날짜'])
    
    # 리포트 유형 선택
    report_type = st.radio(
        "📅 리포트 유형",
        options=["월간 리포트", "주간 리포트"],
        horizontal=True,
        key="report_type"
    )
    
    # 기간 선택
    col1, col2 = st.columns([1, 3])
    with col1:
        if report_type == "월간 리포트":
            default_date = datetime.now().replace(day=1)
            selected_date = st.date_input(
                "월 선택",
                value=default_date,
                format="YYYY/MM/DD"
            )
            start_date = selected_date.replace(day=1)
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            period = selected_date.strftime("%Y년 %m월")
        else:
            today = datetime.now()
            monday = today - timedelta(days=today.weekday())
            selected_date = st.date_input(
                "주 선택",
                value=monday,
                format="YYYY/MM/DD"
            )
            # 선택된 날짜의 주의 시작일과 종료일 계산
            week_start = selected_date - timedelta(days=selected_date.weekday())
            week_end = week_start + timedelta(days=6)
            start_date = week_start  # 이미 date 객체이므로 그대로 사용
            end_date = week_end  # 이미 date 객체이므로 그대로 사용
            period = f"{week_start.strftime('%Y년 %m월 %d일')} ~ {week_end.strftime('%m월 %d일')}"

    # 선택된 기간의 데이터 필터링
    mask = (df['날짜'].dt.date >= start_date) & (df['날짜'].dt.date <= end_date)
    period_df = df[mask]
    
    if period_df.empty:
        st.warning(f"⚠️ {period} 기간의 데이터가 없습니다.")
        return

    st.markdown(f"### 📈 {period} 실적 현황")
    
    # KPI 지표 계산
    total_inspections = period_df['검사수량'].sum()
    total_defects = period_df['불량수량'].sum()
    avg_defect_rate = (total_defects / total_inspections * 100) if total_inspections > 0 else 0
    avg_efficiency = period_df['효율'].mean()
    inspector_count = period_df['검사원ID'].nunique()
    
    # 이전 기간과 비교를 위한 데이터 준비
    if report_type == "월간 리포트":
        prev_start = start_date - timedelta(days=start_date.day)
        prev_end = start_date - timedelta(days=1)
    else:
        prev_start = start_date - timedelta(days=7)
        prev_end = start_date - timedelta(days=1)
    
    prev_mask = (df['날짜'].dt.date >= prev_start) & (df['날짜'].dt.date <= prev_end)
    prev_df = df[prev_mask]
    
    # 이전 기간 KPI 계산
    if not prev_df.empty:
        prev_inspections = prev_df['검사수량'].sum()
        prev_defects = prev_df['불량수량'].sum()
        prev_defect_rate = (prev_defects / prev_inspections * 100) if prev_inspections > 0 else 0
        prev_efficiency = prev_df['효율'].mean()
        prev_inspector_count = prev_df['검사원ID'].nunique()
        
        # 증감 계산
        inspection_delta = total_inspections - prev_inspections
        defect_rate_delta = avg_defect_rate - prev_defect_rate
        efficiency_delta = avg_efficiency - prev_efficiency
        inspector_delta = inspector_count - prev_inspector_count
    else:
        inspection_delta = defect_rate_delta = efficiency_delta = inspector_delta = None

    # KPI 지표 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📦 총 검사량",
            value=f"{total_inspections:,}개",
            delta=f"{inspection_delta:+,}개" if inspection_delta is not None else None,
            delta_color="inverse"
        )
    
    with col2:
        st.metric(
            label="⚠️ 평균 불량률",
            value=f"{avg_defect_rate:.1f}%",
            delta=f"{defect_rate_delta:+.1f}%" if defect_rate_delta is not None else None,
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            label="⚡ 평균 효율",
            value=f"{avg_efficiency:.1f}%",
            delta=f"{efficiency_delta:+.1f}%" if efficiency_delta is not None else None,
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="👥 검사원 수",
            value=f"{inspector_count}명",
            delta=f"{inspector_delta:+d}명" if inspector_delta is not None else None,
            delta_color="inverse"
        )

    # 차트 영역
    st.markdown("---")
    col1, col2 = st.columns([1.8, 1])
    
    with col1:
        st.markdown("#### 📊 일별 검사량 및 불량률 추이")
        
        # 일별 데이터 집계
        daily_data = period_df.groupby(period_df['날짜'].dt.date).agg({
            '검사수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        daily_data['불량률'] = (daily_data['불량수량'] / daily_data['검사수량'] * 100).round(2)
        
        # 차트 생성
        fig = go.Figure()
        
        # 검사량 바 차트
        fig.add_trace(go.Bar(
            x=daily_data['날짜'],
            y=daily_data['검사수량'],
            name='검사량',
            marker_color='rgba(59, 130, 246, 0.7)',
            hovertemplate='검사량: %{y:,.0f}개<br>날짜: %{x|%Y-%m-%d}<extra></extra>'
        ))
        
        # 불량률 라인 차트
        fig.add_trace(go.Scatter(
            x=daily_data['날짜'],
            y=daily_data['불량률'],
            name='불량률',
            line=dict(color='#EF4444', width=3),
            mode='lines+markers',
            marker=dict(
                size=8,
                symbol='circle',
                line=dict(color='white', width=2)
            ),
            yaxis='y2',
            hovertemplate='불량률: %{y:.1f}%<br>날짜: %{x|%Y-%m-%d}<extra></extra>'
        ))
        
        # 레이아웃 설정
        fig.update_layout(
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            yaxis=dict(
                title='검사량(개)',
                titlefont=dict(color='#3B82F6', size=13),
                tickfont=dict(color='#3B82F6'),
                gridcolor='rgba(0,0,0,0.1)',
                showgrid=True
            ),
            yaxis2=dict(
                title='불량률(%)',
                titlefont=dict(color='#EF4444', size=13),
                tickfont=dict(color='#EF4444'),
                overlaying='y',
                side='right',
                showgrid=False
            ),
            xaxis=dict(
                title='날짜',
                titlefont=dict(size=13),
                tickformat='%m/%d',
                gridcolor='rgba(0,0,0,0.1)',
                showgrid=True
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            margin=dict(l=60, r=60, t=80, b=40),
            bargap=0.3,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("#### 🎯 공정별 불량률 분포")
        
        # 공정별 불량률 계산
        process_data = period_df.groupby('공정').agg({
            '검사수량': 'sum',
            '불량수량': 'sum'
        }).reset_index()
        
        process_data['불량률'] = (process_data['불량수량'] / process_data['검사수량'] * 100).round(2)
        
        # 도넛 차트 생성
        fig = go.Figure(data=[go.Pie(
            labels=process_data['공정'],
            values=process_data['불량률'],
            hole=.4,
            marker_colors=['#60A5FA', '#34D399', '#A78BFA', '#F59E0B']
        )])
        
        # 레이아웃 설정
        fig.update_layout(
            height=350,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)

# 데이터베이스 초기화 후, 검사원 관련 함수들 추가
# 검사원 데이터 조회 함수
def get_inspectors():
    """
    모든 검사원 정보를 조회하는 함수
    
    Returns:
        pd.DataFrame: 검사원 정보가 담긴 데이터프레임
    """
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect('inspection_data.db')
        
        # 쿼리 실행 및 데이터프레임 변환
        query = "SELECT id, name, department, process, years_of_service FROM inspectors"
        df = pd.read_sql_query(query, conn)
        
        # 연결 종료
        conn.close()
        
        if len(df) == 0:
            print("등록된 검사원이 없습니다.")
        else:
            print(f"총 {len(df)}명의 검사원 정보를 불러왔습니다.")
            
        return df
        
    except Exception as e:
        print(f"검사원 정보 조회 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 빈 데이터프레임 반환
        return pd.DataFrame(columns=['id', 'name', 'department', 'process', 'years_of_service'])

# 검사원 추가 함수
def add_inspector(inspector_id, name, department, process="", years_of_service=0):
    try:
        # 기본값 및 타입 변환 처리
        if not process:
            process = department
        
        try:
            years_of_service = float(years_of_service)
        except (ValueError, TypeError):
            years_of_service = 0.0
            
        conn = sqlite3.connect('inspection_data.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO inspectors (id, name, department, process, years_of_service)
            VALUES (?, ?, ?, ?, ?)
        ''', (inspector_id, name, department, process, years_of_service))
        conn.commit()
        conn.close()
        print(f"검사원 추가 성공: {inspector_id} - {name}")
        return True, "검사원이 성공적으로 추가되었습니다."
    except sqlite3.IntegrityError:
        print(f"검사원 추가 실패 (중복): {inspector_id}")
        return False, "이미 존재하는 검사원 ID입니다."
    except Exception as e:
        print(f"검사원 추가 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"검사원 추가 중 오류가 발생했습니다: {str(e)}"

# 검사원 업데이트 함수
def update_inspector(inspector_id, name, department, process="", years_of_service=0):
    try:
        # 기본값 및 타입 변환 처리
        if not process:
            process = department
        
        try:
            years_of_service = float(years_of_service)
        except (ValueError, TypeError):
            years_of_service = 0.0
            
        conn = sqlite3.connect('inspection_data.db')
        c = conn.cursor()
        c.execute('''
            UPDATE inspectors 
            SET name=?, department=?, process=?, years_of_service=?
            WHERE id=?
        ''', (name, department, process, years_of_service, inspector_id))
        conn.commit()
        conn.close()
        print(f"검사원 정보 업데이트 성공: {inspector_id} - {name}")
        return True, "검사원 정보가 업데이트되었습니다."
    except Exception as e:
        print(f"검사원 업데이트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"검사원 업데이트 중 오류가 발생했습니다: {str(e)}"

# 검사원 삭제 함수
def delete_inspector(inspector_id):
    try:
        conn = sqlite3.connect('inspection_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM inspectors WHERE id=?', (inspector_id,))
        conn.commit()
        conn.close()
        print(f"검사원 삭제 성공: {inspector_id}")
        return True, "검사원이 삭제되었습니다."
    except Exception as e:
        print(f"검사원 삭제 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return False, f"검사원 삭제 중 오류가 발생했습니다: {str(e)}"

# 특정 검사원 조회 함수
def get_inspector(inspector_id):
    try:
        conn = sqlite3.connect('inspection_data.db')
        c = conn.cursor()
        c.execute('SELECT id, name, department, process, years_of_service FROM inspectors WHERE id=?', (inspector_id,))
        result = c.fetchone()
        conn.close()
        if result:
            print(f"검사원 조회 성공: {inspector_id}")
            return {
                'id': result[0],
                'name': result[1],
                'department': result[2],
                'process': result[3],
                'years_of_service': result[4]
            }
        print(f"검사원 조회 결과 없음: {inspector_id}")
        return None
    except Exception as e:
        print(f"검사원 조회 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# 검사원 이름으로 검색하는 함수
def search_inspectors_by_name(name_query):
    try:
        conn = sqlite3.connect('inspection_data.db')
        query = "SELECT id, name, department, process, years_of_service FROM inspectors WHERE name LIKE ? ORDER BY name"
        inspectors_df = pd.read_sql_query(query, conn, params=[f'%{name_query}%'])
        conn.close()
        print(f"검사원 이름 검색 성공: '{name_query}' - {len(inspectors_df)}명 찾음")
        return inspectors_df
    except Exception as e:
        print(f"검사원 이름 검색 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['id', 'name', 'department', 'process', 'years_of_service'])

# 부서별 검사원 목록 조회 함수
def get_inspectors_by_department(department):
    try:
        conn = sqlite3.connect('inspection_data.db')
        query = "SELECT id, name, department, process, years_of_service FROM inspectors WHERE department=? ORDER BY name"
        inspectors_df = pd.read_sql_query(query, conn, params=[department])
        conn.close()
        print(f"부서별 검사원 조회 성공: {department} - {len(inspectors_df)}명")
        return inspectors_df
    except Exception as e:
        print(f"부서별 검사원 조회 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame(columns=['id', 'name', 'department', 'process', 'years_of_service'])

# 불량 정보 및 최종 저장 부분 수정
def add_daily_performance(inspector_id, date, department, process, inspection_count, work_minutes, defect_info=None):
    """
    일일 검사 성과를 데이터베이스에 저장하는 함수
    
    Args:
        inspector_id (str): 검사원 ID
        date (date): 검사 일자
        department (str): 부서명
        process (str): 공정명
        inspection_count (int): 검사 수량
        work_minutes (int): 작업 시간(분)
        defect_info (dict, optional): 불량 정보 (유형별 수량)
        
    Returns:
        bool: 저장 성공 여부
    """
    conn = None
    try:
        # 데이터베이스 연결
        conn = sqlite3.connect('inspection_data.db')
        cursor = conn.cursor()
        
        # 기본 정보 저장 쿼리
        cursor.execute("""
        INSERT INTO inspection_data 
        (inspector_id, date, department, process, inspection_count, work_minutes) 
        VALUES (?, ?, ?, ?, ?, ?)
        """, (inspector_id, date.strftime('%Y-%m-%d'), department, process, inspection_count, work_minutes))
        
        # 저장된 기본 정보의 ID 가져오기
        inspection_id = cursor.lastrowid
        print(f"기본 정보 저장 성공 (ID: {inspection_id})")
        
        # 불량 정보가 있는 경우 저장
        if defect_info and len(defect_info) > 0:
            try:
                for defect_type, count in defect_info.items():
                    if count > 0:
                        cursor.execute("""
                        INSERT INTO defect_data 
                        (inspection_id, defect_type, count) 
                        VALUES (?, ?, ?)
                        """, (inspection_id, defect_type, count))
                        
                print(f"불량 정보 저장 성공")
            except Exception as defect_error:
                print(f"불량 정보 저장 중 오류 발생: {str(defect_error)}")
                # 불량 정보 저장 실패 시에도 기본 정보는 유지
        
        # 변경사항 저장 및 연결 종료
        conn.commit()
        print("모든 데이터 저장 완료")
        
        return True
    
    except Exception as e:
        print(f"일일 성과 저장 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 오류 발생 시 변경사항 롤백
        try:
            if conn:
                conn.rollback()
        except Exception as rollback_error:
            print(f"롤백 중 오류 발생: {str(rollback_error)}")
        
        return False
    
    finally:
        # 연결 종료
        try:
            if conn:
                conn.close()
        except Exception as close_error:
            print(f"연결 종료 중 오류 발생: {str(close_error)}")

def get_defect_counts_by_date(start_date, end_date=None):
    """
    지정된 날짜 범위 내의 불량 데이터를 가져오는 함수
    
    Args:
        start_date (date): 시작 날짜
        end_date (date, optional): 종료 날짜. 지정하지 않으면 시작 날짜와 동일
        
    Returns:
        pd.DataFrame: 날짜별 불량 데이터
    """
    try:
        if end_date is None:
            end_date = start_date
            
        # 데이터베이스 연결
        conn = sqlite3.connect('inspection_data.db')
        
        # 쿼리 실행
        query = """
        SELECT 
            i.date,
            d.defect_type,
            SUM(d.count) as total_count
        FROM 
            inspection_data i
        JOIN 
            defect_data d ON i.id = d.inspection_id
        WHERE 
            i.date BETWEEN ? AND ?
        GROUP BY 
            i.date, d.defect_type
        ORDER BY 
            i.date, d.defect_type
        """
        
        # 데이터프레임으로 변환
        df = pd.read_sql_query(
            query, 
            conn, 
            params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
        )
        
        conn.close()
        
        # 결과가 없으면 빈 데이터프레임 반환
        if len(df) == 0:
            return pd.DataFrame(columns=['date', 'defect_type', 'total_count'])
            
        return df
        
    except Exception as e:
        print(f"데이터 조회 중 오류 발생: {str(e)}")
        return pd.DataFrame(columns=['date', 'defect_type', 'total_count'])

# 데이터베이스 관련 함수들
def save_data(file_path, data):
    """데이터를 JSON 파일로 저장"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    except Exception as e:
        st.error(f"데이터 저장 중 오류가 발생했습니다: {str(e)}")

def load_data(file_path, default_data):
    """JSON 파일에서 데이터 로드"""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_data
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {str(e)}")
        return default_data

def get_inspectors():
    """모든 검사원 정보 조회"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    return pd.DataFrame(data["inspectors"])

def add_inspector(inspector_data):
    """새로운 검사원 추가"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    data["inspectors"].append(inspector_data)
    save_data(INSPECTOR_DATA_FILE, data)
    return True, "검사원이 성공적으로 등록되었습니다."

def update_inspector(inspector_id, updated_data):
    """검사원 정보 업데이트"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    for inspector in data["inspectors"]:
        if inspector["id"] == inspector_id:
            inspector.update(updated_data)
            save_data(INSPECTOR_DATA_FILE, data)
            return True, "검사원 정보가 성공적으로 업데이트되었습니다."
    return False, "해당 ID의 검사원을 찾을 수 없습니다."

def delete_inspector(inspector_id):
    """검사원 삭제"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    data["inspectors"] = [i for i in data["inspectors"] if i["id"] != inspector_id]
    save_data(INSPECTOR_DATA_FILE, data)
    return True, "검사원이 성공적으로 삭제되었습니다."

def get_inspector(inspector_id):
    """특정 검사원 정보 조회"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    for inspector in data["inspectors"]:
        if inspector["id"] == inspector_id:
            return inspector
    return None

def search_inspectors_by_name(name):
    """이름으로 검사원 검색"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    matching_inspectors = [i for i in data["inspectors"] if name.lower() in i["name"].lower()]
    return pd.DataFrame(matching_inspectors)

def get_inspectors_by_department(department):
    """부서별 검사원 조회"""
    data = load_data(INSPECTOR_DATA_FILE, {"inspectors": []})
    department_inspectors = [i for i in data["inspectors"] if i["department"] == department]
    return pd.DataFrame(department_inspectors)

def save_inspection(inspection_data):
    """검사 데이터 저장"""
    data = load_data(INSPECTION_DATA_FILE, {"inspections": []})
    data["inspections"].append(inspection_data)
    save_data(INSPECTION_DATA_FILE, data)
if __name__ == "__main__":
    # 메인 앱 실행
    main() 