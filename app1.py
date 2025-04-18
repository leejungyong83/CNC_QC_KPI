import streamlit as st
from supabase import create_client
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
import httpx

# Supabase 초기화
try:
    # Supabase 연결 (가장 기본적인 형태)
    # 매개변수를 위치 기반으로만 전달
    supabase = create_client(
        "https://czfvtkbndsfoznmknwsx.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6ZnZ0a2JuZHNmb3pubWtud3N4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxNTE1NDIsImV4cCI6MjA1ODcyNzU0Mn0.IpbN__1zImksnMo22CghSLTA-UCGoI67hHoDkrNpQGE"
    )
except Exception as e:
    st.error(f"데이터베이스 연결에 실패했습니다: {str(e)}")
    st.stop()

# 페이지 설정
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
</style>
""", unsafe_allow_html=True)

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
st.sidebar.success(f"{st.session_state.username}님 환영합니다!")
st.sidebar.write(f"역할: {st.session_state.user_role}")

# 세션 유지를 위한 요소 추가
add_keep_alive_element()

# 로그아웃 버튼
if st.sidebar.button("로그아웃"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = "일반"
    st.session_state.page = "login"
    st.rerun()

# 언어 선택 (한국어/베트남어)
TRANSLATIONS = {
    "ko": {
        "title": "ALMUS TECH CNC 작업자 KPI 관리 시스템",
        "menu_groups": {
            "admin": "관리자 메뉴",
            "report": "리포트 메뉴"
        },
        "admin_menu": {
            "manager_auth": "👥 관리자 및 사용자 관리",
            "process_auth": "⚙️ 관리자 동록 및 관리",
            "user_auth": "🔑 사용자 등록 및 관리",
            "inspection_data": "📊 검사실적 관리"
        },
        "report_menu": {
            "total_dashboard": "📈 종합 대시보드",
            "daily_report": "📊 일간 리포트",
            "weekly_report": "📅 주간 리포트",
            "monthly_report": "📆 월간 리포트",
            "quality_report": "⭐ 월간 품질 리포트"
        }
    },
    "vi": {
        "title": "Hệ thống quản lý KPI cho công nhân CNC ALMUS TECH",
        "menu_groups": {
            "admin": "Menu quản trị",
            "report": "Menu báo cáo"
        },
        "admin_menu": {
            "manager_auth": "👥 Quản lý quản trị viên và người dùng",
            "process_auth": "⚙️ Đăng ký và quản lý quản trị viên",
            "user_auth": "🔑 Đăng ký và quản lý người dùng",
            "inspection_data": "📊 Quản lý dữ liệu kiểm tra"
        },
        "report_menu": {
            "total_dashboard": "📈 Bảng điều khiển tổng hợp",
            "daily_report": "📊 Báo cáo hàng ngày",
            "weekly_report": "📅 Báo cáo hàng tuần",
            "monthly_report": "📆 Báo cáo hàng tháng",
            "quality_report": "⭐ Báo cáo chất lượng hàng tháng"
        }
    }
}

# 초기 언어 설정
if 'language' not in st.session_state:
    st.session_state.language = 'ko'

# 사이드바에 언어 선택 추가
lang_col1, lang_col2 = st.sidebar.columns(2)
with lang_col1:
    if st.button("한국어", key="ko_btn"):
        st.session_state.language = 'ko'
        st.rerun()
with lang_col2:
    if st.button("Tiếng Việt", key="vi_btn"):
        st.session_state.language = 'vi'
        st.rerun()

# 현재 선택된 언어의 번역 가져오기
curr_lang = TRANSLATIONS[st.session_state.language]

# 메뉴 페이지 정의
if 'page' not in st.session_state:
    st.session_state.page = "total_dashboard"

# 관리자 메뉴 섹션
st.sidebar.markdown(f"### {curr_lang['menu_groups']['admin']}")
admin_menu = curr_lang['admin_menu']
selected_admin = st.sidebar.radio(
    label="",
    options=list(admin_menu.keys()),
    format_func=lambda x: admin_menu[x],
    key="admin_menu", 
    index=0
)

# 리포트 메뉴 섹션
st.sidebar.markdown(f"### {curr_lang['menu_groups']['report']}")
report_menu = curr_lang['report_menu']
selected_report = st.sidebar.radio(
    label="",
    options=list(report_menu.keys()),
    format_func=lambda x: report_menu[x],
    key="report_menu",
    index=0
)

# 선택된 메뉴에 따라 페이지 상태 업데이트
if selected_admin in admin_menu:
    st.session_state.page = selected_admin
elif selected_report in report_menu:
    st.session_state.page = selected_report

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
if st.session_state.page == "total_dashboard":
    # 상단 헤더 섹션
    st.markdown("<div class='title-area'><h1>🏭 CNC 품질관리 시스템 - 대시보드</h1></div>", unsafe_allow_html=True)
    
    # 상단 메트릭 섹션 (2x2 그리드)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("📝 총 검사 건수", "152", "+12")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("⚠️ 평균 불량률", "0.8%", "-0.2%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("🔍 최다 불량 유형", "치수불량", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("⚙️ 진행 중인 작업", "3", "+1")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 날짜 필터 (메트릭 카드 아래에 통합)
    col1, col2 = st.columns([1, 1])
    with col1:
        start_date = st.date_input("📅 시작일", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("📅 종료일", datetime.now())
    
    # 차트 섹션 (2x1 그리드)
    col1, col2 = st.columns(2)
    
    with col1:
        # 일별 불량률 추이 차트
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>📊 일별 불량률 추이 (최근 7일)</div>", unsafe_allow_html=True)
        
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
    
    # 최근 검사 데이터 섹션 (전체 너비)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📋 최근 검사 데이터</div>", unsafe_allow_html=True)
    
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

elif st.session_state.page == "input_inspection":
    st.title("📝 검사 데이터 입력")
    
    # 기본 정보 입력
    with st.form("basic_info"):
        st.subheader("📋 기본 정보 입력")
        
        col1, col2 = st.columns(2)
        with col1:
            inspector = st.selectbox("👤 검사원", options=st.session_state.inspectors['name'].tolist())
            process = st.selectbox("⚙️ 공정", options=["선삭", "밀링"])
            
        with col2:
            date = st.date_input("📅 검사일자")
            time = st.time_input("⏰ 검사시간")
            
        lot_number = st.text_input("🔢 LOT 번호")
        total_quantity = st.number_input("📦 전체 수량", min_value=1, value=1)
        
        submit_basic = st.form_submit_button("✅ 기본 정보 등록")
        
    if submit_basic:
        st.session_state.basic_info_valid = True
        st.success("✅ 기본 정보가 등록되었습니다.")
    else:
        st.session_state.basic_info_valid = False

    # 불량 정보 입력
    if st.session_state.get('basic_info_valid', False):
        with st.form("defect_info"):
            st.subheader("⚠️ 불량 정보 입력")
            
            col1, col2 = st.columns(2)
            with col1:
                defect_type = st.selectbox("🔍 불량 유형", 
                    options=["치수", "표면거칠기", "칩핑", "기타"])
            
            with col2:
                defect_quantity = st.number_input("📊 불량 수량", 
                    min_value=1, max_value=total_quantity, value=1)
                
            submit_defect = st.form_submit_button("➕ 불량 등록")
            
        if submit_defect:
            new_defect = {
                "type": defect_type,
                "quantity": defect_quantity
            }
            st.session_state.registered_defects.append(new_defect)
            st.success(f"✅ {defect_type} 불량이 {defect_quantity}개 등록되었습니다.")
            
        # 등록된 불량 정보 표시
        if st.session_state.registered_defects:
            st.subheader("📋 등록된 불량 정보")
            defects_df = pd.DataFrame(st.session_state.registered_defects)
            st.dataframe(defects_df)
            
            total_defects = defects_df['quantity'].sum()
            defect_rate = (total_defects / total_quantity) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 총 불량 수량", f"{total_defects}개")
            with col2:
                st.metric("📈 불량률", f"{defect_rate:.2f}%")
                
        # 불량 목록 초기화 버튼
        if st.button("🔄 불량 목록 초기화"):
            st.session_state.registered_defects = []
            st.success("✅ 불량 목록이 초기화되었습니다.")
            st.stop()
            
        # 검사 데이터 저장
        if st.button("💾 검사 데이터 저장"):
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
                    
                    st.success("✅ 검사 데이터가 성공적으로 저장되었습니다.")
                    st.session_state.registered_defects = []
                    st.stop()
                except Exception as e:
                    st.error(f"❌ 데이터 저장 중 오류가 발생했습니다: {str(e)}")
            else:
                st.warning("⚠️ 저장할 불량 데이터가 없습니다.")

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

elif st.session_state.page == "daily_report":
    # 일간 리포트 페이지
    st.markdown("<div class='title-area'><h1>📊 일간 리포트</h1></div>", unsafe_allow_html=True)
    
    # 날짜 선택
    selected_date = st.date_input("📅 조회할 날짜 선택", datetime.now())
    
    # 데이터 로딩 표시
    with st.spinner("데이터 불러오는 중..."):
        time.sleep(0.5)  # 데이터 로딩 시뮬레이션
        
    # 일간 요약 지표
    st.subheader("일간 품질 요약")
    
    # 4개의 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("당일 검사 건수", "28", "+3")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("당일 불량률", "0.65%", "-0.1%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("주요 불량 유형", "표면거칠기", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("평균 검사 시간", "8.2분", "-0.5분")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 시간대별 검사 추이
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>⏰ 시간대별 검사 건수</div>", unsafe_allow_html=True)
    
    # 시간대별 데이터 준비
    hours = list(range(9, 18))  # 9시부터 17시까지
    hourly_inspections = np.random.randint(3, 15, size=len(hours))
    
    # 시간대별 검사 건수 차트
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{h}:00" for h in hours],
        y=hourly_inspections,
        marker_color="#4361ee",
        hovertemplate='시간: %{x}<br>검사 건수: %{y}건<extra></extra>'
    ))
    
    fig.update_layout(
        title=None,
        xaxis_title="시간",
        yaxis_title="검사 건수",
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 발생 현황
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>🔍 불량 발생 현황</div>", unsafe_allow_html=True)
    
    # 불량 타입별 데이터
    defect_types = ["치수 불량", "표면 거칠기", "칩핑", "기타"]
    defect_counts = np.random.randint(1, 8, size=len(defect_types))
    
    # 차트
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # 막대 그래프
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=defect_types,
            y=defect_counts,
            orientation='h',
            marker_color=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"],
            hovertemplate='유형: %{y}<br>건수: %{x}건<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="발생 건수",
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # 불량 요약 통계
        total_defects = sum(defect_counts)
        total_inspected = sum(hourly_inspections)
        defect_rate = (total_defects / total_inspected) * 100
        
        st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='font-size: 24px;'>총 불량 건수</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='font-size: 36px; color: #4361ee;'>{total_defects}건</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-size: 18px;'>불량률: {defect_rate:.2f}%</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 세부 테이블
    defect_details = {
        "시간": [f"{np.random.choice(hours)}:00" for _ in range(total_defects)],
        "LOT번호": [f"LOT{i:04d}" for i in range(1, total_defects + 1)],
        "불량유형": np.random.choice(defect_types, total_defects),
        "불량수량": np.random.randint(1, 5, total_defects)
    }
    
    defect_df = pd.DataFrame(defect_details)
    st.dataframe(defect_df, use_container_width=True, hide_index=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "weekly_report":
    # 주간 리포트 페이지
    st.markdown("<div class='title-area'><h1>📅 주간 리포트</h1></div>", unsafe_allow_html=True)
    
    # 주간 선택기
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    col1, col2 = st.columns(2)
    with col1:
        week_start = st.date_input("📅 주간 시작일", start_of_week)
    with col2:
        week_end = st.date_input("📅 주간 종료일", end_of_week)
    
    # 데이터 로딩 표시
    with st.spinner("주간 데이터 불러오는 중..."):
        time.sleep(0.5)  # 데이터 로딩 시뮬레이션
    
    # 주간 요약 지표
    st.subheader("주간 품질 요약")
    
    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("주간 검사 건수", "143", "+12")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("주간 불량률", "0.72%", "-0.08%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("주요 불량 유형", "치수불량", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("주간 목표 달성", "95.2%", "+2.1%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 일별 추이 차트
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 일별 검사 및 불량 추이</div>", unsafe_allow_html=True)
    
    # 요일 데이터
    weekdays = ["월", "화", "수", "목", "금", "토", "일"]
    inspections = np.random.randint(15, 35, size=7)
    defect_rates = np.random.rand(7) * 1.5  # 0~1.5% 사이의 불량률
    
    # 이중 Y축 차트
    fig = go.Figure()
    
    # 첫 번째 Y축: 검사 건수 (막대)
    fig.add_trace(go.Bar(
        x=weekdays,
        y=inspections,
        name="검사 건수",
        marker_color="#4361ee",
        yaxis="y",
        hovertemplate='%{x}요일<br>검사 건수: %{y}건<extra></extra>',
        opacity=0.8
    ))
    
    # 두 번째 Y축: 불량률 (선)
    fig.add_trace(go.Scatter(
        x=weekdays,
        y=defect_rates,
        name="불량률",
        marker=dict(size=8),
        line=dict(color="#fb8c00", width=3),
        mode="lines+markers",
        yaxis="y2",
        hovertemplate='%{x}요일<br>불량률: %{y:.2f}%<extra></extra>'
    ))
    
    # 목표 불량률 라인
    target_rate = 1.0
    fig.add_trace(go.Scatter(
        x=weekdays,
        y=[target_rate] * 7,
        name="목표 불량률",
        line=dict(color="red", width=2, dash="dash"),
        mode="lines",
        yaxis="y2",
        hovertemplate='목표 불량률: %{y}%<extra></extra>'
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title=None,
        xaxis=dict(title="요일"),
        yaxis=dict(
            title="검사 건수",
            side="left",
            showgrid=False
        ),
        yaxis2=dict(
            title="불량률 (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, max(defect_rates) * 1.2]  # Y축 범위 설정
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 유형 및 공정별 분석
    col1, col2 = st.columns(2)
    
    with col1:
        # 불량 유형 분석
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>🔍 불량 유형 분석</div>", unsafe_allow_html=True)
        
        # 불량 유형별 데이터
        defect_types = ["치수 불량", "표면 거칠기", "칩핑", "기타"]
        defect_counts = np.random.randint(5, 20, size=len(defect_types))
        
        # 수평 막대 그래프
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=defect_types,
            x=defect_counts,
            orientation='h',
            marker_color=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"],
            hovertemplate='유형: %{y}<br>건수: %{x}건<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="발생 건수",
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # 공정별 불량률
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>⚙️ 공정별 불량률</div>", unsafe_allow_html=True)
        
        # 공정별 데이터
        processes = ["선삭", "밀링", "연삭", "조립"]
        process_rates = np.random.rand(len(processes)) * 1.8  # 0~1.8% 불량률
        
        # 공정별 불량률 차트
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=processes,
            y=process_rates,
            marker_color="#4cb782",
            hovertemplate='공정: %{x}<br>불량률: %{y:.2f}%<extra></extra>'
        ))
        
        # 평균 불량률 라인
        avg_rate = np.mean(process_rates)
        fig.add_trace(go.Scatter(
            x=processes,
            y=[avg_rate] * len(processes),
            mode="lines",
            name="평균",
            line=dict(color="#fb8c00", width=2, dash="dash"),
            hovertemplate='평균 불량률: %{y:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="공정",
            yaxis_title="불량률 (%)",
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 주간 검사 데이터 테이블
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📋 주간 검사 데이터 요약</div>", unsafe_allow_html=True)
    
    # 샘플 데이터
    weekly_data = {
        "요일": weekdays,
        "검사 건수": inspections,
        "불량 건수": [int(rate * inspection / 100) for rate, inspection in zip(defect_rates, inspections)],
        "불량률 (%)": defect_rates.round(2),
        "주요 불량 유형": np.random.choice(defect_types, size=7)
    }
    
    weekly_df = pd.DataFrame(weekly_data)
    st.dataframe(weekly_df, use_container_width=True, hide_index=True)
    
    # 주간 요약 통계
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_inspection = int(np.mean(inspections))
        st.metric("📊 평균 일일 검사 건수", f"{avg_inspection}건")
    with col2:
        avg_defect_rate = np.mean(defect_rates)
        st.metric("⚠️ 평균 불량률", f"{avg_defect_rate:.2f}%")
    with col3:
        total_inspections = sum(inspections)
        st.metric("📈 총 검사 건수", f"{total_inspections}건")
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "monthly_report":
    # 월간 리포트 페이지
    st.markdown("<div class='title-area'><h1>📆 월간 리포트</h1></div>", unsafe_allow_html=True)
    
    # 월 선택
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("연도 선택", options=list(range(current_year-2, current_year+1)), index=2)
    with col2:
        selected_month = st.selectbox("월 선택", options=list(range(1, 13)), index=current_month-1)
    
    # 선택된 월의 문자열 표현
    month_names = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
    selected_month_name = month_names[selected_month-1]
    
    # 데이터 로딩 표시
    with st.spinner(f"{selected_year}년 {selected_month_name} 데이터 불러오는 중..."):
        time.sleep(0.5)  # 데이터 로딩 시뮬레이션
    
    # 월간 요약 지표
    st.subheader(f"{selected_year}년 {selected_month_name} 품질 요약")
    
    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("월간 검사 건수", "587", "+23")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("월간 불량률", "0.68%", "-0.12%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("주요 불량 유형", "표면거칠기", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("월간 목표 달성", "97.8%", "+1.5%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 월간 추이 차트
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 일별 불량률 추이</div>", unsafe_allow_html=True)
    
    # 선택된 월의 일수 계산
    import calendar
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    
    # 일자 데이터
    days = list(range(1, days_in_month + 1))
    # 불량률 데이터 (평균 0.7% 주변에서 랜덤 변동)
    daily_defect_rates = [0.7 + (np.random.rand() - 0.5) / 2 for _ in range(days_in_month)]
    
    # 차트 생성
    fig = go.Figure()
    
    # 불량률 라인
    fig.add_trace(go.Scatter(
        x=days,
        y=daily_defect_rates,
        mode="lines+markers",
        name="일별 불량률",
        line=dict(color="#4361ee", width=2),
        marker=dict(size=6),
        hovertemplate='%{x}일<br>불량률: %{y:.2f}%<extra></extra>'
    ))
    
    # 평균 불량률 라인
    avg_rate = np.mean(daily_defect_rates)
    fig.add_trace(go.Scatter(
        x=[days[0], days[-1]],
        y=[avg_rate, avg_rate],
        mode="lines",
        name="평균 불량률",
        line=dict(color="#4cb782", width=2, dash="dash"),
        hovertemplate='평균 불량률: %{y:.2f}%<extra></extra>'
    ))
    
    # 목표 불량률 라인
    target_rate = 1.0
    fig.add_trace(go.Scatter(
        x=[days[0], days[-1]],
        y=[target_rate, target_rate],
        mode="lines",
        name="목표 불량률",
        line=dict(color="red", width=2, dash="dot"),
        hovertemplate='목표 불량률: %{y:.2f}%<extra></extra>'
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title=None,
        xaxis=dict(
            title="일자",
            tickmode='linear',
            tick0=1,
            dtick=3,  # 3일 간격으로 표시
        ),
        yaxis=dict(
            title="불량률 (%)",
            range=[0, max(daily_defect_rates) * 1.5]  # Y축 범위 설정
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 공정 및 불량 분석
    col1, col2 = st.columns(2)
    
    with col1:
        # 공정별 불량률 비교
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>⚙️ 공정별 불량률 비교</div>", unsafe_allow_html=True)
        
        # 공정별 데이터
        processes = ["선삭", "밀링", "연삭", "드릴링", "조립"]
        process_inspections = np.random.randint(80, 150, size=len(processes))
        process_defect_rates = np.random.rand(len(processes)) * 1.5  # 0~1.5% 불량률
        
        # 공정별 불량률 및 검사 건수를 함께 표시하는 차트
        process_df = pd.DataFrame({
            "공정": processes,
            "검사건수": process_inspections,
            "불량률": process_defect_rates
        })
        
        # 검사건수에 비례한 버블 크기로 표시
        fig = px.scatter(
            process_df,
            x="공정",
            y="불량률",
            size="검사건수",
            color="공정",
            size_max=50,
            hover_name="공정",
            hover_data={"공정": False, "검사건수": True, "불량률": ":.2f%"},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig.update_layout(
            title=None,
            xaxis_title=None,
            yaxis_title="불량률 (%)",
            showlegend=False,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=320
        )
        
        # 불량률의 평균선 추가
        avg_process_rate = np.mean(process_defect_rates)
        fig.add_shape(
            type="line",
            x0=-0.5, y0=avg_process_rate,
            x1=len(processes)-0.5, y1=avg_process_rate,
            line=dict(color="#4cb782", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=processes[1],
            y=avg_process_rate,
            text=f"평균: {avg_process_rate:.2f}%",
            showarrow=False,
            yshift=10,
            font=dict(size=12, color="#4cb782")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # 불량 유형 분포
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>🔍 불량 유형 분포</div>", unsafe_allow_html=True)
        
        # 불량 유형별 데이터
        defect_types = ["치수 불량", "표면 거칠기", "칩핑", "소재 결함", "조립 불량", "기타"]
        defect_percents = np.random.rand(len(defect_types))
        defect_percents = (defect_percents / defect_percents.sum()) * 100  # 백분율로 변환
        
        # 불량 유형 파이 차트
        fig = go.Figure(data=[go.Pie(
            labels=defect_types,
            values=defect_percents,
            hole=.4,
            textinfo="percent+label",
            insidetextorientation="radial",
            marker=dict(colors=px.colors.qualitative.Bold),
            hovertemplate='%{label}<br>비율: %{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            title=None,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=320,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 주별 성능 추이
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📊 주별 성능 추이</div>", unsafe_allow_html=True)
    
    # 주차 데이터 (보통 한 달에 4-5주)
    weeks = [f"{selected_month}월 1주차", f"{selected_month}월 2주차", 
            f"{selected_month}월 3주차", f"{selected_month}월 4주차"]
    if days_in_month > 28:
        weeks.append(f"{selected_month}월 5주차")
    
    # 주별 검사 건수 및 불량률
    weekly_inspections = np.random.randint(120, 180, size=len(weeks))
    weekly_defect_rates = np.random.rand(len(weeks)) * 1.2  # 0~1.2% 불량률
    
    # 복합 차트 (막대 + 선)
    fig = go.Figure()
    
    # 검사 건수 (막대)
    fig.add_trace(go.Bar(
        x=weeks,
        y=weekly_inspections,
        name="검사 건수",
        marker_color="#4361ee",
        yaxis="y",
        hovertemplate='%{x}<br>검사 건수: %{y}건<extra></extra>',
        opacity=0.8
    ))
    
    # 불량률 (선)
    fig.add_trace(go.Scatter(
        x=weeks,
        y=weekly_defect_rates,
        name="불량률",
        yaxis="y2",
        line=dict(color="#fb8c00", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        hovertemplate='%{x}<br>불량률: %{y:.2f}%<extra></extra>'
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title=None,
        xaxis=dict(title="주차"),
        yaxis=dict(
            title="검사 건수",
            side="left",
            showgrid=False
        ),
        yaxis2=dict(
            title="불량률 (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, max(weekly_defect_rates) * 1.3]  # Y축 범위 설정
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 주별 요약 테이블
    weekly_summary = pd.DataFrame({
        "주차": weeks,
        "검사 건수": weekly_inspections,
        "불량 건수": [int(rate * inspection / 100) for rate, inspection in zip(weekly_defect_rates, weekly_inspections)],
        "불량률 (%)": weekly_defect_rates.round(2),
        "목표 달성 여부": [rate < 1.0 for rate in weekly_defect_rates]
    })
    
    # 테이블 형식 조정
    st.dataframe(
        weekly_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "불량률 (%)": st.column_config.ProgressColumn(
                "불량률 (%)",
                help="주별 불량률 퍼센트",
                format="%.2f%%",
                min_value=0,
                max_value=2,
            ),
            "목표 달성 여부": st.column_config.CheckboxColumn(
                "목표 달성 여부",
                help="불량률 1% 이하 목표 달성 여부"
            )
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "manager_auth":
    # 관리자 및 사용자 관리 페이지
    st.markdown("<div class='title-area'><h1>👥 관리자 및 사용자 관리</h1></div>", unsafe_allow_html=True)
    
    # 관리자 권한 확인
    if st.session_state.user_role != "관리자":
        st.warning("이 페이지는 관리자만 접근할 수 있습니다.")
        st.stop()
    
    # 탭 구성
    tab1, tab2 = st.tabs(["👤 사용자 관리", "🔑 권한 설정"])
    
    with tab1:
        # 사용자 관리 섹션
        st.subheader("등록된 사용자 목록")
        
        # 샘플 사용자 데이터
        users_data = {
            "아이디": ["admin", "user1", "user2", "manager1", "operator1"],
            "이름": ["관리자", "홍길동", "김철수", "이부장", "박작업"],
            "역할": ["관리자", "일반", "일반", "관리자", "일반"],
            "부서": ["관리부", "생산부", "품질부", "생산부", "생산부"],
            "최근 접속일": [
                (datetime.now() - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
            ],
            "상태": ["활성", "활성", "비활성", "활성", "활성"]
        }
        
        users_df = pd.DataFrame(users_data)
        
        # 사용자 목록 필터링
        col1, col2 = st.columns(2)
        with col1:
            role_filter = st.selectbox("역할 필터", options=["전체", "관리자", "일반"])
        with col2:
            status_filter = st.selectbox("상태 필터", options=["전체", "활성", "비활성"])
        
        # 필터 적용
        filtered_df = users_df.copy()
        if role_filter != "전체":
            filtered_df = filtered_df[filtered_df["역할"] == role_filter]
        if status_filter != "전체":
            filtered_df = filtered_df[filtered_df["상태"] == status_filter]
        
        # 필터링된 사용자 목록 표시
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # 새 사용자 등록 폼
        st.subheader("새 사용자 등록")
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("아이디")
                new_user_name = st.text_input("이름")
                new_user_dept = st.selectbox("부서", options=["관리부", "생산부", "품질부", "기술부"])
            with col2:
                new_user_password = st.text_input("비밀번호", type="password")
                new_user_password_confirm = st.text_input("비밀번호 확인", type="password")
                new_user_role = st.selectbox("역할", options=["일반", "관리자"])
            
            submit_user = st.form_submit_button("사용자 등록")
            
        if submit_user:
            if not new_user_id or not new_user_name or not new_user_password:
                st.error("필수 항목을 모두 입력하세요.")
            elif new_user_password != new_user_password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif new_user_id in users_df["아이디"].values:
                st.error("이미 존재하는 아이디입니다.")
            else:
                st.success(f"사용자 '{new_user_name}'이(가) 성공적으로 등록되었습니다.")
                st.info("실제 데이터베이스 연동 시 사용자 정보가 저장됩니다.")
    
    with tab2:
        # 권한 설정 섹션
        st.subheader("사용자 권한 설정")
        
        # 권한 설정할 사용자 선택
        selected_user = st.selectbox(
            "권한을 설정할 사용자 선택",
            options=users_df["아이디"].tolist(),
            format_func=lambda x: f"{x} ({users_df[users_df['아이디'] == x]['이름'].values[0]})"
        )
        
        # 선택된 사용자의 정보 표시
        user_info = users_df[users_df["아이디"] == selected_user].iloc[0]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("현재 역할", user_info["역할"])
        with col2:
            st.metric("소속 부서", user_info["부서"])
        with col3:
            st.metric("계정 상태", user_info["상태"])
        
        # 권한 설정 옵션
        st.subheader("권한 설정")
        
        col1, col2 = st.columns(2)
        with col1:
            new_role = st.radio("역할", options=["일반", "관리자"], index=0 if user_info["역할"] == "일반" else 1)
        with col2:
            new_status = st.radio("상태", options=["활성", "비활성"], index=0 if user_info["상태"] == "활성" else 1)
        
        # 메뉴별 접근 권한
        st.subheader("메뉴별 접근 권한")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**관리자 메뉴**")
            admin_auth = {
                "사용자 관리": st.checkbox("사용자 관리", value=user_info["역할"] == "관리자"),
                "공정 관리": st.checkbox("공정 관리", value=user_info["역할"] == "관리자"),
                "검사 관리": st.checkbox("검사 관리", value=True),
                "시스템 설정": st.checkbox("시스템 설정", value=user_info["역할"] == "관리자")
            }
        
        with col2:
            st.markdown("**리포트 메뉴**")
            report_auth = {
                "종합 대시보드": st.checkbox("종합 대시보드", value=True),
                "일간 리포트": st.checkbox("일간 리포트", value=True),
                "주간 리포트": st.checkbox("주간 리포트", value=True),
                "월간 리포트": st.checkbox("월간 리포트", value=user_info["역할"] == "관리자")
            }
        
        # 권한 저장 버튼
        if st.button("권한 설정 저장"):
            st.success(f"사용자 '{selected_user}'의 권한이 성공적으로 업데이트되었습니다.")
            st.info("실제 데이터베이스 연동 시 권한 정보가 저장됩니다.")

elif st.session_state.page == "process_auth":
    # 관리자 등록 및 관리 페이지
    st.markdown("<div class='title-area'><h1>⚙️ 관리자 등록 및 관리</h1></div>", unsafe_allow_html=True)
    
    # 관리자 권한 확인
    if st.session_state.user_role != "관리자":
        st.warning("이 페이지는 관리자만 접근할 수 있습니다.")
        st.stop()
    
    # 탭 구성
    tab1, tab2 = st.tabs(["📋 관리자 목록", "➕ 관리자 등록"])
    
    with tab1:
        # 관리자 목록 섹션
        st.subheader("등록된 관리자 목록")
        
        # 샘플 관리자 데이터
        admin_data = {
            "아이디": ["admin", "manager1", "manager2", "supervisor1"],
            "이름": ["시스템 관리자", "이부장", "김과장", "최대리"],
            "직급": ["관리자", "부장", "과장", "대리"],
            "부서": ["IT부", "생산부", "품질부", "관리부"],
            "권한레벨": ["최고관리자", "부서관리자", "부서관리자", "부서관리자"],
            "계정생성일": [
                (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            ],
            "상태": ["활성", "활성", "활성", "비활성"]
        }
        
        admin_df = pd.DataFrame(admin_data)
        
        # 관리자 목록 필터링
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("부서 필터", options=["전체", "IT부", "생산부", "품질부", "관리부"])
        with col2:
            status_filter = st.selectbox("상태 필터", options=["전체", "활성", "비활성"])
        
        # 필터 적용
        filtered_df = admin_df.copy()
        if dept_filter != "전체":
            filtered_df = filtered_df[filtered_df["부서"] == dept_filter]
        if status_filter != "전체":
            filtered_df = filtered_df[filtered_df["상태"] == status_filter]
        
        # 필터링된 관리자 목록 표시
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # 선택한 관리자 상세 정보 및 권한 관리
        selected_admin = st.selectbox(
            "상세 정보를 볼 관리자 선택",
            options=filtered_df["아이디"].tolist(),
            format_func=lambda x: f"{x} ({filtered_df[filtered_df['아이디'] == x]['이름'].values[0]})"
        )
        
        if selected_admin:
            st.subheader(f"관리자 상세 정보: {selected_admin}")
            
            # 선택된 관리자 정보
            admin_info = filtered_df[filtered_df["아이디"] == selected_admin].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("이름", admin_info["이름"])
                st.metric("직급", admin_info["직급"])
            with col2:
                st.metric("부서", admin_info["부서"])
                st.metric("권한레벨", admin_info["권한레벨"])
            with col3:
                st.metric("계정생성일", admin_info["계정생성일"])
                st.metric("상태", admin_info["상태"])
            
            # 계정 활성화/비활성화 버튼
            col1, col2 = st.columns(2)
            with col1:
                if admin_info["상태"] == "활성":
                    if st.button(f"'{admin_info['이름']}' 계정 비활성화", key="deactivate_admin"):
                        st.warning(f"'{admin_info['이름']}' 계정이 비활성화되었습니다.")
                        st.info("실제 데이터베이스 연동 시 상태가 변경됩니다.")
                else:
                    if st.button(f"'{admin_info['이름']}' 계정 활성화", key="activate_admin"):
                        st.success(f"'{admin_info['이름']}' 계정이 활성화되었습니다.")
                        st.info("실제 데이터베이스 연동 시 상태가 변경됩니다.")
            
            with col2:
                if st.button(f"'{admin_info['이름']}' 비밀번호 초기화", key="reset_admin_pwd"):
                    st.success(f"'{admin_info['이름']}' 계정의 비밀번호가 초기화되었습니다.")
                    st.code("임시 비밀번호: Admin@1234")
                    st.info("실제 데이터베이스 연동 시 비밀번호가 변경됩니다.")
            
            # 권한 레벨 변경
            st.subheader("권한 레벨 변경")
            new_auth_level = st.radio(
                "권한 레벨 선택",
                options=["최고관리자", "부서관리자", "일반관리자"],
                index=0 if admin_info["권한레벨"] == "최고관리자" else 
                      1 if admin_info["권한레벨"] == "부서관리자" else 2
            )
            
            if st.button("권한 레벨 변경 저장"):
                st.success(f"'{admin_info['이름']}' 계정의 권한 레벨이 '{new_auth_level}'로 변경되었습니다.")
                st.info("실제 데이터베이스 연동 시 권한이 변경됩니다.")
    
    with tab2:
        # 관리자 등록 섹션
        st.subheader("새 관리자 등록")
        
        with st.form("new_admin_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_admin_id = st.text_input("아이디")
                new_admin_name = st.text_input("이름")
                new_admin_position = st.selectbox("직급", options=["부장", "과장", "대리", "주임", "사원"])
            with col2:
                new_admin_pwd = st.text_input("비밀번호", type="password")
                new_admin_pwd_confirm = st.text_input("비밀번호 확인", type="password")
                new_admin_dept = st.selectbox("부서", options=["IT부", "생산부", "품질부", "관리부"])
            
            new_admin_level = st.radio("권한 레벨", options=["최고관리자", "부서관리자", "일반관리자"])
            
            submit_admin = st.form_submit_button("관리자 등록")
        
        if submit_admin:
            if not new_admin_id or not new_admin_name or not new_admin_pwd:
                st.error("필수 항목을 모두 입력하세요.")
            elif new_admin_pwd != new_admin_pwd_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif new_admin_id in admin_df["아이디"].values:
                st.error("이미 존재하는 아이디입니다.")
            else:
                st.success(f"관리자 '{new_admin_name}'이(가) 성공적으로 등록되었습니다.")
                st.info("실제 데이터베이스 연동 시 관리자 정보가 저장됩니다.")

elif st.session_state.page == "user_auth":
    # 사용자 등록 및 관리 페이지
    st.markdown("<div class='title-area'><h1>🔑 사용자 등록 및 관리</h1></div>", unsafe_allow_html=True)
    
    # 관리자 권한 확인
    if st.session_state.user_role != "관리자":
        st.warning("이 페이지는 관리자만 접근할 수 있습니다.")
        st.stop()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["👥 사용자 목록", "➕ 사용자 등록", "📊 사용 통계"])
    
    with tab1:
        # 사용자 목록 섹션
        st.subheader("등록된 사용자 목록")
        
        # 샘플 사용자 데이터
        user_data = {
            "아이디": ["user1", "user2", "user3", "user4", "user5", "user6"],
            "이름": ["홍길동", "김철수", "이영희", "박민수", "최지훈", "정수민"],
            "부서": ["생산부", "생산부", "품질부", "품질부", "기술부", "관리부"],
            "직급": ["사원", "대리", "사원", "주임", "과장", "사원"],
            "공정": ["선삭", "밀링", "검사", "검사", "설계", "관리"],
            "계정 생성일": [
                (datetime.now() - timedelta(days=120)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=45)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=15)).strftime("%Y-%m-%d"),
            ],
            "최근 접속일": [
                (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M"),
                (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d %H:%M"),
            ],
            "상태": ["활성", "활성", "활성", "활성", "비활성", "휴면"]
        }
        
        user_df = pd.DataFrame(user_data)
        
        # 필터링 옵션
        col1, col2, col3 = st.columns(3)
        with col1:
            dept_filter = st.selectbox("부서 필터", options=["전체", "생산부", "품질부", "기술부", "관리부"], key="user_dept_filter")
        with col2:
            process_filter = st.selectbox("공정 필터", options=["전체", "선삭", "밀링", "검사", "설계", "관리"], key="user_process_filter")
        with col3:
            status_filter = st.selectbox("상태 필터", options=["전체", "활성", "비활성", "휴면"], key="user_status_filter")
        
        # 필터 적용
        filtered_user_df = user_df.copy()
        if dept_filter != "전체":
            filtered_user_df = filtered_user_df[filtered_user_df["부서"] == dept_filter]
        if process_filter != "전체":
            filtered_user_df = filtered_user_df[filtered_user_df["공정"] == process_filter]
        if status_filter != "전체":
            filtered_user_df = filtered_user_df[filtered_user_df["상태"] == status_filter]
        
        # 필터링된 사용자 목록 표시
        st.dataframe(filtered_user_df, use_container_width=True, hide_index=True)
        
        # 사용자 검색
        search_query = st.text_input("사용자 검색 (이름 또는 아이디)", key="user_search")
        if search_query:
            search_results = user_df[
                user_df["이름"].str.contains(search_query) | 
                user_df["아이디"].str.contains(search_query)
            ]
            if not search_results.empty:
                st.subheader("검색 결과")
                st.dataframe(search_results, use_container_width=True, hide_index=True)
            else:
                st.info("검색 결과가 없습니다.")
        
        # 선택한 사용자 상세 정보 및 관리
        selected_user_id = st.selectbox(
            "상세 정보를 볼 사용자 선택",
            options=user_df["아이디"].tolist(),
            format_func=lambda x: f"{x} ({user_df[user_df['아이디'] == x]['이름'].values[0]})"
        )
        
        if selected_user_id:
            st.subheader(f"사용자 상세 정보: {selected_user_id}")
            
            # 선택된 사용자 정보
            user_info = user_df[user_df["아이디"] == selected_user_id].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("이름", user_info["이름"])
                st.metric("부서", user_info["부서"])
            with col2:
                st.metric("직급", user_info["직급"])
                st.metric("공정", user_info["공정"])
            with col3:
                st.metric("계정 생성일", user_info["계정 생성일"])
                st.metric("최근 접속일", user_info["최근 접속일"])
            
            # 계정 상태 관리
            st.subheader("계정 상태 관리")
            
            col1, col2 = st.columns(2)
            with col1:
                new_status = st.radio(
                    "계정 상태",
                    options=["활성", "비활성", "휴면"],
                    index=0 if user_info["상태"] == "활성" else 
                          1 if user_info["상태"] == "비활성" else 2,
                    key="user_status_change"
                )
            
            with col2:
                if st.button("비밀번호 초기화", key="user_reset_pwd"):
                    st.success(f"'{user_info['이름']}' 계정의 비밀번호가 초기화되었습니다.")
                    st.code("임시 비밀번호: User@1234")
                    st.info("실제 데이터베이스 연동 시 비밀번호가 변경됩니다.")
            
            if st.button("상태 변경 저장", key="save_user_status"):
                st.success(f"'{user_info['이름']}' 계정의 상태가 '{new_status}'로 변경되었습니다.")
                st.info("실제 데이터베이스 연동 시 상태가 변경됩니다.")

    with tab2:
        # 사용자 등록 섹션
        st.subheader("새 사용자 등록")
        
        with st.form("new_user_form_2"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("아이디", key="new_user_id_2")
                new_user_name = st.text_input("이름", key="new_user_name_2")
                new_user_dept = st.selectbox("부서", options=["생산부", "품질부", "기술부", "관리부"], key="new_user_dept_2")
            with col2:
                new_user_pwd = st.text_input("비밀번호", type="password", key="new_user_pwd_2")
                new_user_pwd_confirm = st.text_input("비밀번호 확인", type="password", key="new_user_pwd_confirm_2")
                new_user_position = st.selectbox("직급", options=["사원", "주임", "대리", "과장", "부장"], key="new_user_position_2")
            
            new_user_process = st.selectbox("담당 공정", options=["선삭", "밀링", "검사", "설계", "관리"], key="new_user_process_2")
            new_user_memo = st.text_area("메모 (선택사항)", max_chars=200, key="new_user_memo_2")
            
            submit_user = st.form_submit_button("사용자 등록")
        
        if submit_user:
            if not new_user_id or not new_user_name or not new_user_pwd:
                st.error("필수 항목을 모두 입력하세요.")
            elif new_user_pwd != new_user_pwd_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif new_user_id in user_df["아이디"].values:
                st.error("이미 존재하는 아이디입니다.")
            else:
                st.success(f"사용자 '{new_user_name}'이(가) 성공적으로 등록되었습니다.")
                st.info("실제 데이터베이스 연동 시 사용자 정보가 저장됩니다.")
    
    with tab3:
        # 사용 통계 섹션
        st.subheader("사용자 통계")
        
        # 부서별 사용자 분포
        dept_counts = user_df["부서"].value_counts().reset_index()
        dept_counts.columns = ["부서", "사용자 수"]
        
        # 공정별 사용자 분포
        process_counts = user_df["공정"].value_counts().reset_index()
        process_counts.columns = ["공정", "사용자 수"]
        
        # 상태별 사용자 분포
        status_counts = user_df["상태"].value_counts().reset_index()
        status_counts.columns = ["상태", "사용자 수"]
        
        # 차트 표시
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='emoji-title'>👥 부서별 사용자 분포</div>", unsafe_allow_html=True)
            
            fig = px.bar(
                dept_counts, 
                x="부서", 
                y="사용자 수",
                color="부서",
                color_discrete_sequence=px.colors.qualitative.Bold
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=10, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='emoji-title'>⚙️ 공정별 사용자 분포</div>", unsafe_allow_html=True)
            
            fig = px.pie(
                process_counts, 
                names="공정", 
                values="사용자 수",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=10, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='emoji-title'>🔄 계정 상태 분포</div>", unsafe_allow_html=True)
            
            fig = px.pie(
                status_counts, 
                names="상태", 
                values="사용자 수",
                color="상태",
                color_discrete_map={
                    "활성": "#4cb782",
                    "비활성": "#fb8c00",
                    "휴면": "#7c3aed"
                }
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=20, r=20, t=10, b=20),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
            )
            
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
            # 접속 활동 요약
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("<div class='emoji-title'>📈 접속 활동 요약</div>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                active_users = len(user_df[user_df["상태"] == "활성"])
                st.metric("활성 사용자", f"{active_users}명")
                
                recent_users = len(user_df[pd.to_datetime(user_df["최근 접속일"]) > (datetime.now() - timedelta(days=7))])
                st.metric("최근 7일 접속자", f"{recent_users}명")
            
            with col2:
                inactive_users = len(user_df[user_df["상태"] != "활성"])
                st.metric("비활성/휴면 사용자", f"{inactive_users}명")
                
                no_login_users = len(user_df[pd.to_datetime(user_df["최근 접속일"]) < (datetime.now() - timedelta(days=30))])
                st.metric("30일 이상 미접속자", f"{no_login_users}명")
            
            st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "inspection_data":
    # 생산 실적 관리 페이지
    st.markdown("<div class='title-area'><h1>📊 검사실적 관리</h1></div>", unsafe_allow_html=True)
    
    # 관리자 권한 확인
    if st.session_state.user_role != "관리자":
        st.warning("이 페이지는 관리자만 접근할 수 있습니다.")
        st.stop()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📑 실적 데이터 조회", "📝 실적 데이터 입력", "🔍 데이터 검증"])
    
    with tab1:
        # 실적 데이터 조회 섹션
        st.subheader("검사 실적 데이터 조회")
        
        # 검색 및 필터 조건
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=30), key="prod_start_date")
        with col2:
            end_date = st.date_input("종료일", datetime.now(), key="prod_end_date")
        with col3:
            process_filter = st.selectbox("공정 필터", options=["전체", "선삭", "밀링", "연삭", "조립"], key="prod_process")
        
        # 샘플 생산 실적 데이터
        production_data = {
            "날짜": pd.date_range(start=datetime.now()-timedelta(days=30), periods=50, freq='B').strftime("%Y-%m-%d"),
            "작업지시번호": [f"WO-{i:05d}" for i in range(1001, 1051)],
            "품목코드": [f"ITEM-{i:04d}" for i in range(1, 51)],
            "품목명": [f"부품 {chr(65 + i % 26)}-{i % 10}" for i in range(50)],
            "공정": np.random.choice(["선삭", "밀링", "연삭", "조립"], 50),
            "작업자": np.random.choice(["홍길동", "김철수", "이영희", "박민수", "최지훈"], 50),
            "계획수량": np.random.randint(50, 200, 50),
            "생산수량": [np.random.randint(40, x+1) for x in np.random.randint(50, 200, 50)],
            "불량수량": np.random.randint(0, 10, 50)
        }
        
        production_data["작업시작시간"] = [(datetime.now() - timedelta(days=d, hours=np.random.randint(0, 5))).strftime("%H:%M") 
                       for d in range(30, 0, -1)] + [(datetime.now() - timedelta(hours=np.random.randint(0, 5))).strftime("%H:%M") 
                       for _ in range(20)]
        
        production_data["작업종료시간"] = [(datetime.now() - timedelta(days=d, hours=np.random.randint(0, 3))).strftime("%H:%M") 
                       for d in range(30, 0, -1)] + [(datetime.now() - timedelta(hours=np.random.randint(0, 3))).strftime("%H:%M") 
                       for _ in range(20)]
        
        production_data["상태"] = np.random.choice(["완료", "진행중", "대기"], 50, p=[0.7, 0.2, 0.1])
        
        prod_df = pd.DataFrame(production_data)
        
        # 데이터프레임에 불량률 계산 추가
        prod_df["불량률(%)"] = (prod_df["불량수량"] / prod_df["생산수량"] * 100).round(2)
        prod_df["달성률(%)"] = (prod_df["생산수량"] / prod_df["계획수량"] * 100).round(2)
        
        # 필터 적용
        filtered_prod_df = prod_df.copy()
        
        # 날짜 필터 적용
        filtered_prod_df = filtered_prod_df[
            (pd.to_datetime(filtered_prod_df["날짜"]) >= pd.Timestamp(start_date)) & 
            (pd.to_datetime(filtered_prod_df["날짜"]) <= pd.Timestamp(end_date))
        ]
        
        # 공정 필터 적용
        if process_filter != "전체":
            filtered_prod_df = filtered_prod_df[filtered_prod_df["공정"] == process_filter]
        
        # 검색 기능
        search_query = st.text_input("품목 또는 작업지시번호 검색", key="prod_search")
        if search_query:
            filtered_prod_df = filtered_prod_df[
                filtered_prod_df["품목명"].str.contains(search_query) | 
                filtered_prod_df["작업지시번호"].str.contains(search_query) |
                filtered_prod_df["품목코드"].str.contains(search_query)
            ]
        
        # 데이터 정렬 옵션
        sort_option = st.selectbox(
            "정렬 기준",
            options=["날짜(최신순)", "날짜(오래된순)", "달성률(높은순)", "달성률(낮은순)", "불량률(높은순)", "불량률(낮은순)"],
            index=0
        )
        
        # 정렬 적용
        if sort_option == "날짜(최신순)":
            filtered_prod_df = filtered_prod_df.sort_values(by="날짜", ascending=False)
        elif sort_option == "날짜(오래된순)":
            filtered_prod_df = filtered_prod_df.sort_values(by="날짜", ascending=True)
        elif sort_option == "달성률(높은순)":
            filtered_prod_df = filtered_prod_df.sort_values(by="달성률(%)", ascending=False)
        elif sort_option == "달성률(낮은순)":
            filtered_prod_df = filtered_prod_df.sort_values(by="달성률(%)", ascending=True)
        elif sort_option == "불량률(높은순)":
            filtered_prod_df = filtered_prod_df.sort_values(by="불량률(%)", ascending=False)
        elif sort_option == "불량률(낮은순)":
            filtered_prod_df = filtered_prod_df.sort_values(by="불량률(%)", ascending=True)
        
        # 필터링된 생산 실적 표시
        st.dataframe(
            filtered_prod_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "불량률(%)": st.column_config.ProgressColumn(
                    "불량률(%)",
                    help="생산된 제품 중 불량 비율",
                    format="%.2f%%",
                    min_value=0,
                    max_value=10,
                ),
                "달성률(%)": st.column_config.ProgressColumn(
                    "달성률(%)",
                    help="계획 대비 생산 달성률",
                    format="%.2f%%",
                    min_value=0,
                    max_value=120,
                    width="medium"
                ),
            }
        )
    
    # 나머지 탭은 구현이 복잡하므로 간단한 안내 메시지로 대체
    with tab2:
        st.info("실적 데이터 입력 기능은 데이터베이스 연동 후 구현됩니다.")
    
    with tab3:
        st.info("데이터 검증 기능은 데이터베이스 연동 후 구현됩니다.")

elif st.session_state.page == "quality_report":
    # 월간 품질 리포트 페이지
    st.markdown("<div class='title-area'><h1>⭐ 월간 품질 리포트</h1></div>", unsafe_allow_html=True)
    
    # 날짜 선택
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("연도 선택", options=list(range(datetime.now().year-2, datetime.now().year+1)), index=2)
    with col2:
        selected_month = st.selectbox("월 선택", options=list(range(1, 13)), index=datetime.now().month-1)
    
    # 선택된 월의 문자열 표현
    month_names = ["1월", "2월", "3월", "4월", "5월", "6월", "7월", "8월", "9월", "10월", "11월", "12월"]
    selected_month_name = month_names[selected_month-1]
    
    # 데이터 로딩 표시
    with st.spinner(f"{selected_year}년 {selected_month_name} 품질 데이터 분석 중..."):
        time.sleep(0.5)  # 데이터 로딩 시뮬레이션
    
    # 품질 요약 지표
    st.subheader(f"{selected_year}년 {selected_month_name} 품질 요약")
    
    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("월별 검사 건수", "487건", "+12%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("불량률", "0.62%", "-0.08%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("품질 목표 달성률", "97.5%", "+1.2%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("고객 반품률", "0.05%", "-0.02%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # 품질 트렌드 차트
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📈 6개월 품질 추이</div>", unsafe_allow_html=True)
    
    # 샘플 데이터 준비
    months = [(datetime.now() - timedelta(days=30*i)).strftime("%Y-%m") for i in range(5, -1, -1)]
    month_labels = [(datetime.now() - timedelta(days=30*i)).strftime("%Y년 %m월") for i in range(5, -1, -1)]
    
    # 불량률 데이터 (개선 추세)
    defect_rates = [0.82, 0.78, 0.74, 0.69, 0.65, 0.62]
    
    # 반품률 데이터 (더 낮은 값)
    return_rates = [0.12, 0.10, 0.09, 0.07, 0.06, 0.05]
    
    # 품질 목표 달성률 데이터 (상승 추세)
    quality_achievement = [92.5, 93.2, 94.1, 95.3, 96.2, 97.5]
    
    # 복합 그래프 생성
    fig = go.Figure()
    
    # 불량률 (선 그래프)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=defect_rates,
        name="불량률(%)",
        line=dict(color="#4361ee", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        yaxis="y1",
        hovertemplate='%{x}<br>불량률: %{y:.2f}%<extra></extra>'
    ))
    
    # 반품률 (선 그래프)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=return_rates,
        name="반품률(%)",
        line=dict(color="#fb8c00", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        yaxis="y1",
        hovertemplate='%{x}<br>반품률: %{y:.2f}%<extra></extra>'
    ))
    
    # 품질 목표 달성률 (선 그래프, 두 번째 y축)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=quality_achievement,
        name="품질 목표 달성률(%)",
        line=dict(color="#4cb782", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        yaxis="y2",
        hovertemplate='%{x}<br>품질 달성률: %{y:.1f}%<extra></extra>'
    ))
    
    # 불량률 목표선 (1%)
    fig.add_trace(go.Scatter(
        x=[month_labels[0], month_labels[-1]],
        y=[1.0, 1.0],
        name="불량률 목표(1%)",
        line=dict(color="red", width=2, dash="dash"),
        mode="lines",
        yaxis="y1",
        hoverinfo="skip"
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title=None,
        xaxis=dict(title=None),
        yaxis=dict(
            title="불량률/반품률 (%)",
            side="left",
            range=[0, 1.2],
            showgrid=False
        ),
        yaxis2=dict(
            title="목표 달성률 (%)",
            side="right",
            overlaying="y",
            range=[90, 100],
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 공정별 품질 분석
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>⚙️ 공정별 품질 분석</div>", unsafe_allow_html=True)
    
    # 공정 데이터
    processes = ["선삭", "밀링", "연삭", "드릴링", "조립", "검사"]
    process_defect_rates = [0.85, 0.65, 0.55, 0.70, 0.45, 0.20]
    process_inspection_counts = [1200, 980, 850, 780, 1500, 2000]
    
    # 공정별 데이터프레임
    process_df = pd.DataFrame({
        "공정": processes,
        "불량률(%)": process_defect_rates,
        "검사건수": process_inspection_counts
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 공정별 불량률 막대 그래프
        fig = px.bar(
            process_df,
            x="공정",
            y="불량률(%)",
            color="공정",
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"불량률(%)": "불량률 (%)"},
            text_auto='.2f'
        )
        
        # 평균 불량률 라인
        avg_defect = np.mean(process_defect_rates)
        fig.add_shape(
            type="line",
            x0=-0.5, y0=avg_defect,
            x1=len(processes)-0.5, y1=avg_defect,
            line=dict(color="#4361ee", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=1, y=avg_defect,
            text=f"평균: {avg_defect:.2f}%",
            showarrow=False,
            yshift=10,
            font=dict(color="#4361ee")
        )
        
        fig.update_layout(
            title=None,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # 공정별 불량률 및 검사건수 버블 차트
        fig = px.scatter(
            process_df,
            x="공정",
            y="불량률(%)",
            size="검사건수",
            color="불량률(%)",
            color_continuous_scale="Viridis",
            size_max=50,
            labels={"불량률(%)": "불량률 (%)"},
            hover_data={"검사건수": True}
        )
        
        fig.update_layout(
            title=None,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            coloraxis_colorbar=dict(title="불량률 (%)")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # 공정별 품질 지표 테이블
    process_df["개선필요"] = ["" if rate < 0.7 else "⚠️" for rate in process_df["불량률(%)"]]
    process_df["품질그룹"] = ["A" if rate < 0.5 else "B" if rate < 0.7 else "C" for rate in process_df["불량률(%)"]]
    
    st.dataframe(
        process_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "불량률(%)": st.column_config.ProgressColumn(
                "불량률(%)",
                help="공정별 불량률",
                format="%.2f%%",
                min_value=0,
                max_value=1,
            ),
            "검사건수": st.column_config.NumberColumn(
                "검사건수",
                help="공정별 검사 건수",
                format="%d건",
            ),
            "개선필요": st.column_config.TextColumn(
                "개선필요",
                help="불량률 0.7% 이상 공정은 개선 필요"
            ),
            "품질그룹": st.column_config.SelectboxColumn(
                "품질그룹",
                help="불량률에 따른 품질 그룹",
                options=["A", "B", "C"],
                required=True,
            ),
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 불량 유형 분석
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>🔍 불량 유형 분석</div>", unsafe_allow_html=True)
    
    defect_types = ["치수불량", "표면거칠기", "칩핑", "소재결함", "가공불량", "조립불량", "기타"]
    defect_counts = [42, 35, 28, 15, 22, 18, 10]
    
    defect_df = pd.DataFrame({
        "불량유형": defect_types,
        "발생건수": defect_counts,
        "비율(%)": [(count / sum(defect_counts) * 100).round(2) for count in defect_counts]
    })
    
    # 불량 유형별 파레토 차트
    fig = go.Figure()
    
    # 막대 그래프 (불량 건수)
    fig.add_trace(go.Bar(
        x=defect_df["불량유형"],
        y=defect_df["발생건수"],
        marker_color="#4361ee",
        name="발생건수",
        text=defect_df["발생건수"],
        textposition="auto"
    ))
    
    # 누적 비율 계산
    defect_df = defect_df.sort_values(by="발생건수", ascending=False)
    cum_percent = np.cumsum(defect_df["발생건수"]) / sum(defect_df["발생건수"]) * 100
    
    # 선 그래프 (누적 비율)
    fig.add_trace(go.Scatter(
        x=defect_df["불량유형"],
        y=cum_percent,
        mode="lines+markers",
        marker=dict(size=8),
        line=dict(color="#fb8c00", width=3),
        name="누적 비율(%)",
        yaxis="y2",
        hovertemplate='%{x}<br>누적 비율: %{y:.1f}%<extra></extra>'
    ))
    
    # 80% 기준선
    fig.add_trace(go.Scatter(
        x=[defect_df["불량유형"].iloc[0], defect_df["불량유형"].iloc[-1]],
        y=[80, 80],
        mode="lines",
        line=dict(color="red", width=2, dash="dash"),
        name="80% 기준",
        yaxis="y2",
        hoverinfo="skip"
    ))
    
    # 레이아웃 설정
    fig.update_layout(
        title=None,
        xaxis=dict(title="불량 유형"),
        yaxis=dict(
            title="발생 건수",
            side="left",
            showgrid=False
        ),
        yaxis2=dict(
            title="누적 비율 (%)",
            side="right",
            overlaying="y",
            range=[0, 105],
            showgrid=False
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        hovermode="x unified"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("핵심 개선 대상")
        st.markdown("**주요 불량 유형 (80% 비중)**")
        
        # 누적 80%까지의 불량 유형
        critical_defects = defect_df[cum_percent <= 80]
        
        for idx, row in critical_defects.iterrows():
            st.markdown(f"⚠️ **{row['불량유형']}**: {row['발생건수']}건 ({row['비율(%)']}%)")
        
        st.markdown("---")
        st.markdown("**신규 불량 탐지**")
        
        new_defects = ["표면거칠기", "조립불량"]
        for defect in new_defects:
            st.markdown(f"🆕 **{defect}**: 전월 대비 증가")
    
    # 불량 유형별 개선 권고 사항
    improvement_data = {
        "불량유형": ["치수불량", "표면거칠기", "칩핑"],
        "근본원인": ["공구 마모", "가공 조건 부적절", "소재 품질 불량"],
        "개선방안": ["공구 교체 주기 단축", "가공 속도 및 이송 조정", "소재 공급업체 품질 관리 강화"],
        "담당부서": ["생산부", "기술부", "품질부"],
        "우선순위": ["상", "상", "중"]
    }
    
    improvement_df = pd.DataFrame(improvement_data)
    
    st.subheader("주요 불량 개선 권고사항")
    st.dataframe(improvement_df, use_container_width=True, hide_index=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 월간 품질 요약 보고서
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>📋 월간 품질 요약 보고서</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    ### {selected_year}년 {selected_month_name} 품질 성과 요약
    
    - **전체 불량률**: 0.62% (전월 대비 0.08%p 감소)
    - **불량 유형 분석**: 치수불량과 표면거칠기가 전체 불량의 약 45%를 차지함
    - **공정별 분석**: 선삭 공정이 가장 높은 불량률(0.85%)을 보임
    - **품질 개선 활동**: 공구 교체 주기 단축, 가공 조건 최적화로 표면거칠기 불량 감소
    - **권고 사항**: 치수불량 개선을 위한 공정 모니터링 시스템 도입 검토
    
    ### 다음 달 품질 개선 계획
    
    1. 선삭 공정 가공 조건 최적화 연구
    2. 치수불량 개선을 위한 작업자 교육 프로그램 실시
    3. 새로운 측정 장비 도입으로 불량 탐지율 향상
    """)
    
    # 보고서 다운로드 버튼
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button(
            label="📄 PDF 보고서 다운로드",
            data=b"Sample PDF Report",
            file_name=f"품질보고서_{selected_year}_{selected_month}.pdf",
            mime="application/pdf"
        )
    
    with download_col2:
        st.download_button(
            label="📊 Excel 데이터 다운로드",
            data=b"Sample Excel Data",
            file_name=f"품질데이터_{selected_year}_{selected_month}.xlsx",
            mime="application/vnd.ms-excel"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)