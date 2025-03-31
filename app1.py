import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
import json
from pathlib import Path
import os
import threading

# 페이지 설정을 가장 먼저 실행
st.set_page_config(
    page_title="CNC 품질관리 시스템", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/leejungyong83/CNC_QC_KPI',
        'Report a bug': 'https://github.com/leejungyong83/CNC_QC_KPI/issues',
        'About': '# CNC 품질관리 시스템\n 품질 데이터 수집 및 분석을 위한 앱입니다.'
    }
)

# 카드 스타일 CSS 추가
st.markdown("""
<style>
    .card {
        border-radius: 12px;
        padding: 22px;
        background-color: white;
        box-shadow: 0 6px 10px rgba(0, 0, 0, 0.08);
        margin-bottom: 24px;
        border-top: 4px solid #4e8df5;
        transition: transform 0.3s;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .metric-card {
        border-radius: 10px;
        padding: 18px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.06);
        text-align: center;
        border-left: 5px solid #4e8df5;
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
    }
    .title-area {
        padding: 12px 0;
        margin-bottom: 24px;
        border-bottom: 2px solid #f0f2f5;
    }
    .sub-text {
        color: #637381;
        font-size: 14px;
        margin-top: 4px;
    }
    .dashboard-divider {
        height: 24px;
    }
    .emoji-title {
        font-size: 24px;
        font-weight: 600;
        margin-bottom: 12px;
        color: #1f2937;
    }
    .emoji-icon {
        font-size: 22px;
        margin-right: 8px;
        vertical-align: middle;
    }
    /* 각 지표별 색상 */
    .blue-indicator {
        border-left-color: #4361ee;
    }
    .green-indicator {
        border-left-color: #4cb782;
    }
    .orange-indicator {
        border-left-color: #fb8c00;
    }
    .purple-indicator {
        border-left-color: #7c3aed;
    }
    
    /* 사이드바 스타일 추가 */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);
        color: white;
        padding-top: 20px;
        padding-bottom: 20px;
        box-shadow: 2px 0px 10px rgba(0, 0, 0, 0.2);
    }
    
    .sidebar .sidebar-content .stRadio > label {
        color: white;
        font-weight: 600;
        margin-bottom: 12px;
        font-size: 1.05rem;
        letter-spacing: 0.5px;
    }
    
    .sidebar .sidebar-content .stRadio > div {
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 18px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .sidebar .sidebar-content .stRadio > div > label {
        color: rgba(255, 255, 255, 0.9);
        transition: all 0.3s ease;
        padding: 8px 10px;
        border-radius: 8px;
        font-weight: 500;
    }
    
    .sidebar .sidebar-content .stRadio > div > label:hover {
        color: #ffffff;
        background-color: rgba(255, 255, 255, 0.15);
        transform: translateX(5px);
    }
    
    .sidebar .sidebar-content .stButton > button {
        background-color: rgba(255, 255, 255, 0.15);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 12px 15px;
        font-weight: 600;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
    }
    
    .sidebar .sidebar-content .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.25);
        transform: translateY(-3px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    /* 로그아웃 버튼 특별 스타일 */
    .logout-button {
        position: fixed;
        bottom: 20px;
        left: 30px;
        width: calc(100% - 60px);
    }
    
    .logout-button button {
        background-color: rgba(255, 77, 77, 0.2) !important;
        border: 1px solid rgba(255, 77, 77, 0.3) !important;
        font-weight: 600 !important;
    }
    
    .logout-button button:hover {
        background-color: rgba(255, 77, 77, 0.3) !important;
    }
    
    /* 사이드바 사용자 정보 스타일 */
    .user-info {
        background-color: rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        margin-bottom: 25px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
    }
    
    .user-info h3 {
        color: white;
        margin: 0;
        font-size: 20px;
        font-weight: 600;
    }
    
    .user-info p {
        color: rgba(255, 255, 255, 0.8);
        margin: 8px 0 0 0;
        font-size: 14px;
    }
    
    /* 메뉴 아이콘 스타일 */
    .menu-icon {
        display: inline-block;
        width: 28px;
        text-align: center;
        margin-right: 10px;
    }
    
    .menu-category {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px 15px;
        margin-top: 25px;
        margin-bottom: 15px;
        font-weight: 700;
        color: white;
        text-align: center;
        letter-spacing: 1px;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Supabase 초기화
try:
    # Streamlit Cloud에서 secrets를 사용하는 경우
    supabase_url = st.secrets["supabase"]["url"]
    supabase_key = st.secrets["supabase"]["key"]
except KeyError:
    # 로컬 개발 또는 secrets가 설정되지 않은 경우
    supabase_url = "https://czfvtkbndsfoznmknwsx.supabase.co"
    supabase_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6ZnZ0a2JuZHNmb3pubWtud3N4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxNTE1NDIsImV4cCI6MjA1ODcyNzU0Mn0.IpbN__1zImksnMo22CghSLTA-UCGoI67hHoDkrNpQGE"

# Supabase 클라이언트 생성 - 최신 버전 호환성 고려
try:
    supabase: Client = create_client(supabase_url, supabase_key)
except TypeError:
    # 이전 버전 호환성을 위한 대체 방법
    import httpx
    from supabase._sync.client import SyncClient
    supabase = SyncClient(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        http_client=httpx.Client()
    )

# 데이터 파일 경로 설정
if 'data_path' in st.secrets.get('database', {}):
    DATA_DIR = Path(st.secrets['database']['data_path'])
else:
    DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# 데이터 파일 경로
INSPECTION_DATA_FILE = DATA_DIR / "inspection_data.json"
INSPECTOR_DATA_FILE = DATA_DIR / "inspector_data.json"
DEFECT_DATA_FILE = DATA_DIR / "defect_data.json"

def init_db():
    """JSON 파일 기반 데이터베이스 초기화"""
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

def init_session_state():
    """세션 상태 초기화"""
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'username' not in st.session_state:
        st.session_state.username = ""
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = "일반"
    
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
    
    if 'basic_info_valid' not in st.session_state:
        st.session_state.basic_info_valid = False
    
    if 'registered_defects' not in st.session_state:
        st.session_state.registered_defects = []

# 세션 상태 초기화 실행
init_session_state()

# 앱이 잠자기 모드로 들어가지 않도록 하는 함수
def prevent_sleep():
    # 백그라운드 로깅 - 스레딩 사용하지 않음
    print("앱 활성 상태 유지 모드 활성화")

# 세션 유지를 위한 숨겨진 요소 추가
def add_keep_alive_element():
    # 타임스탬프 표시 (작게 표시)
    current_time = datetime.now().strftime("%H:%M:%S")
    st.sidebar.markdown(f"<small>세션 활성 상태: {current_time}</small>", unsafe_allow_html=True)

# 앱 시작 시 prevent_sleep 함수 호출
prevent_sleep()

def verify_login(username, password):
    """로그인 검증"""
    # 하드코딩된 사용자 정보로 먼저 확인
    if username == "admin" and password == "admin123":
        return True, "관리자"
        
    try:
        # 기본 사용자 정보
        default_users = {"admin": "admin123"}
        default_roles = {"admin": "관리자"}
        
        # Streamlit Cloud의 secrets에서 사용자 정보 가져오기
        try:
            users = st.secrets.get("users", default_users)
            roles = st.secrets.get("roles", default_roles)
        except:
            users = default_users
            roles = default_roles
            
        if username in users:
            if password == users[username]:
                user_role = roles.get(username, "일반")
                return True, user_role
        return False, None
    except Exception as e:
        st.error(f"로그인 검증 중 오류 발생: {str(e)}")
        return False, None

def check_password():
    """비밀번호 확인 및 로그인 처리"""
    # 이미 로그인되어 있다면 바로 성공 반환
    if st.session_state.get('logged_in', False):
        return True
        
    # 세션 유지를 위한 요소 추가
    add_keep_alive_element()
    
    # 디버그 모드 - 개발 환경에서만 사용 (프로덕션에서는 제거 필요)
    if st.sidebar.button("디버그 모드로 로그인"):
        # 로그인 성공 상태 설정
        st.session_state.logged_in = True
        st.session_state.user_role = "관리자"
        st.session_state.username = "admin_debug"
        st.session_state.login_attempts = 0
        st.session_state.page = "dashboard"
        # 페이지 새로고침
        st.rerun()
        return True
    
    # 로그인 시도 횟수 확인
    login_attempts = st.session_state.get('login_attempts', 0)
    if login_attempts >= 3:
        st.error("로그인 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.")
        st.session_state.login_attempts = 0  # 제한 시간 후 리셋
        return False

    # 로그인 UI
    st.title("CNC 품질관리 시스템")
    st.subheader("로그인")
    
    # 로그인 입력 필드
    username = st.text_input("아이디", key="login_username")
    password = st.text_input("비밀번호", type="password", key="login_password")
    login_button = st.button("로그인", key="login_button")
    
    if login_button:
        if not username:
            st.error("아이디를 입력하세요.")
            return False
        if not password:
            st.error("비밀번호를 입력하세요.")
            return False

        success, user_role = verify_login(username, password)
        if success:
            # 로그인 성공 상태 설정
                st.session_state.logged_in = True
            st.session_state.user_role = user_role
            st.session_state.username = username
            st.session_state.login_attempts = 0
                st.session_state.page = "dashboard"
            st.success(f"{username}님 환영합니다!")
            time.sleep(1)  # 1초 후 리로드
                st.rerun()
            return True
            else:
            # 로그인 실패 처리
            st.session_state.login_attempts = login_attempts + 1
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            if st.session_state.login_attempts >= 3:
                st.warning("로그인을 3회 이상 실패했습니다. 계정 정보를 확인하세요.")
            return False

    return False

# 로그인 상태 확인 및 페이지 표시
if not check_password():
    # 로그인 실패 시 여기서 멈춤
    st.stop()

# 여기서부터 로그인 성공 후 표시되는 내용
st.sidebar.markdown("""
<div class="user-info">
    <h3>👤 {0}님 환영합니다!</h3>
    <p>역할: {1}</p>
            </div>
""".format(st.session_state.username, st.session_state.user_role), unsafe_allow_html=True)

# 세션 유지를 위한 요소 추가
add_keep_alive_element()

# 메뉴 카테고리 스타일 추가
st.sidebar.markdown("""
<style>
.menu-category {
    background-color: rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    padding: 8px 12px;
    margin-top: 20px;
    margin-bottom: 10px;
    font-weight: 600;
    color: white;
    text-align: center;
}
</style>
        """, unsafe_allow_html=True)
        
# 사용자 프로필 섹션 추가
st.sidebar.markdown("""
<div class="user-info">
    <div style="margin-bottom: 12px;">
        <img src="https://ui-avatars.com/api/?name={}&background=random&size=80&rounded=true" alt="프로필" style="border-radius: 50%; border: 3px solid rgba(255, 255, 255, 0.3);">
    </div>
    <h3>{}</h3>
    <p>역할: {}</p>
    <div style="height: 1px; background-color: rgba(255, 255, 255, 0.1); margin: 12px 0;"></div>
    <p style="font-size: 12px;">최근 로그인: {}</p>
</div>
""".format(
    st.session_state.username,
    st.session_state.username,
    st.session_state.user_role,
    datetime.now().strftime('%Y-%m-%d %H:%M')
), unsafe_allow_html=True)

# 관리자 메뉴 카테고리
st.sidebar.markdown('<div class="menu-category">👨‍💼 관리자 메뉴</div>', unsafe_allow_html=True)

# 관리자 메뉴 항목
admin_pages = {
    "👤 관리자 및 사용자 관리": "manage_user",
    "👷 작업자 등록 및 관리": "manage_worker",
    "🏭 생산 모델 관리": "manage_model",
    "📋 생산 실적 관리": "manage_production",
    "💾 데이터 관리": "manage_data"
}

# 관리자 메뉴 선택 라디오 버튼
selected_admin_page = st.sidebar.radio("", list(admin_pages.keys()), key="admin_menu")

# 리포트 메뉴 카테고리
st.sidebar.markdown('<div class="menu-category">📈 리포트 메뉴</div>', unsafe_allow_html=True)

# 리포트 메뉴 항목
report_pages = {
    "📊 종합 대시보드": "dashboard",
    "📈 일간 품질리포트": "daily_report",
    "📆 주간 품질리포트": "weekly_report",
    "📅 월간 품질리포트": "monthly_report",
    "📚 연간 품질리포트": "yearly_report"
}

# 리포트 메뉴 아이템을 더 현대적인 디자인으로 개선
st.sidebar.markdown("""
<style>
.report-menu-item {
    display: flex;
    align-items: center;
    padding: 10px 15px;
    background-color: rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    margin-bottom: 8px;
    transition: all 0.3s ease;
    border-left: 3px solid transparent;
}
.report-menu-item:hover {
    background-color: rgba(255, 255, 255, 0.15);
    transform: translateX(5px);
    border-left: 3px solid rgba(255, 255, 255, 0.5);
}
.report-menu-item.active {
    background-color: rgba(255, 255, 255, 0.2);
    border-left: 3px solid white;
}
.report-menu-icon {
    font-size: 20px;
    margin-right: 10px;
    width: 24px;
    text-align: center;
}
.report-menu-text {
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# 리포트 메뉴 선택 라디오 버튼 대신 커스텀 라디오 버튼과 유사한 UI
selected_report = st.sidebar.radio("", list(report_pages.keys()), key="report_menu", label_visibility="collapsed")

# 선택된 메뉴에 따라 페이지 설정
if selected_admin_page in admin_pages:
    st.session_state.page = admin_pages[selected_admin_page]
elif selected_report in report_pages:
    st.session_state.page = report_pages[selected_report]

# 로그아웃 버튼 - 페이지 하단에 배치
st.sidebar.markdown('<div class="logout-button">', unsafe_allow_html=True)
if st.sidebar.button("로그아웃"):
            st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = "일반"
            st.session_state.page = "login"
            st.rerun()
st.sidebar.markdown('</div>', unsafe_allow_html=True)

# 검사원 정보 가져오기
def load_inspectors():
    try:
        response = supabase.table('inspectors').select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
    else:
            # 샘플 검사원 데이터 (실제 저장하지 않음)
            default_inspectors = [
                {"id": "INS001", "name": "홍길동", "department": "CNC_1", "process": "선삭", "years_of_service": 5.5},
                {"id": "INS002", "name": "김철수", "department": "CNC_2", "process": "밀링", "years_of_service": 3.2},
                {"id": "INS003", "name": "이영희", "department": "PQC_LINE", "process": "검사", "years_of_service": 7.1}
            ]
            return pd.DataFrame(default_inspectors)
    except Exception as e:
        st.error(f"검사원 정보 로딩 중 오류: {str(e)}")
        # 오류 발생시 샘플 데이터 반환
        default_inspectors = [
            {"id": "INS001", "name": "홍길동", "department": "CNC_1", "process": "선삭", "years_of_service": 5.5},
            {"id": "INS002", "name": "김철수", "department": "CNC_2", "process": "밀링", "years_of_service": 3.2},
            {"id": "INS003", "name": "이영희", "department": "PQC_LINE", "process": "검사", "years_of_service": 7.1}
        ]
        return pd.DataFrame(default_inspectors)

# 검사 데이터 저장
def save_inspection_data(data):
    response = supabase.table('inspection_data').insert(data).execute()
    return response

# 불량 데이터 저장
def save_defect_data(data):
    response = supabase.table('defect_data').insert(data).execute()
    return response

# 세션 상태 초기화 (앱 최초 로드 시 한 번만 실행)
if 'inspectors' not in st.session_state:
    st.session_state.inspectors = load_inspectors()

if 'registered_defects' not in st.session_state:
    st.session_state.registered_defects = []

# 현재 페이지에 따라 다른 내용 표시
if st.session_state.page == "dashboard":
    st.markdown("<div class='title-area'><h1>🏭 CNC 품질관리 시스템 - 대시보드</h1></div>", unsafe_allow_html=True)
    
    # 날짜 필터 (카드 형태)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        start_date = st.date_input("📅 시작일", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("📅 종료일", datetime.now())
    with col3:
        st.markdown("<div style='height: 40px;'></div>", unsafe_allow_html=True)
        st.markdown("<span class='sub-text'>📊 선택한 기간의 품질 데이터를 확인하세요</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 주요 품질 지표 (새로운 카드 디자인)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 주요 품질 지표</div>", unsafe_allow_html=True)
    st.markdown("<span class='sub-text'>최근 30일간의 주요 품질 지표 현황</span>", unsafe_allow_html=True)
    
    # 샘플 데이터
    cols = st.columns(4)
    with cols[0]:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>총 검사 건수</span></div>", unsafe_allow_html=True)
        st.metric("", "152", "+12")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전월 대비 검사 건수가 증가하고 있습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>평균 불량률</span></div>", unsafe_allow_html=True)
        st.metric("", "0.8%", "-0.2%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전월 대비 불량률이 개선되었습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>최다 불량 유형</span></div>", unsafe_allow_html=True)
        st.metric("", "치수불량", "")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>가장 많이 발생하는 불량 유형입니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>진행 중인 작업</span></div>", unsafe_allow_html=True)
        st.metric("", "3", "+1")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>현재 진행 중인 작업 건수입니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 차트 영역
    col1, col2 = st.columns(2)
    
    with col1:
        # 공정별 불량률 추이 차트 (1주일 기준으로 변경)
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>📊 일별 불량률 추이 (최근 7일)</div>", unsafe_allow_html=True)
        st.markdown("<span class='sub-text'>최근 7일간의 공정별 일일 불량률 변화</span>", unsafe_allow_html=True)
        
        # 일주일 데이터 준비 (현재 날짜부터 7일 전까지)
        last_week = pd.date_range(end=datetime.now(), periods=7)
        weekdays = [d.strftime("%a") for d in last_week]  # 요일 약자 (월,화,수...)
        dates_str = [d.strftime("%m/%d") for d in last_week]  # 날짜 형식 (월/일)
        
        # 날짜와 요일 결합
        x_labels = [f"{d} ({w})" for d, w in zip(dates_str, weekdays)]
        
        # 밀링 데이터 (막대 그래프)
        milling_data = np.random.rand(7) * 1.5
        # 선삭 데이터 (라인 차트)
        turning_data = np.random.rand(7) * 2
        
        # 복합 그래프 생성
        fig = go.Figure()
        
        # 밀링 공정 (막대 그래프)
        fig.add_trace(go.Bar(
            x=x_labels,
            y=milling_data,
            name="밀링",
            marker_color="#4361ee",
            opacity=0.7
        ))
        
        # 선삭 공정 (선 그래프)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=turning_data,
            mode='lines+markers',
            name='선삭',
            line=dict(color='#fb8c00', width=3),
            marker=dict(size=8)
        ))
        
        # 평균 불량률 (점선)
        avg_defect = np.mean(np.concatenate([milling_data, turning_data]))
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=[avg_defect] * 7,
            mode='lines',
            name='평균',
            line=dict(color='#4cb782', width=2, dash='dash'),
        ))
        
        # 레이아웃 업데이트
        fig.update_layout(
            title=None,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False,
                title="날짜 (요일)",
                tickangle=-30,
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor="rgba(0,0,0,0.05)",
                title="불량률 (%)"
            ),
            hovermode="x unified",
            barmode='group'
        )
        
        # 불량률 목표선 (예: 1%)
        target_rate = 1.0
        fig.add_shape(
            type="line",
            x0=x_labels[0],
            y0=target_rate,
            x1=x_labels[-1],
            y1=target_rate,
            line=dict(color="red", width=1, dash="dot"),
        )
        
        # 목표선 주석 추가
        fig.add_annotation(
            x=x_labels[1],
            y=target_rate,
            text="목표선 (1%)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            arrowsize=1,
            arrowwidth=1,
            ax=-40,
            ay=-30
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # 불량 유형 분포 차트
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>🍩 불량 유형 분포</div>", unsafe_allow_html=True)
        st.markdown("<span class='sub-text'>불량 유형별 발생 비율</span>", unsafe_allow_html=True)
        
        # 불량 유형 분포
        defect_types = ["치수 불량", "표면 거칠기", "칩핑", "기타"]
        defect_counts = np.random.randint(5, 30, size=len(defect_types))
        
        # 도넛 차트에 아이콘 지정 (이모티콘)
        defect_icons = ["📏", "🔍", "🔨", "❓"]
        custom_labels = [f"{icon} {label}" for icon, label in zip(defect_icons, defect_types)]
        
        fig = px.pie(
            values=defect_counts, 
            names=custom_labels, 
            hole=0.6,
            color_discrete_sequence=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"]
        )
        
        # 중앙에 총 불량 수 표시
        total_defects = sum(defect_counts)
        fig.add_annotation(
            text=f"총 불량<br>{total_defects}건",
            x=0.5, y=0.5,
            font_size=15,
                font_family="Arial",
                showarrow=False
        )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=10, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            paper_bgcolor="rgba(0,0,0,0)"
        )
        fig.update_traces(
            textposition='outside', 
            textinfo='percent',
            hovertemplate='%{label}<br>수량: %{value}<br>비율: %{percent}',
        )
        st.plotly_chart(fig, use_container_width=True)

    # 최근 검사 데이터 섹션
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📋 최근 검사 데이터</div>", unsafe_allow_html=True)
    st.markdown("<span class='sub-text'>가장 최근에 등록된 검사 데이터 현황</span>", unsafe_allow_html=True)
    
    # 최근 데이터를 위한 샘플 테이블
    recent_data = {
        "📅 검사일자": pd.date_range(end=datetime.now(), periods=5).strftime("%Y-%m-%d"),
        "🔢 LOT번호": [f"LOT{i:04d}" for i in range(1, 6)],
        "👨‍🔧 검사원": np.random.choice(["홍길동", "김철수", "이영희"], 5),
        "⚙️ 공정": np.random.choice(["선삭", "밀링"], 5),
        "📦 전체수량": np.random.randint(50, 200, 5),
        "⚠️ 불량수량": np.random.randint(0, 10, 5),
    }
    
    df = pd.DataFrame(recent_data)
    df["📊 불량률(%)"] = (df["⚠️ 불량수량"] / df["📦 전체수량"] * 100).round(2)
    
    # 데이터프레임에 스타일 적용
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "📊 불량률(%)": st.column_config.ProgressColumn(
                "📊 불량률(%)",
                help="불량률 퍼센트",
                format="%.1f%%",
                min_value=0,
                max_value=5,  # 대부분의 불량률은 5% 이하로 가정
            ),
        }
    )
    
    # 최근 검사 데이터 요약 지표
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_defect_rate = df["📊 불량률(%)"].mean()
        st.metric("⚠️ 평균 불량률", f"{avg_defect_rate:.2f}%")
    with col2:
        min_defect_rate = df["📊 불량률(%)"].min()
        st.metric("🟢 최소 불량률", f"{min_defect_rate:.2f}%")
    with col3:
        max_defect_rate = df["📊 불량률(%)"].max()
        st.metric("🔴 최대 불량률", f"{max_defect_rate:.2f}%")
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "daily_report":
    daily_report()
    
elif st.session_state.page == "weekly_report":
    weekly_report()
    
elif st.session_state.page == "monthly_report":
    monthly_report()
    
elif st.session_state.page == "yearly_report":
    yearly_report()
    
elif st.session_state.page == "input_inspection":
    st.title("검사 데이터 입력")
    
    # 기본 정보 입력
    with st.form("basic_info"):
        st.subheader("기본 정보 입력")
        
        col1, col2 = st.columns(2)
        with col1:
            inspector = st.selectbox("검사원", options=st.session_state.inspectors['name'].tolist())
            process = st.selectbox("공정", options=["선삭", "밀링"])
            
        with col2:
            date = st.date_input("검사일자")
            time = st.time_input("검사시간")
            
        lot_number = st.text_input("LOT 번호")
        total_quantity = st.number_input("전체 수량", min_value=1, value=1)
        
        submit_basic = st.form_submit_button("기본 정보 등록")
        
    if submit_basic:
        st.session_state.basic_info_valid = True
        st.success("기본 정보가 등록되었습니다.")
    else:
        st.session_state.basic_info_valid = False

    # 불량 정보 입력
    if st.session_state.get('basic_info_valid', False):
        with st.form("defect_info"):
            st.subheader("불량 정보 입력")
            
            col1, col2 = st.columns(2)
        with col1:
                defect_type = st.selectbox("불량 유형", 
                    options=["치수", "표면거칠기", "칩핑", "기타"])
            
            with col2:
                defect_quantity = st.number_input("불량 수량", 
                    min_value=1, max_value=total_quantity, value=1)
                
            submit_defect = st.form_submit_button("불량 등록")
            
        if submit_defect:
            new_defect = {
                "type": defect_type,
                "quantity": defect_quantity
            }
            st.session_state.registered_defects.append(new_defect)
            st.success(f"{defect_type} 불량이 {defect_quantity}개 등록되었습니다.")
            
        # 등록된 불량 정보 표시
        if st.session_state.registered_defects:
            st.subheader("등록된 불량 정보")
            defects_df = pd.DataFrame(st.session_state.registered_defects)
            st.dataframe(defects_df)
            
            total_defects = defects_df['quantity'].sum()
            defect_rate = (total_defects / total_quantity) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("총 불량 수량", f"{total_defects}개")
        with col2:
                st.metric("불량률", f"{defect_rate:.2f}%")
                
        # 불량 목록 초기화 버튼
        if st.button("불량 목록 초기화"):
            st.session_state.registered_defects = []
            st.success("불량 목록이 초기화되었습니다.")
            st.stop()  # 현재 실행을 중지하고 페이지를 다시 로드합니다
            
        # 검사 데이터 저장
        if st.button("검사 데이터 저장"):
            if st.session_state.registered_defects:
                inspection_datetime = datetime.combine(date, time)
                inspector_data = st.session_state.inspectors[st.session_state.inspectors['name'] == inspector].iloc[0]
                
                inspection_data = {
                    "inspector_id": inspector_data['id'],
                    "process": process,
                    "inspection_datetime": inspection_datetime.isoformat(),
                    "lot_number": lot_number,
                    "total_quantity": total_quantity
                }
                
                try:
                    # 검사 데이터 저장 (로컬 세션 상태에만 저장)
                    st.session_state.last_inspection = inspection_data
                    
                    # 불량 데이터 저장 (로컬 세션 상태에만 저장)
                    if 'saved_defects' not in st.session_state:
                        st.session_state.saved_defects = []
                        
                    for defect in st.session_state.registered_defects:
                        defect_data = {
                            "inspection_id": lot_number,  # 임시 ID로 LOT 번호 사용
                            "defect_type": defect['type'],
                            "quantity": defect['quantity']
                        }
                        st.session_state.saved_defects.append(defect_data)
                    
                    st.success("검사 데이터가 성공적으로 저장되었습니다.")
                    st.session_state.registered_defects = []
                    st.stop()  # 현재 실행을 중지하고 페이지를 다시 로드합니다
                except Exception as e:
                    st.error(f"데이터 저장 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("저장할 불량 데이터가 없습니다.")

elif st.session_state.page == "view_inspection":
    st.title("검사 데이터 조회")
    
    # 필터링 옵션
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_process = st.selectbox("공정 필터", options=["전체", "선삭", "밀링"])
    with col2:
        filter_start_date = st.date_input("시작일", datetime.now() - timedelta(days=30))
    with col3:
        filter_end_date = st.date_input("종료일", datetime.now())
    
    try:
        # 검사 데이터 조회
        st.subheader("검사 데이터 목록")
        
        # Supabase에서 데이터 가져오기 (실제 구현 필요)
        # 샘플 데이터 표시
        sample_data = {
            "inspection_id": [f"INSP{i}" for i in range(1, 11)],
            "inspector_name": np.random.choice(["홍길동", "김철수", "이영희"], 10),
            "process": np.random.choice(["선삭", "밀링"], 10),
            "inspection_date": pd.date_range(start=filter_start_date, periods=10).strftime("%Y-%m-%d"),
            "lot_number": [f"LOT{i:04d}" for i in range(1, 11)],
            "total_quantity": np.random.randint(50, 200, 10),
            "defect_count": np.random.randint(0, 10, 10),
        }
        
        df = pd.DataFrame(sample_data)
        df["defect_rate"] = (df["defect_count"] / df["total_quantity"] * 100).round(2)
        
        # 공정 필터링
        if filter_process != "전체":
            df = df[df["process"] == filter_process]
            
        st.dataframe(df)
        
        # 선택한 데이터 상세 보기 기능
        inspection_id = st.selectbox("상세 정보를 볼 검사 ID 선택", options=df["inspection_id"].tolist())
        
        if inspection_id:
            st.subheader(f"검사 상세 정보: {inspection_id}")
            # 선택한 검사의 상세 정보 (샘플)
            selected_row = df[df["inspection_id"] == inspection_id].iloc[0]
            
            col1, col2, col3 = st.columns(3)
        with col1:
                st.metric("검사원", selected_row["inspector_name"])
                st.metric("총 수량", f"{selected_row['total_quantity']}개")
        with col2:
                st.metric("공정", selected_row["process"])
                st.metric("불량 수량", f"{selected_row['defect_count']}개")
        with col3:
                st.metric("검사일", selected_row["inspection_date"])
                st.metric("불량률", f"{selected_row['defect_rate']}%")
                
            # 불량 상세 정보 (샘플)
            st.subheader("불량 상세 정보")
            defect_detail = {
                "defect_type": np.random.choice(["치수", "표면거칠기", "칩핑", "기타"], 
                                           selected_row["defect_count"]),
                "quantity": np.random.randint(1, 5, selected_row["defect_count"])
            }
            
            if selected_row["defect_count"] > 0:
                defect_df = pd.DataFrame(defect_detail)
                st.dataframe(defect_df)
                
                # 불량 유형 분포 차트
                fig = px.pie(defect_df, names="defect_type", values="quantity", 
                           title="불량 유형 분포")
                st.plotly_chart(fig)
            else:
                st.info("이 검사에는 등록된 불량이 없습니다.")
    except Exception as e:
        st.error(f"데이터 조회 중 오류가 발생했습니다: {str(e)}")

elif st.session_state.page == "manage_inspectors":
    if st.session_state.user_role != "관리자":
        st.warning("관리자만 접근할 수 있는 페이지입니다.")
        st.stop()
        
    st.title("검사원 관리")
    
    # 검사원 목록 표시
    st.subheader("등록된 검사원 목록")
    
    try:
        inspectors_df = load_inspectors()
        st.dataframe(inspectors_df)
        
        # 새 검사원 등록 양식
        st.subheader("새 검사원 등록")
        with st.form("new_inspector"):
            col1, col2 = st.columns(2)
        with col1:
                inspector_id = st.text_input("검사원 ID")
                name = st.text_input("이름")
        with col2:
                department = st.selectbox("부서", options=["CNC_1", "CNC_2", "PQC_LINE", "CDC"])
                process = st.selectbox("담당 공정", options=["선삭", "밀링", "검사", "기타"])
            
            years = st.number_input("근속년수", min_value=0.0, step=0.5)
            
            submit_inspector = st.form_submit_button("검사원 등록")
            
        if submit_inspector:
            if not inspector_id or not name:
                st.error("검사원 ID와 이름은 필수 입력 항목입니다.")
            else:
                new_inspector = {
                    "id": inspector_id,
                    "name": name,
                    "department": department,
                    "process": process,
                    "years_of_service": years
                }
                
                try:
                    # Supabase 데이터베이스 저장은 RLS 정책 설정을 먼저 확인 후 진행
                    # 현재는 임시로 세션 상태에만 저장
                    temp_df = pd.DataFrame([new_inspector])
                    if 'inspectors_df' in st.session_state:
                        st.session_state.inspectors_df = pd.concat([st.session_state.inspectors_df, temp_df])
                    else:
                        st.session_state.inspectors_df = temp_df
                    
                    # 기존 inspectors 업데이트
                    if 'inspectors' in st.session_state:
                        new_inspectors = st.session_state.inspectors.copy()
                        new_inspectors = pd.concat([new_inspectors, temp_df], ignore_index=True)
                        st.session_state.inspectors = new_inspectors
                    
                    st.success(f"{name} 검사원이 성공적으로 등록되었습니다. (로컬 저장)")
                    st.info("현재 Supabase RLS 정책으로 인해 데이터는 로컬 세션에만 저장됩니다.")
                    
                except Exception as e:
                    st.error(f"검사원 등록 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        st.error(f"검사원 관리 중 오류가 발생했습니다: {str(e)}")

elif st.session_state.page == "settings":
    if st.session_state.user_role != "관리자":
        st.warning("관리자만 접근할 수 있는 페이지입니다.")
        st.stop()
        
    st.title("시스템 설정")
    
    # 시스템 설정 양식
    st.subheader("불량 유형 설정")
    current_defect_types = st.session_state.defect_types
    
    defect_types_str = st.text_area("불량 유형 목록 (쉼표로 구분)", 
                                  value=", ".join(current_defect_types))
    
    if st.button("불량 유형 저장"):
        new_defect_types = [dtype.strip() for dtype in defect_types_str.split(",")]
        st.session_state.defect_types = new_defect_types
        st.success("불량 유형이 저장되었습니다.")
        
    # 데이터베이스 설정 (관리자 전용)
    st.subheader("데이터베이스 관리")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("데이터베이스 백업"):
            st.info("데이터베이스 백업 기능은 준비 중입니다.")
    with col2:
        if st.button("테스트 데이터 생성"):
            st.info("테스트 데이터 생성 기능은 준비 중입니다.") 

# 일간 리포트 페이지
def daily_report():
    st.markdown("<div class='title-area'><h1>📈 일간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 날짜 선택 기능
    selected_date = st.date_input("날짜 선택", datetime.now())
    
    # 4개의 카드 레이아웃 생성
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>불량률 일간 추이</h3>
            <p>오늘의 시간대별 불량률 변화를 확인합니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 시간대별 불량률 차트 (예시 데이터)
        hours = list(range(0, 24))
        defect_rates = [1.2, 1.1, 0.8, 0.7, 0.9, 1.0, 1.3, 1.5, 1.8, 1.7, 1.6, 1.4, 
                        1.3, 1.2, 1.4, 1.5, 1.6, 1.7, 1.5, 1.3, 1.1, 0.9, 0.8, 1.0]
        
        fig = px.line(x=hours, y=defect_rates, 
                     labels={"x": "시간", "y": "불량률 (%)"},
                     title="시간대별 불량률")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("""
        <div class="card">
            <h3>불량 유형 분석</h3>
            <p>오늘 발생한 불량 유형별 비율입니다.</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 불량 유형별 파이 차트 (예시 데이터)
        defect_types = ["치수 불량", "표면 불량", "기능 불량", "기타"]
        defect_counts = [45, 30, 15, 10]
        
        fig = px.pie(values=defect_counts, names=defect_types, 
                    title="불량 유형 분포")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
    st.markdown("""
        <div class="card">
            <h3>공정별 품질 지표</h3>
            <p>각 공정별 품질 지표를 확인합니다.</p>
        </div>
    """, unsafe_allow_html=True)
    
        # 공정별 불량률 막대 그래프 (예시 데이터)
        processes = ["선삭", "밀링", "연삭", "조립", "검사"]
        process_defect_rates = [1.5, 2.1, 0.8, 1.2, 0.5]
        
        fig = px.bar(x=processes, y=process_defect_rates,
                    labels={"x": "공정", "y": "불량률 (%)"},
                    title="공정별 불량률")
        fig.update_layout(height=350)
        st.plotly_chart(fig, use_container_width=True)
        
    with col4:
    st.markdown("""
        <div class="card">
            <h3>품질 개선 조치 현황</h3>
            <p>일간 품질 개선 조치 현황을 확인합니다.</p>
        </div>
    """, unsafe_allow_html=True)
    
        # 품질 개선 조치 현황 테이블 (예시 데이터)
        data = {
            "조치 내용": ["작업자 교육", "설비 점검", "공구 교체", "작업 방법 개선"],
            "담당자": ["김철수", "이영희", "박지성", "최민수"],
            "상태": ["완료", "진행중", "계획", "완료"]
        }
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True, height=300)

# 주간 리포트 페이지
def weekly_report():
    st.markdown("<div class='title-area'><h1>📆 주간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 주 선택 기능
    today = datetime.now()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    st.subheader(f"{week_start.strftime('%Y-%m-%d')} ~ {week_end.strftime('%Y-%m-%d')}")
    
    # 주간 요약 지표
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
    st.markdown("""
        <div class="metric-card">
            <h3>주간 평균 불량률</h3>
            <h2>1.23%</h2>
            <p style="color: green">↓ 0.2% 전주 대비</p>
        </div>
    """, unsafe_allow_html=True)
    
        with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>주간 생산량</h3>
            <h2>12,450개</h2>
            <p style="color: green">↑ 5.2% 전주 대비</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>품질 조치건수</h3>
            <h2>24건</h2>
            <p style="color: red">↑ 3건 전주 대비</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
    st.markdown("""
        <div class="metric-card">
            <h3>고객 클레임</h3>
            <h2>2건</h2>
            <p style="color: green">↓ 1건 전주 대비</p>
        </div>
    """, unsafe_allow_html=True)
    
    # 주간 상세 분석
    st.markdown("<br>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["일별 추이", "제품별 분석", "품질 문제 요약"])
    
    with tab1:
        # 일별 불량률 추이 (예시 데이터)
        days = ["월", "화", "수", "목", "금", "토", "일"]
        daily_defect_rates = [1.4, 1.2, 1.3, 1.1, 1.0, 0.9, 1.5]
        daily_production = [2300, 2450, 2380, 2420, 2500, 200, 200]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days, 
            y=daily_defect_rates,
            mode='lines+markers',
            name='불량률 (%)',
            line=dict(color='red', width=2),
            marker=dict(size=8)
        ))
        
        fig.add_trace(go.Bar(
            x=days,
            y=daily_production,
            name='생산량',
            marker_color='lightblue',
            opacity=0.7,
            yaxis='y2'
        ))
        
        fig.update_layout(
            title='일별 생산량 및 불량률',
            xaxis=dict(title='요일'),
            yaxis=dict(title='불량률 (%)', range=[0, 2]),
            yaxis2=dict(title='생산량', overlaying='y', side='right', range=[0, 3000]),
            legend=dict(x=0.02, y=0.98),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # 제품별 불량률 (예시 데이터)
        products = ["A-1001", "B-2002", "C-3003", "D-4004", "E-5005"]
        product_defect_rates = [1.8, 1.2, 0.7, 1.5, 2.1]
        product_volumes = [3500, 2800, 1500, 2200, 2450]
        
        bubble_size = [v/100 for v in product_volumes]
        
        fig = px.scatter(
            x=products,
            y=product_defect_rates,
            size=bubble_size,
            color=product_defect_rates,
            color_continuous_scale='RdYlGn_r',
            labels={'x': '제품 모델', 'y': '불량률 (%)'},
            title='제품별 불량률 및 생산량'
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    with tab3:
        # 품질 문제 요약 (예시 데이터)
        st.subheader("주요 품질 문제 및 조치사항")
        
        data = {
            "문제 유형": ["치수 불량", "표면 스크래치", "조립 불량", "재료 결함", "기능 이상"],
            "발생 건수": [32, 28, 15, 8, 12],
            "영향 제품": ["A-1001, B-2002", "전 제품", "C-3003", "D-4004", "B-2002"],
            "조치 상태": ["해결", "진행중", "해결", "조사중", "해결"],
            "담당자": ["김철수", "이영희", "박지성", "최민수", "정동원"]
        }
        
        df = pd.DataFrame(data)
        st.dataframe(df, use_container_width=True)

# 월간 리포트 페이지
def monthly_report():
    st.markdown("<div class='title-area'><h1>📅 월간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 월 선택 기능
    current_month = datetime.now().replace(day=1)
    months = []
    month_labels = []
    
    for i in range(6):
        month = current_month - timedelta(days=30*i)
        months.append(month)
        month_labels.append(month.strftime('%Y년 %m월'))
    
    selected_month = st.selectbox("월 선택", month_labels)
    
    # 월간 요약 차트
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("월간 품질 성과 요약")
    
    # 품질 KPI 달성도 게이지 차트
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = 92,
            title = {'text': "양품률 (%)"},
            delta = {'reference': 90, 'increasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 70], 'color': "red"},
                    {'range': [70, 85], 'color': "orange"},
                    {'range': [85, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 2},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = 85,
            title = {'text': "납기 준수율 (%)"},
            delta = {'reference': 90, 'decreasing': {'color': "red"}},
            gauge = {
                'axis': {'range': [0, 100]},
                'bar': {'color': "orange"},
                'steps': [
                    {'range': [0, 70], 'color': "red"},
                    {'range': [70, 85], 'color': "orange"},
                    {'range': [85, 100], 'color': "lightgreen"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 2},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        fig = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = 0.8,
            title = {'text': "고객 클레임률 (%)"},
            delta = {'reference': 1.0, 'decreasing': {'color': "green"}},
            gauge = {
                'axis': {'range': [0, 3]},
                'bar': {'color': "green"},
                'steps': [
                    {'range': [0, 1], 'color': "lightgreen"},
                    {'range': [1, 2], 'color': "orange"},
                    {'range': [2, 3], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 2},
                    'thickness': 0.75,
                    'value': 1.0
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    # 월간 트렌드 분석
    st.subheader("월간 불량률 트렌드 분석")
    
    # 최근 6개월 불량률 트렌드 (예시 데이터)
    months_trend = ["1월", "2월", "3월", "4월", "5월", "6월"]
    defect_rate_trend = [1.8, 1.6, 1.4, 1.3, 1.2, 0.8]
    target_line = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months_trend,
        y=defect_rate_trend,
        mode='lines+markers',
        name='실제 불량률',
        line=dict(color='blue', width=3),
        marker=dict(size=10)
    ))
    
    fig.add_trace(go.Scatter(
        x=months_trend,
        y=target_line,
        mode='lines',
        name='목표 불량률',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    fig.update_layout(
        title="최근 6개월 불량률 추이",
        xaxis_title="월",
        yaxis_title="불량률 (%)",
        legend=dict(y=0.99, x=0.01),
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 월간 품질 개선 활동
    st.subheader("품질 개선 활동 및 성과")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="card">
            <h3>주요 품질 개선 활동</h3>
            <ul>
                <li>CNC 가공 정밀도 향상을 위한 설비 보정</li>
                <li>품질 검사 프로세스 자동화 구축</li>
                <li>작업자 품질 교육 프로그램 시행</li>
                <li>공급업체 품질 관리 강화</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="card">
            <h3>주요 개선 성과</h3>
            <ul>
                <li>치수 불량 30% 감소</li>
                <li>표면 품질 불량 25% 감소</li>
                <li>검사 공정 시간 40% 단축</li>
                <li>재작업 비용 35% 절감</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

# 연간 리포트 페이지
def yearly_report():
    st.markdown("<div class='title-area'><h1>📚 연간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 연도 선택 기능
    current_year = datetime.now().year
    years = list(range(current_year-5, current_year+1))
    selected_year = st.selectbox("연도 선택", years, index=5)
    
    # 연간 품질 성과 대시보드
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("연간 품질 성과 대시보드")
    
    # 주요 KPI 요약
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h3>평균 불량률</h3>
            <h2>0.92%</h2>
            <p style="color: green">목표 대비 8% 개선</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h3>품질 조치건수</h3>
            <h2>287건</h2>
            <p style="color: orange">전년 대비 12% 증가</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h3>고객 품질 만족도</h3>
            <h2>4.3/5.0</h2>
            <p style="color: green">전년 대비 0.2점 향상</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card">
            <h3>품질 비용</h3>
            <h2>₩128M</h2>
            <p style="color: green">전년 대비 7% 절감</p>
        </div>
        """, unsafe_allow_html=True)
    
    # 연간 불량률 추이
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 분기별 불량률 히트맵 (예시 데이터)
    quarters = ["Q1", "Q2", "Q3", "Q4"]
    product_lines = ["A 라인", "B 라인", "C 라인", "D 라인", "E 라인"]
    
    # 히트맵용 데이터 생성 (예시)
    heatmap_data = np.array([
        [1.2, 1.0, 0.9, 0.7],
        [1.5, 1.3, 1.2, 1.0],
        [0.8, 0.7, 0.6, 0.5],
        [1.8, 1.6, 1.4, 1.2],
        [1.1, 1.0, 0.9, 0.8]
    ])
    
    fig = px.imshow(
        heatmap_data,
        labels=dict(x="분기", y="생산 라인", color="불량률 (%)"),
        x=quarters,
        y=product_lines,
        color_continuous_scale='RdYlGn_r',
        title="생산 라인별 분기 불량률"
    )
    
    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    # 연간 품질 리스크 분석
    st.subheader("품질 리스크 분석")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 파레토 차트 (품질 문제 유형)
        defect_types = ["치수 불량", "표면 스크래치", "조립 불량", "기능 불량", "재료 결함", "라벨링 오류", "포장 불량"]
        defect_counts = [420, 350, 280, 190, 150, 120, 90]
        cumulative_percent = np.cumsum(defect_counts) / np.sum(defect_counts) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=defect_types,
            y=defect_counts,
            name="발생 건수",
            marker_color="skyblue"
        ))
        
        fig.add_trace(go.Scatter(
            x=defect_types,
            y=cumulative_percent,
            name="누적 %",
            marker=dict(color="red"),
            mode="lines+markers",
            yaxis="y2"
        ))
        
        fig.update_layout(
            title="품질 문제 유형별 파레토 분석",
            xaxis_title="불량 유형",
            yaxis_title="발생 건수",
            yaxis2=dict(
                title="누적 %",
                overlaying="y",
                side="right",
                range=[0, 100]
            ),
            legend=dict(x=0.02, y=0.98),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 품질 비용 분석
        cost_categories = ["예방 비용", "평가 비용", "내부 실패 비용", "외부 실패 비용"]
        cost_values = [35, 42, 30, 21]
        cost_colors = ["green", "blue", "orange", "red"]
        
        fig = px.pie(
            values=cost_values, 
            names=cost_categories,
            color=cost_categories,
            color_discrete_sequence=cost_colors,
            title="품질 비용 분석"
        )
        
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # 연간 품질 개선 성과
    st.subheader("품질 개선 성과 및 다음 해 계획")
    
    tab1, tab2 = st.tabs(["주요 성과", "다음 해 계획"])
    
    with tab1:
        st.markdown("""
        <div class="card">
            <h3>품질 개선 주요 성과</h3>
            <ol>
                <li><strong>공정 자동화 시스템 도입</strong>: CNC 가공 공정 자동화를 통해 품질 안정성 30% 향상</li>
                <li><strong>품질 관리 시스템 고도화</strong>: 실시간 품질 모니터링 시스템 구축으로 불량 조기 감지 능력 강화</li>
                <li><strong>공급업체 품질 관리 프로그램</strong>: 핵심 공급업체에 대한 품질 인증 프로그램을 통해 원자재 불량 25% 감소</li>
                <li><strong>직원 역량 강화 프로그램</strong>: 품질 관련 교육 프로그램 시행으로 인적 오류 20% 감소</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)
        
    with tab2:
        st.markdown("""
        <div class="card">
            <h3>다음 해 품질 개선 계획</h3>
            <ol>
                <li><strong>AI 기반 품질 예측 모델 도입</strong>: 불량 예측 및 예방 시스템 구축</li>
                <li><strong>디지털 트윈 기술 적용</strong>: 가상 시뮬레이션을 통한 품질 문제 사전 검증</li>
                <li><strong>글로벌 품질 표준 인증 획득</strong>: ISO 9001:2015 및 산업별 특화 인증 확대</li>
                <li><strong>친환경 생산 프로세스 도입</strong>: 환경 영향 최소화 및 지속가능한 품질 관리 체계 구축</li>
                <li><strong>품질 비용 최적화 프로그램</strong>: 예방 활동 강화를 통한 실패 비용 최소화</li>
            </ol>
        </div>
        """, unsafe_allow_html=True)

def dashboard():
    st.title("📊 종합 대시보드")
    st.subheader("실시간 품질 현황 및 주요 지표")
    
    # 현재 날짜 표시
    current_date = datetime.now().strftime("%Y년 %m월 %d일")
    st.write(f"최종 업데이트: {current_date}")
    
    # 주요 KPI 지표 (4개 카드)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(label="현재 불량률", value="1.2%", delta="-0.3%")
    
    with col2:
        st.metric(label="일일 생산량", value="2,450개", delta="125개")
    
    with col3:
        st.metric(label="품질 점수", value="94.5점", delta="2.1점")
    
    with col4:
        st.metric(label="대응중인 이슈", value="3건", delta="-2건")
    
    # 실시간 모니터링 (2개 차트)
    st.subheader("실시간 공정 모니터링")
    col1, col2 = st.columns(2)
    
    with col1:
        # 공정별 품질 상태
        processes = ["절단 공정", "가공 공정", "조립 공정", "도장 공정", "포장 공정"]
        status = ["정상", "정상", "주의", "정상", "정상"]
        status_color = {"정상": "#28a745", "주의": "#ffc107", "경고": "#dc3545"}
        
        status_df = pd.DataFrame({
            "공정": processes,
            "상태": status
        })
        
        # 상태별 색상 지정
        fig = go.Figure(data=[go.Table(
            header=dict(values=["공정", "상태"],
                        fill_color="#f8f9fa",
                        align="center"),
            cells=dict(values=[status_df["공정"], status_df["상태"]],
                      fill_color=[[status_color.get(s, "#ffffff") for s in status_df["상태"]]],
                      align="center"))
        ])
        
        fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=250)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 시간대별 불량률 추이
        hours = list(range(8, 18))
        defect_rates = [1.4, 1.3, 1.2, 1.5, 1.1, 1.3, 1.7, 1.4, 1.2, 1.0]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hours, y=defect_rates, mode='lines+markers', 
                                name='불량률', line=dict(color='royalblue', width=3)))
        
        fig.update_layout(
            title='시간대별 불량률 변화',
            xaxis_title='시간',
            yaxis_title='불량률(%)',
            yaxis=dict(range=[0.8, 2.0]),
            height=250,
            margin=dict(l=0, r=0, t=40, b=0)
        )
        
        # 경계선 추가
        fig.add_shape(type="line",
            x0=8, y0=1.5, x1=17, y1=1.5,
            line=dict(color="red", width=1, dash="dot"),
        )
        
        st.plotly_chart(fig, use_container_width=True)

    # 품질 문제 요약
    st.subheader("주요 품질 이슈 및 조치 현황")
    
    issues = [
        {"이슈": "조립 공정 체결력 불량", "발생일": "2023-05-22", "상태": "대응중", "담당자": "김품질", "조치내용": "조립 장비 캘리브레이션 진행중"},
        {"이슈": "도장 공정 색상 불일치", "발생일": "2023-05-21", "상태": "대응중", "담당자": "박공정", "조치내용": "도료 공급업체 컨택 및 샘플 테스트 진행"},
        {"이슈": "포장재 파손", "발생일": "2023-05-20", "상태": "대응중", "담당자": "이포장", "조치내용": "포장 자재 변경 및 취급 방법 개선 중"},
        {"이슈": "원자재 규격 이탈", "발생일": "2023-05-18", "상태": "완료", "담당자": "최자재", "조치내용": "공급업체 품질 회의 완료 및 개선 확인"},
        {"이슈": "측정 장비 오차", "발생일": "2023-05-15", "상태": "완료", "담당자": "정측정", "조치내용": "장비 재교정 완료 및 측정 시스템 분석 실시"}
    ]
    
    issues_df = pd.DataFrame(issues)
    
    # 테이블 색상 스타일링 함수
    def highlight_status(s):
        return ['background-color: #28a745; color: white' if v == '완료' else 'background-color: #ffc107; color: black' if v == '대응중' else '' for v in s]
    
    # 스타일이 적용된 테이블 표시
    st.dataframe(issues_df.style.apply(highlight_status, subset=['상태']), height=300)

# 페이지 선택에 따른 함수 호출
if selected_option == "👨‍💼 사용자 관리":
    user_management()
elif selected_option == "👷 작업자 등록 및 관리":
    worker_registration()
elif selected_option == "🧪 자재 및 변수 관리":
    material_management()
elif selected_option == "📋 작업 지시 관리":
    work_order_management()
elif selected_option == "🔧 설비 관리":
    equipment_management()
elif selected_option == "📊 종합 대시보드":
    dashboard()
elif selected_option == "📈 일간 품질리포트":
    daily_report()
elif selected_option == "📆 주간 품질리포트":
    weekly_report()
elif selected_option == "📅 월간 품질리포트":
    monthly_report()
elif selected_option == "📚 연간 품질리포트":
    yearly_report()
else:
    st.write("페이지를 선택해주세요.")