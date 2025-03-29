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
        background: linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%);
        color: white;
        padding-top: 20px;
        padding-bottom: 20px;
    }
    
    .sidebar .sidebar-content .stRadio > label {
        color: white;
        font-weight: 500;
        margin-bottom: 10px;
    }
    
    .sidebar .sidebar-content .stRadio > div {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 15px;
    }
    
    .sidebar .sidebar-content .stRadio > div > label {
        color: white;
        transition: all 0.2s ease;
    }
    
    .sidebar .sidebar-content .stRadio > div > label:hover {
        color: #56CCF2;
        background-color: rgba(255, 255, 255, 0.2);
    }
    
    .sidebar .sidebar-content .stButton > button {
        background-color: rgba(255, 255, 255, 0.2);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 15px;
        font-weight: 500;
        width: 100%;
        transition: all 0.3s ease;
    }
    
    .sidebar .sidebar-content .stButton > button:hover {
        background-color: rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
    }
    
    /* 로그아웃 버튼 특별 스타일 */
    .logout-button {
        position: fixed;
        bottom: 20px;
        left: 30px;
        width: calc(100% - 60px);
    }
    
    .logout-button button {
        background-color: rgba(255, 255, 255, 0.15) !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
    }
    
    .logout-button button:hover {
        background-color: rgba(255, 255, 255, 0.25) !important;
    }
    
    /* 사이드바 사용자 정보 스타일 */
    .user-info {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .user-info h3 {
        color: white;
        margin: 0;
        font-size: 18px;
        font-weight: 500;
    }
    
    .user-info p {
        color: rgba(255, 255, 255, 0.8);
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    
    /* 메뉴 아이콘 스타일 */
    .menu-icon {
        display: inline-block;
        width: 24px;
        text-align: center;
        margin-right: 8px;
    }
    
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

# 관리자 메뉴 카테고리
st.sidebar.markdown('<div class="menu-category">👨‍💼 관리자 메뉴</div>', unsafe_allow_html=True)

# 관리자 메뉴 항목
admin_pages = {
    "🔑 관리자 및 사용자 관리": "manage_user",
    "📊 작업자 등록 및 관리": "manage_worker",
    "🏭 생산 모델 관리": "manage_model",
    "📋 생산 실적 관리": "manage_production",
    "📉 데이터 관리": "manage_data"
}

# 관리자 메뉴 선택 라디오 버튼
selected_admin_page = st.sidebar.radio("", list(admin_pages.keys()), key="admin_menu")

# 리포트 메뉴 카테고리
st.sidebar.markdown('<div class="menu-category">📈 리포트 메뉴</div>', unsafe_allow_html=True)

# 리포트 메뉴 항목
report_pages = {
    "📊 종합 대시보드": "dashboard",
    "📅 일간 리포트": "daily_report",
    "📆 주간 리포트": "weekly_report",
    "🗓️ 월간 리포트": "monthly_report",
    "📆 연간 리포트": "yearly_report"
}

# 리포트 메뉴 선택 라디오 버튼
selected_report_page = st.sidebar.radio("", list(report_pages.keys()), key="report_menu")

# 선택된 메뉴에 따라 페이지 설정
if selected_admin_page in admin_pages:
    st.session_state.page = admin_pages[selected_admin_page]
elif selected_report_page in report_pages:
    st.session_state.page = report_pages[selected_report_page]

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
    st.markdown("<div class='title-area'><h1>📅 일간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 날짜 선택
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_date = st.date_input("조회 날짜", datetime.now())
    
    # 날짜 표시 카드
    st.markdown(f"""
    <div class='card'>
        <div class='emoji-title'>📅 {selected_date.strftime('%Y년 %m월 %d일')} 품질 현황</div>
        <span class='sub-text'>선택한 날짜의 품질 데이터를 확인하세요</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 주요 품질 지표 (일간)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 일별 주요 품질 지표</div>", unsafe_allow_html=True)
    st.markdown("<span class='sub-text'>선택한 날짜의 시간대별 품질 지표 현황</span>", unsafe_allow_html=True)
    
    # 샘플 데이터
    cols = st.columns(4)
    with cols[0]:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>당일 생산량</span></div>", unsafe_allow_html=True)
        st.metric("", "458", "+23")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전일 대비 생산량이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>당일 불량률</span></div>", unsafe_allow_html=True)
        st.metric("", "0.5%", "-0.3%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전일 대비 불량률이 감소했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>당일 주요 불량</span></div>", unsafe_allow_html=True)
        st.metric("", "치수불량", "")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>가장 많이 발생한 불량 유형입니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>작업자 효율</span></div>", unsafe_allow_html=True)
        st.metric("", "96.8%", "+1.2%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전일 대비 작업 효율이 향상되었습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 시간대별 생산량 및 불량률 차트
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>⏰ 시간대별 생산량 및 불량률</div>", unsafe_allow_html=True)
    
    # 시간대별 데이터
    hours = list(range(8, 21))  # 8시부터 20시까지
    labels = [f"{h}:00" for h in hours]
    
    # 시간대별 생산량 (랜덤 샘플 데이터)
    production_data = np.random.randint(30, 60, len(hours))
    # 시간대별 불량수량 (랜덤 샘플 데이터)
    defect_data = np.random.randint(0, 5, len(hours))
    # 불량률 계산
    defect_rate = (defect_data / production_data * 100).round(2)
    
    # 복합 그래프 생성
    fig = go.Figure()
    
    # 생산량 (막대 그래프)
    fig.add_trace(go.Bar(
        x=labels,
        y=production_data,
        name="생산량",
        marker_color="#4361ee",
        opacity=0.7
    ))
    
    # 불량률 (선 그래프)
    fig.add_trace(go.Scatter(
        x=labels,
        y=defect_rate,
        mode='lines+markers',
        name='불량률 (%)',
        yaxis='y2',
        line=dict(color='#fb8c00', width=3),
        marker=dict(size=8)
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title=f"{selected_date.strftime('%Y년 %m월 %d일')} 시간대별 현황",
        xaxis=dict(title="시간"),
        yaxis=dict(title="생산량 (개)"),
        yaxis2=dict(
            title="불량률 (%)",
            overlaying="y",
            side="right",
            range=[0, max(defect_rate) * 1.5 if max(defect_rate) > 0 else 5]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 발생 유형 분석
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>🔍 일별 불량 유형 분석</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 불량 유형 분포 도넛 차트
        defect_types = ["치수불량", "표면거칠기", "칩핑", "기타불량"]
        defect_counts = np.random.randint(1, 10, len(defect_types))
        
        fig = px.pie(
            values=defect_counts, 
            names=defect_types, 
            hole=0.6,
            color_discrete_sequence=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"]
        )
        
        fig.update_layout(
            title="불량 유형 분포",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # 중앙에 총 불량 수 표시
        total_defects = sum(defect_counts)
        fig.add_annotation(
            text=f"총 불량<br>{total_defects}건",
            x=0.5, y=0.5,
            font_size=15,
            showarrow=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 불량률 모니터링 트렌드
        # 최근 7일 데이터 (오늘 포함)
        last_7_days = [selected_date - timedelta(days=i) for i in range(6, -1, -1)]
        days_labels = [d.strftime("%m/%d") for d in last_7_days]
        
        # 일별 불량률 트렌드 (임의 데이터)
        defect_rates = np.random.uniform(0.3, 1.5, 7).round(2)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days_labels,
            y=defect_rates,
            mode='lines+markers',
            name='일별 불량률',
            line=dict(color='#4cb782', width=3),
            fill='tozeroy',
            fillcolor='rgba(76, 183, 130, 0.1)'
        ))
        
        # 목표선 추가
        fig.add_shape(
            type="line",
            x0=days_labels[0],
            y0=1.0,
            x1=days_labels[-1],
            y1=1.0,
            line=dict(color="red", width=1, dash="dash"),
        )
        
        # 목표선 주석
        fig.add_annotation(
            x=days_labels[1],
            y=1.0,
            text="목표 불량률 (1%)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            arrowsize=1,
            arrowwidth=1,
            ax=-40,
            ay=-30
        )
        
        fig.update_layout(
            title="최근 7일 불량률 트렌드",
            xaxis_title="날짜",
            yaxis_title="불량률 (%)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 작업자별 성능 분석
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>👨‍🔧 작업자별 생산 및 품질 현황</div>", unsafe_allow_html=True)
    
    # 작업자 샘플 데이터
    workers = ["홍길동", "김철수", "이영희", "박민수", "최지영"]
    production = np.random.randint(80, 120, len(workers))
    defect_counts = np.random.randint(0, 5, len(workers))
    defect_rates = (defect_counts / production * 100).round(2)
    efficiency = np.random.uniform(90, 99, len(workers)).round(1)
    
    worker_data = pd.DataFrame({
        "작업자": workers,
        "생산량": production,
        "불량수": defect_counts,
        "불량률(%)": defect_rates,
        "효율(%)": efficiency
    })
    
    st.dataframe(
        worker_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "불량률(%)": st.column_config.ProgressColumn(
                "불량률(%)",
                help="불량률 퍼센트",
                format="%.1f%%",
                min_value=0,
                max_value=5,
            ),
            "효율(%)": st.column_config.ProgressColumn(
                "효율(%)",
                help="작업 효율",
                format="%.1f%%",
                min_value=0,
                max_value=100,
                width="medium"
            ),
        }
    )
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "weekly_report":
    st.markdown("<div class='title-area'><h1>📆 주간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 주차 선택
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_date = st.date_input("기준 날짜", datetime.now())
    
    # 해당 날짜가 속한 주의 시작일과 종료일 계산
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    # 주차 표시 카드
    st.markdown(f"""
    <div class='card'>
        <div class='emoji-title'>📆 {start_of_week.strftime('%Y년 %m월 %d일')} ~ {end_of_week.strftime('%Y년 %m월 %d일')} 주간 품질 현황</div>
        <span class='sub-text'>선택한 주의 품질 데이터를 확인하세요</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 주요 품질 지표 (주간)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 주간 주요 품질 지표</div>", unsafe_allow_html=True)
    st.markdown("<span class='sub-text'>선택한 주의 종합 품질 지표 현황</span>", unsafe_allow_html=True)
    
    # 샘플 데이터
    cols = st.columns(4)
    with cols[0]:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>주간 생산량</span></div>", unsafe_allow_html=True)
        st.metric("", "2,156", "+128")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전주 대비 생산량이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>주간 평균 불량률</span></div>", unsafe_allow_html=True)
        st.metric("", "0.7%", "-0.1%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전주 대비 불량률이 감소했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>불량 감소율</span></div>", unsafe_allow_html=True)
        st.metric("", "12.5%", "+3.2%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>불량 개선율이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>평균 생산성</span></div>", unsafe_allow_html=True)
        st.metric("", "97.2%", "+0.8%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전주 대비 생산성이 향상되었습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 일별 생산량 및 불량률 추이
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📊 일별 생산량 및 불량률 추이</div>", unsafe_allow_html=True)
    
    # 일별 데이터
    week_days = [(start_of_week + timedelta(days=i)).strftime("%m/%d (%a)") for i in range(7)]
    
    # 일별 생산량 (랜덤 샘플 데이터)
    production_data = np.random.randint(250, 350, 7)
    # 일별 불량수량 (랜덤 샘플 데이터)
    defect_data = np.random.randint(1, 8, 7)
    # 불량률 계산
    defect_rate = (defect_data / production_data * 100).round(2)
    
    # 복합 그래프 생성
    fig = go.Figure()
    
    # 생산량 (막대 그래프)
    fig.add_trace(go.Bar(
        x=week_days,
        y=production_data,
        name="생산량",
        marker_color="#4361ee",
        opacity=0.7
    ))
    
    # 불량률 (선 그래프)
    fig.add_trace(go.Scatter(
        x=week_days,
        y=defect_rate,
        mode='lines+markers',
        name='불량률 (%)',
        yaxis='y2',
        line=dict(color='#fb8c00', width=3),
        marker=dict(size=8)
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="주간 일별 생산량 및 불량률 추이",
        xaxis=dict(title="날짜"),
        yaxis=dict(title="생산량 (개)"),
        yaxis2=dict(
            title="불량률 (%)",
            overlaying="y",
            side="right",
            range=[0, max(defect_rate) * 1.5 if max(defect_rate) > 0 else 5]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 주간 공정별 불량률 및 유형 분석
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>🏭 공정별 불량률</div>", unsafe_allow_html=True)
        
        # 공정별 불량률 데이터
        processes = ["선삭", "밀링", "드릴링", "연삭", "조립"]
        process_defect_rates = np.random.uniform(0.3, 1.8, len(processes)).round(2)
        
        # 가로 막대 차트
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=processes,
            x=process_defect_rates,
            orientation='h',
            marker_color=['#4361ee' if rate < 1.0 else '#fb8c00' for rate in process_defect_rates],
            text=[f"{rate}%" for rate in process_defect_rates],
            textposition='outside'
        ))
        
        # 목표선 추가
        fig.add_shape(
            type="line",
            x0=1.0,
            y0=-0.5,
            x1=1.0,
            y1=len(processes) - 0.5,
            line=dict(color="red", width=1, dash="dash"),
        )
        
        fig.update_layout(
            title="공정별 불량률 비교",
            xaxis_title="불량률 (%)",
            yaxis_title="공정",
            margin=dict(l=20, r=20, t=60, b=20),
            xaxis=dict(range=[0, max(process_defect_rates) * 1.2])
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>🔍 주간 주요 불량 유형</div>", unsafe_allow_html=True)
        
        # 불량 유형별 발생 건수
        defect_types = ["치수불량", "표면거칠기", "칩핑", "조립불량", "외관불량"]
        defect_counts = np.random.randint(5, 25, len(defect_types))
        
        # 불량 유형별 추세 표시 (전주 대비)
        prev_counts = np.array([20, 15, 12, 18, 10])  # 전주 데이터 (샘플)
        change_pct = ((defect_counts - prev_counts) / prev_counts * 100).round(1)
        
        # 데이터프레임 생성
        defect_df = pd.DataFrame({
            "불량유형": defect_types,
            "발생건수": defect_counts,
            "전주대비": change_pct,
            "추세": ["⬆️" if c > 0 else "⬇️" if c < 0 else "➡️" for c in change_pct]
        })
        
        # 발생 건수로 정렬
        defect_df = defect_df.sort_values("발생건수", ascending=False).reset_index(drop=True)
        
        # 데이터프레임 표시
        st.dataframe(
            defect_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "전주대비": st.column_config.NumberColumn(
                    "전주대비(%)",
                    format="%.1f%%"
                )
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)
        
    # 품질 지표 개선 트렌드
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📉 품질 지표 개선 트렌드 (최근 8주)</div>", unsafe_allow_html=True)
    
    # 최근 8주 데이터
    last_8_weeks = [(end_of_week - timedelta(days=7*i)).strftime("%m/%d") for i in range(7, -1, -1)]
    
    # 불량률 트렌드 (임의 데이터)
    defect_rates = np.array([1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7])
    
    # 목표값
    target_rate = 1.0
    
    # 그래프 생성
    fig = go.Figure()
    
    # 실제 불량률
    fig.add_trace(go.Scatter(
        x=last_8_weeks,
        y=defect_rates,
        mode='lines+markers',
        name='불량률 추이',
        line=dict(color='#4361ee', width=3),
        marker=dict(size=8)
    ))
    
    # 목표선
    fig.add_trace(go.Scatter(
        x=last_8_weeks,
        y=[target_rate] * len(last_8_weeks),
        mode='lines',
        name='목표 불량률',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="주간 불량률 개선 추이",
        xaxis_title="주차",
        yaxis_title="불량률 (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    # 그래프 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # 목표 달성 여부 표시
    current_rate = defect_rates[-1]
    if current_rate <= target_rate:
        st.success(f"🎉 불량률 목표를 달성했습니다! (목표: {target_rate}%, 현재: {current_rate}%)")
    else:
        st.warning(f"⚠️ 불량률 목표를 달성하지 못했습니다. (목표: {target_rate}%, 현재: {current_rate}%)")
        
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "monthly_report":
    st.markdown("<div class='title-area'><h1>🗓️ 월간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 월 선택
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_date = st.date_input("기준 날짜", datetime.now())
    
    # 월 표시 카드
    st.markdown(f"""
    <div class='card'>
        <div class='emoji-title'>🗓️ {selected_date.strftime('%Y년 %m월')} 품질 현황</div>
        <span class='sub-text'>선택한 월의 품질 데이터를 확인하세요</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 주요 품질 지표 (월간)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 월별 주요 품질 지표</div>", unsafe_allow_html=True)
    st.markdown("<span class='sub-text'>선택한 월의 종합 품질 지표 현황</span>", unsafe_allow_html=True)
    
    # 샘플 데이터
    cols = st.columns(4)
    with cols[0]:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>월간 생산량</span></div>", unsafe_allow_html=True)
        st.metric("", "12,345", "+234")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전월 대비 생산량이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>월간 평균 불량률</span></div>", unsafe_allow_html=True)
        st.metric("", "0.6%", "-0.1%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전월 대비 불량률이 감소했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>불량 감소율</span></div>", unsafe_allow_html=True)
        st.metric("", "10.2%", "+2.1%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>불량 개선율이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>평균 생산성</span></div>", unsafe_allow_html=True)
        st.metric("", "97.9%", "+0.7%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전월 대비 생산성이 향상되었습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 일별 생산량 및 불량률 추이
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📊 일별 생산량 및 불량률 추이</div>", unsafe_allow_html=True)
    
    # 일별 데이터
    month_days = [f"{selected_date.strftime('%m/%d')} ({datetime(selected_date.year, selected_date.month, i).strftime('%a')})" for i in range(1, selected_date.day + 1)]
    
    # 일별 생산량 (랜덤 샘플 데이터)
    production_data = np.random.randint(200, 400, len(month_days))
    # 일별 불량수량 (랜덤 샘플 데이터)
    defect_data = np.random.randint(0, 10, len(month_days))
    # 불량률 계산
    defect_rate = (defect_data / production_data * 100).round(2)
    
    # 복합 그래프 생성
    fig = go.Figure()
    
    # 생산량 (막대 그래프)
    fig.add_trace(go.Bar(
        x=month_days,
        y=production_data,
        name="생산량",
        marker_color="#4361ee",
        opacity=0.7
    ))
    
    # 불량률 (선 그래프)
    fig.add_trace(go.Scatter(
        x=month_days,
        y=defect_rate,
        mode='lines+markers',
        name='불량률 (%)',
        yaxis='y2',
        line=dict(color='#fb8c00', width=3),
        marker=dict(size=8)
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="월간 일별 생산량 및 불량률 추이",
        xaxis=dict(title="날짜"),
        yaxis=dict(title="생산량 (개)"),
        yaxis2=dict(
            title="불량률 (%)",
            overlaying="y",
            side="right",
            range=[0, max(defect_rate) * 1.5 if max(defect_rate) > 0 else 5]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 발생 유형 분석
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>🔍 월별 불량 유형 분석</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 불량 유형 분포 도넛 차트
        defect_types = ["치수불량", "표면거칠기", "칩핑", "조립불량", "외관불량"]
        defect_counts = np.random.randint(1, 10, len(defect_types))
        
        fig = px.pie(
            values=defect_counts, 
            names=defect_types, 
            hole=0.6,
            color_discrete_sequence=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"]
        )
        
        fig.update_layout(
            title="불량 유형 분포",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # 중앙에 총 불량 수 표시
        total_defects = sum(defect_counts)
        fig.add_annotation(
            text=f"총 불량<br>{total_defects}건",
            x=0.5, y=0.5,
            font_size=15,
            showarrow=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 불량률 모니터링 트렌드
        # 최근 7일 데이터 (오늘 포함)
        last_7_days = [selected_date - timedelta(days=i) for i in range(6, -1, -1)]
        days_labels = [d.strftime("%m/%d") for d in last_7_days]
        
        # 일별 불량률 트렌드 (임의 데이터)
        defect_rates = np.random.uniform(0.3, 1.5, 7).round(2)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days_labels,
            y=defect_rates,
            mode='lines+markers',
            name='일별 불량률',
            line=dict(color='#4cb782', width=3),
            fill='tozeroy',
            fillcolor='rgba(76, 183, 130, 0.1)'
        ))
        
        # 목표선 추가
        fig.add_shape(
            type="line",
            x0=days_labels[0],
            y0=1.0,
            x1=days_labels[-1],
            y1=1.0,
            line=dict(color="red", width=1, dash="dash"),
        )
        
        # 목표선 주석
        fig.add_annotation(
            x=days_labels[1],
            y=1.0,
            text="목표 불량률 (1%)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            arrowsize=1,
            arrowwidth=1,
            ax=-40,
            ay=-30
        )
        
        fig.update_layout(
            title="최근 7일 불량률 트렌드",
            xaxis_title="날짜",
            yaxis_title="불량률 (%)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 품질 지표 개선 트렌드
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>�� 품질 지표 개선 트렌드 (최근 8주)</div>", unsafe_allow_html=True)
    
    # 최근 8주 데이터
    last_8_weeks = [(selected_date - timedelta(days=7*i)).strftime("%m/%d") for i in range(7, -1, -1)]
    
    # 불량률 트렌드 (임의 데이터)
    defect_rates = np.array([1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7])
    
    # 그래프 생성
    fig = go.Figure()
    
    # 실제 불량률
    fig.add_trace(go.Scatter(
        x=last_8_weeks,
        y=defect_rates,
        mode='lines+markers',
        name='불량률 추이',
        line=dict(color='#4361ee', width=3),
        marker=dict(size=8)
    ))
    
    # 목표선
    fig.add_trace(go.Scatter(
        x=last_8_weeks,
        y=[1.0] * len(last_8_weeks),
        mode='lines',
        name='목표 불량률',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="최근 8주 불량률 개선 추이",
        xaxis_title="주차",
        yaxis_title="불량률 (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    # 그래프 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # 목표 달성 여부 표시
    current_rate = defect_rates[-1]
    if current_rate <= 1.0:
        st.success(f"🎉 불량률 목표를 달성했습니다! (목표: 1%, 현재: {current_rate}%)")
    else:
        st.warning(f"⚠️ 불량률 목표를 달성하지 못했습니다. (목표: 1%, 현재: {current_rate}%)")
        
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "yearly_report":
    st.markdown("<div class='title-area'><h1>📆 연간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 연도 선택
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_date = st.date_input("기준 날짜", datetime.now())
    
    # 연도 표시 카드
    st.markdown(f"""
    <div class='card'>
        <div class='emoji-title'>📆 {selected_date.strftime('%Y년')} 품질 현황</div>
        <span class='sub-text'>선택한 연도의 품질 데이터를 확인하세요</span>
    </div>
    """, unsafe_allow_html=True)
    
    # 주요 품질 지표 (연간)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 연간 주요 품질 지표</div>", unsafe_allow_html=True)
    st.markdown("<span class='sub-text'>선택한 연도의 종합 품질 지표 현황</span>", unsafe_allow_html=True)
    
    # 샘플 데이터
    cols = st.columns(4)
    with cols[0]:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>연간 생산량</span></div>", unsafe_allow_html=True)
        st.metric("", "145,678", "+12,345")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전년 대비 생산량이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[1]:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>연간 평균 불량률</span></div>", unsafe_allow_html=True)
        st.metric("", "0.5%", "-0.1%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전년 대비 불량률이 감소했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[2]:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>불량 감소율</span></div>", unsafe_allow_html=True)
        st.metric("", "8.2%", "+1.5%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>불량 개선율이 증가했습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with cols[3]:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center;'><span style='font-weight: bold;'>평균 생산성</span></div>", unsafe_allow_html=True)
        st.metric("", "97.8%", "+0.7%")
        st.markdown("<div style='text-align: center; padding-top: 5px;'>전년 대비 생산성이 향상되었습니다.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 일별 생산량 및 불량률 추이
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📊 일별 생산량 및 불량률 추이</div>", unsafe_allow_html=True)
    
    # 일별 데이터
    year_days = [f"{selected_date.strftime('%m/%d')} ({datetime(selected_date.year, i, 1).strftime('%b')})" for i in range(1, 13)]
    
    # 일별 생산량 (랜덤 샘플 데이터)
    production_data = np.random.randint(1000, 2000, len(year_days))
    # 일별 불량수량 (랜덤 샘플 데이터)
    defect_data = np.random.randint(0, 50, len(year_days))
    # 불량률 계산
    defect_rate = (defect_data / production_data * 100).round(2)
    
    # 복합 그래프 생성
    fig = go.Figure()
    
    # 생산량 (막대 그래프)
    fig.add_trace(go.Bar(
        x=year_days,
        y=production_data,
        name="생산량",
        marker_color="#4361ee",
        opacity=0.7
    ))
    
    # 불량률 (선 그래프)
    fig.add_trace(go.Scatter(
        x=year_days,
        y=defect_rate,
        mode='lines+markers',
        name='불량률 (%)',
        yaxis='y2',
        line=dict(color='#fb8c00', width=3),
        marker=dict(size=8)
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="연간 일별 생산량 및 불량률 추이",
        xaxis=dict(title="날짜"),
        yaxis=dict(title="생산량 (개)"),
        yaxis2=dict(
            title="불량률 (%)",
            overlaying="y",
            side="right",
            range=[0, max(defect_rate) * 1.5 if max(defect_rate) > 0 else 5]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 발생 유형 분석
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>🔍 연간 불량 유형 분석</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 불량 유형 분포 도넛 차트
        defect_types = ["치수불량", "표면거칠기", "칩핑", "조립불량", "외관불량"]
        defect_counts = np.random.randint(1, 10, len(defect_types))
        
        fig = px.pie(
            values=defect_counts, 
            names=defect_types, 
            hole=0.6,
            color_discrete_sequence=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"]
        )
        
        fig.update_layout(
            title="불량 유형 분포",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        # 중앙에 총 불량 수 표시
        total_defects = sum(defect_counts)
        fig.add_annotation(
            text=f"총 불량<br>{total_defects}건",
            x=0.5, y=0.5,
            font_size=15,
            showarrow=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 불량률 모니터링 트렌드
        # 최근 7일 데이터 (오늘 포함)
        last_7_days = [selected_date - timedelta(days=i) for i in range(6, -1, -1)]
        days_labels = [d.strftime("%m/%d") for d in last_7_days]
        
        # 일별 불량률 트렌드 (임의 데이터)
        defect_rates = np.random.uniform(0.3, 1.5, 7).round(2)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days_labels,
            y=defect_rates,
            mode='lines+markers',
            name='일별 불량률',
            line=dict(color='#4cb782', width=3),
            fill='tozeroy',
            fillcolor='rgba(76, 183, 130, 0.1)'
        ))
        
        # 목표선 추가
        fig.add_shape(
            type="line",
            x0=days_labels[0],
            y0=1.0,
            x1=days_labels[-1],
            y1=1.0,
            line=dict(color="red", width=1, dash="dash"),
        )
        
        # 목표선 주석
        fig.add_annotation(
            x=days_labels[1],
            y=1.0,
            text="목표 불량률 (1%)",
            showarrow=True,
            arrowhead=2,
            arrowcolor="red",
            arrowsize=1,
            arrowwidth=1,
            ax=-40,
            ay=-30
        )
        
        fig.update_layout(
            title="최근 7일 불량률 트렌드",
            xaxis_title="날짜",
            yaxis_title="불량률 (%)",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 품질 지표 개선 트렌드
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📉 품질 지표 개선 트렌드 (최근 8주)</div>", unsafe_allow_html=True)
    
    # 최근 8주 데이터
    last_8_weeks = [(selected_date - timedelta(days=7*i)).strftime("%m/%d") for i in range(7, -1, -1)]
    
    # 불량률 트렌드 (임의 데이터)
    defect_rates = np.array([1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7])
    
    # 그래프 생성
    fig = go.Figure()
    
    # 실제 불량률
    fig.add_trace(go.Scatter(
        x=last_8_weeks,
        y=defect_rates,
        mode='lines+markers',
        name='불량률 추이',
        line=dict(color='#4361ee', width=3),
        marker=dict(size=8)
    ))
    
    # 목표선
    fig.add_trace(go.Scatter(
        x=last_8_weeks,
        y=[1.0] * len(last_8_weeks),
        mode='lines',
        name='목표 불량률',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # 레이아웃 업데이트
    fig.update_layout(
        title="최근 8주 불량률 개선 추이",
        xaxis_title="주차",
        yaxis_title="불량률 (%)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="x"
    )
    
    # 그래프 표시
    st.plotly_chart(fig, use_container_width=True)
    
    # 목표 달성 여부 표시
    current_rate = defect_rates[-1]
    if current_rate <= 1.0:
        st.success(f"🎉 불량률 목표를 달성했습니다! (목표: 1%, 현재: {current_rate}%)")
    else:
        st.warning(f"⚠️ 불량률 목표를 달성하지 못했습니다. (목표: 1%, 현재: {current_rate}%)")
        
    st.markdown("</div>", unsafe_allow_html=True)

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