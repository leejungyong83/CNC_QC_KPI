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
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import matplotlib.dates as mdates
import uuid
import re
import random
from PIL import Image

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
ADMIN_DATA_FILE = DATA_DIR / "admin_data.json"
USER_DATA_FILE = DATA_DIR / "user_data.json"

def load_admin_data():
    """관리자 데이터 파일에서 로드하는 함수"""
    try:
        with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # 파일이 없거나 내용이 없을 경우 기본 구조 반환
        return {
            "아이디": [],
            "이름": [],
            "권한": [],
            "부서": [],
            "최근접속일": [],
            "상태": []
        }

def save_admin_data(admin_data):
    """관리자 데이터를 파일에 저장하는 함수"""
    # 디렉토리가 없으면 생성
    os.makedirs(DATA_DIR, exist_ok=True)
    
    with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(admin_data, f, ensure_ascii=False, indent=2)

def load_user_data():
    """사용자 데이터 파일에서 로드하는 함수"""
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
            # 새로운 형식과 기존 형식 모두 처리
            if isinstance(raw_data, dict) and "users" in raw_data:
                # 기존 형식: {"users": [{"email": "...", "name": "...", ...}, ...]}
                users_list = raw_data["users"]
                data = {
                    "아이디": [],
                    "이름": [],
                    "부서": [],
                    "직급": [],
                    "공정": [],
                    "계정생성일": [],
                    "최근접속일": [],
                    "상태": []
                }
                
                for user in users_list:
                    data["아이디"].append(user.get("email", ""))
                    data["이름"].append(user.get("name", ""))
                    data["부서"].append("관리부")  # 기본값
                    data["직급"].append("사원")    # 기본값
                    data["공정"].append("관리")    # 기본값
                    data["계정생성일"].append(user.get("registered_date", ""))
                    data["최근접속일"].append(user.get("last_login", ""))
                    data["상태"].append("활성")    # 기본값
                
                return data
            elif isinstance(raw_data, dict):
                # 누락된 키가 있는지 확인하고 필요하면 초기화
                required_keys = ["아이디", "이름", "부서", "직급", "공정", "계정생성일", "최근접속일", "상태"]
                for key in required_keys:
                    if key not in raw_data:
                        raw_data[key] = []
                return raw_data
            else:
                return {
                    "아이디": [],
                    "이름": [],
                    "부서": [],
                    "직급": [],
                    "공정": [],
                    "계정생성일": [],
                    "최근접속일": [],
                    "상태": []
                }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "아이디": [],
            "이름": [],
            "부서": [],
            "직급": [],
            "공정": [],
            "계정생성일": [],
            "최근접속일": [],
            "상태": []
        }

def save_user_data(user_data):
    """사용자 데이터를 파일에 저장하는 함수"""
    # 디렉토리가 없으면 생성
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 올바른 키가 있는지 확인
    required_keys = ["아이디", "이름", "부서", "직급", "공정", "계정생성일", "최근접속일", "상태"]
    for key in required_keys:
        if key not in user_data:
            user_data[key] = []
    
    # 데이터 저장 - 이 형식은 load_user_data()와 일관되어야 함
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

def init_db():
    """JSON 파일 기반 데이터베이스 초기화"""
    try:
        # 디렉토리가 없으면 생성
        os.makedirs(DATA_DIR, exist_ok=True)
        
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
        
        # 생산모델 데이터 초기화 - 기존 데이터 보존
        if not (DATA_DIR / "product_models.json").exists():
            # 샘플 모델 데이터
            default_models = {
                "models": [
                    {"id": 1, "모델명": "PA1", "공정": "C1"},
                    {"id": 2, "모델명": "PA1", "공정": "C2"},
                    {"id": 3, "모델명": "PA2", "공정": "C1"},
                    {"id": 4, "모델명": "PA2", "공정": "C2"},
                    {"id": 5, "모델명": "PA3", "공정": "C1"},
                    {"id": 6, "모델명": "PA3", "공정": "C2"},
                    {"id": 7, "모델명": "PA3", "공정": "C2-1"},
                    {"id": 8, "모델명": "B6", "공정": "C1"},
                    {"id": 9, "모델명": "B6", "공정": "C2"},
                    {"id": 10, "모델명": "B6M", "공정": "C1"}
                ]
            }
            with open(DATA_DIR / "product_models.json", 'w', encoding='utf-8') as f:
                json.dump(default_models, f, ensure_ascii=False, indent=2)
        
        # 관리자 데이터 초기화 - 기존 데이터 보존
        if not ADMIN_DATA_FILE.exists():
            default_admin_data = {
                "아이디": ["admin"],
                "이름": ["관리자"],
                "권한": ["관리자"],
                "부서": ["관리부"],
                "최근접속일": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "상태": ["활성"]
            }
            with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_admin_data, f, ensure_ascii=False, indent=2)
        
        # 사용자 데이터 초기화 - 기존 데이터 보존
        if not USER_DATA_FILE.exists():
            default_user_data = {
                "아이디": [],
                "이름": [],
                "부서": [],
                "직급": [],
                "공정": [],
                "계정생성일": [],
                "최근접속일": [],
                "상태": []
            }
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_user_data, f, ensure_ascii=False, indent=2)
        
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
            "process_auth": "⚙️ 관리자 등록 및 관리",
            "user_auth": "🔑 검사자 등록 및 관리",
            "inspection_data": "📊 검사실적 관리",
            "product_model": "📦 생산모델 관리"
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
            "inspection_data": "📊 Quản lý dữ liệu kiểm tra",
            "product_model": "📦 Quản lý mô hình sản xuất"
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
            # 샘플 데이터 반환
            default_inspectors = [
                {"id": "INS001", "name": "홍길동", "department": "CNC_1", "process": "선삭", "years_of_service": 5.5},
                {"id": "INS002", "name": "김철수", "department": "CNC_2", "process": "밀링", "years_of_service": 3.2},
                {"id": "INS003", "name": "이영희", "department": "PQC_LINE", "process": "검사", "years_of_service": 7.1}
            ]
            return pd.DataFrame(default_inspectors)
    except Exception as e:
        # 오류 발생 시 기본 데이터 반환
        st.error(f"검사원 정보 로딩 중 오류: {str(e)}")
        default_inspectors = [...]
        return pd.DataFrame(default_inspectors)

# 검사 데이터 저장
def save_inspection_data(data):
    try:
        # 한글 필드명을 영문으로 변환
        field_mapping = {
            "검사원": "inspector_name",
            "공정": "process",
            "모델명": "model_name",
            "검사일자": "inspection_date",
            "검사시간": "inspection_time",
            "LOT번호": "lot_number",
            "작업시간(분)": "work_time_minutes",
            "계획수량": "planned_quantity",
            "검사수량": "total_inspected",
            "불량수량": "total_defects",
            "불량률(%)": "defect_rate",
            "달성률(%)": "achievement_rate",
            "비고": "remarks"
        }
        
        # 데이터 변환
        english_data = {}
        for k, v in data.items():
            if k in field_mapping:
                english_data[field_mapping[k]] = v
            else:
                english_data[k] = v
        
        # 불량 세부정보 처리
        if "불량세부" in data:
            defect_details = []
            for item in data["불량세부"]:
                defect_details.append({
                    "type": item["type"],
                    "quantity": item["quantity"]
                })
            english_data["defect_details"] = json.dumps(defect_details, ensure_ascii=False)
        
        # 영문 필드명으로 저장
        try:
            response = supabase.table('inspection_data').insert(english_data).execute()
            return response
        except Exception as db_error:
            # 데이터베이스 연결 실패 시 로컬에 저장
            if 'saved_inspections' not in st.session_state:
                st.session_state.saved_inspections = []
            st.session_state.saved_inspections.append(data)
            raise db_error
            
    except Exception as e:
        # 세션에 데이터 저장(백업)
        if 'saved_inspections' not in st.session_state:
            st.session_state.saved_inspections = []
        st.session_state.saved_inspections.append(data)
        raise e

# 불량 데이터 저장
def save_defect_data(data):
    try:
        # 한글 필드명을 영문으로 변환
        field_mapping = {
            "불량유형": "defect_type",
            "수량": "quantity",
            "검사ID": "inspection_id",
            "등록일자": "registration_date",
            "등록자": "registered_by",
            "비고": "remarks"
        }
        
        # 데이터 변환
        english_data = {}
        for k, v in data.items():
            if k in field_mapping:
                english_data[field_mapping[k]] = v
            else:
                english_data[k] = v
        
        # 영문 필드명으로 저장
        try:
            response = supabase.table('defect_data').insert(english_data).execute()
            return response
        except Exception as db_error:
            # 데이터베이스 연결 실패 시 로컬에 저장
            if 'saved_defects' not in st.session_state:
                st.session_state.saved_defects = []
            st.session_state.saved_defects.append(data)
            raise db_error
            
    except Exception as e:
        # 세션에 데이터 저장(백업)
        if 'saved_defects' not in st.session_state:
            st.session_state.saved_defects = []
        st.session_state.saved_defects.append(data)
        raise e

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
    df["📊 불량률(%)"] = (df["⚠️ 불량수량"] / df["📦 전체수량"] * 100).apply(lambda x: round(x, 2))
    
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
            defect_rate = round((total_defects / total_quantity * 100), 2) if total_quantity > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📊 총 불량 수량", f"{total_defects}개")
            with col2:
                st.metric("📈 불량률", f"{defect_rate}%")
                
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
        df["defect_rate"] = (df["defect_count"] / df["total_quantity"] * 100).apply(lambda x: round(x, 2))
        
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
        st.subheader("관리자 등록 현황")
        
        # 세션 상태에 관리자 목록 초기화 (처음 접속 시에만)
        if 'admin_users' not in st.session_state:
            # JSON 파일에서 관리자 데이터 로드
            st.session_state.admin_users = load_admin_data()
            
            # 데이터가 비어있는지 확인하고, 비어있으면 기본 관리자 데이터 추가
            if len(st.session_state.admin_users.get("아이디", [])) == 0:
                st.session_state.admin_users = {
                    "아이디": ["admin"],
                    "이름": ["관리자"],
                    "권한": ["관리자"],
                    "부서": ["관리부"],
                    "최근접속일": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "상태": ["활성"]
                }
                # 기본 관리자 데이터 저장
                save_admin_data(st.session_state.admin_users)
                st.info("기본 관리자 계정이 생성되었습니다.")
        
        # 데이터프레임 변환 시 에러 처리
        try:
            # 사용자 데이터프레임 생성 (manager_auth 페이지와 동일한 데이터 사용)
            admin_df = pd.DataFrame(st.session_state.admin_users)
        except Exception as e:
            st.error(f"관리자 데이터 로드 중 오류가 발생했습니다: {str(e)}")
            # 데이터 구조 오류 시 재설정
            st.session_state.admin_users = {
                "아이디": ["admin"],
                "이름": ["관리자"],
                "권한": ["관리자"],
                "부서": ["관리부"],
                "최근접속일": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "상태": ["활성"]
            }
            admin_df = pd.DataFrame(st.session_state.admin_users)
            save_admin_data(st.session_state.admin_users)
            st.warning("관리자 데이터가 재설정되었습니다.")
        
        # 관리자 목록 필터링
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("부서 필터", options=["전체", "관리부", "생산부", "품질부", "기술부"])
        with col2:
            status_filter = st.selectbox("상태 필터", options=["전체", "활성", "비활성"])
        
        # 필터 적용
        filtered_df = admin_df.copy()
        if dept_filter != "전체" and not filtered_df.empty and "부서" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["부서"] == dept_filter]
        if status_filter != "전체" and not filtered_df.empty and "상태" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["상태"] == status_filter]
        
        # 필터링된 관리자 목록 표시
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # 관리자 삭제 섹션 (관리자가 있을 경우에만 표시)
        if not filtered_df.empty:
            st.subheader("관리자 삭제")
            delete_cols = st.columns([3, 2])
            with delete_cols[0]:
                admin_to_delete = st.selectbox(
                    "삭제할 관리자 선택",
                    options=filtered_df["아이디"].tolist(),
                    format_func=lambda x: f"{x} ({filtered_df[filtered_df['아이디'] == x]['이름'].values[0]})"
                )
            with delete_cols[1]:
                delete_confirm = st.checkbox("삭제를 확인합니다")
                
            if st.button("관리자 삭제", type="primary", disabled=not delete_confirm):
                if delete_confirm:
                    # 세션 상태에서 관리자 삭제
                    idx = st.session_state.admin_users["아이디"].index(admin_to_delete)
                    deleted_name = st.session_state.admin_users["이름"][idx]
                    
                    # 관리자 삭제
                    for key in st.session_state.admin_users:
                        st.session_state.admin_users[key].pop(idx)
                    
                    # 파일에 저장
                    save_admin_data(st.session_state.admin_users)
                    
                    # 성공 메시지 및 시각적 효과 - 페이지 리로드 전에 표시
                    st.warning(f"관리자 '{admin_to_delete}'가 시스템에서 삭제되었습니다.")
                    time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                    st.toast(f"🗑️ {deleted_name} 관리자가 삭제되었습니다", icon="🔴")
                    
                    # 삭제 효과를 위한 플래그 설정
                    if 'deleted_admin' not in st.session_state:
                        st.session_state.deleted_admin = True
                    
                    # 페이지 리로드
                    st.experimental_rerun()
                else:
                    st.error("삭제를 확인해주세요.")
        
        # 삭제 효과 표시
        if 'deleted_admin' in st.session_state and st.session_state.deleted_admin:
            st.session_state.deleted_admin = False
            st.snow()  # 삭제 임팩트 효과
        
        # 구분선
        st.markdown("---")
        
        # 새 사용자 등록 폼
        st.subheader("신규 관리자 추가")
        
        # 폼 입력값 초기화를 위한 세션 상태 초기화
        if 'new_user_id' not in st.session_state:
            st.session_state.new_user_id = ""
        if 'new_user_name' not in st.session_state:
            st.session_state.new_user_name = ""
        if 'new_user_password' not in st.session_state:
            st.session_state.new_user_password = ""
        if 'new_user_password_confirm' not in st.session_state:
            st.session_state.new_user_password_confirm = ""
        if 'new_user_dept' not in st.session_state:
            st.session_state.new_user_dept = "관리부"
        if 'new_user_role' not in st.session_state:
            st.session_state.new_user_role = "일반"
            
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("아이디", value=st.session_state.new_user_id, key="input_user_id")
                new_user_name = st.text_input("이름", value=st.session_state.new_user_name, key="input_user_name")
                new_user_dept = st.selectbox("부서", options=["관리부", "생산부", "품질부", "기술부"], index=["관리부", "생산부", "품질부", "기술부"].index(st.session_state.new_user_dept) if st.session_state.new_user_dept in ["관리부", "생산부", "품질부", "기술부"] else 0, key="input_user_dept")
            with col2:
                new_user_password = st.text_input("비밀번호", type="password", value=st.session_state.new_user_password, key="input_user_pwd")
                new_user_password_confirm = st.text_input("비밀번호 확인", type="password", value=st.session_state.new_user_password_confirm, key="input_user_pwd_confirm")
                new_user_role = st.selectbox("권한", options=["일반", "관리자"], index=["일반", "관리자"].index(st.session_state.new_user_role) if st.session_state.new_user_role in ["일반", "관리자"] else 0, key="input_user_role")
            
            submit_user = st.form_submit_button("관리자 추가")
        
        if submit_user:
            if not new_user_id or not new_user_name or not new_user_password:
                st.error("필수 항목을 모두 입력하세요.")
            elif new_user_password != new_user_password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif new_user_id in st.session_state.admin_users["아이디"]:
                st.error("이미 존재하는 아이디입니다.")
            else:
                # 세션 상태에 새 관리자 추가
                st.session_state.admin_users["아이디"].append(new_user_id)
                st.session_state.admin_users["이름"].append(new_user_name)
                st.session_state.admin_users["권한"].append(new_user_role)
                st.session_state.admin_users["부서"].append(new_user_dept)
                st.session_state.admin_users["최근접속일"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.admin_users["상태"].append("활성")
                
                # 파일에 저장
                save_admin_data(st.session_state.admin_users)
                
                # 성공 메시지 및 시각적 효과
                st.success(f"관리자 '{new_user_name}'이(가) 성공적으로 등록되었습니다.")
                time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                
                # 추가 효과를 위한 플래그 설정
                if 'added_admin' not in st.session_state:
                    st.session_state.added_admin = True
                
                # 폼 입력값 리셋을 위한 세션 상태 설정
                st.session_state.new_user_id = ""
                st.session_state.new_user_name = ""
                st.session_state.new_user_password = ""
                st.session_state.new_user_password_confirm = ""
                
                # 페이지 리로드
                st.experimental_rerun()
        
        # 추가 효과 표시
        if 'added_admin' in st.session_state and st.session_state.added_admin:
            st.session_state.added_admin = False
            st.balloons()  # 풍선 효과 추가

    with tab2:
        # 권한 설정 섹션
        st.subheader("사용자 권한 설정")
        
        if users_df.empty:
            st.info("등록된 관리자가 없습니다. 먼저 관리자를 등록해주세요.")
        else:
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
                st.metric("현재 권한", user_info["권한"])
            with col2:
                st.metric("소속 부서", user_info["부서"])
            with col3:
                st.metric("계정 상태", user_info["상태"])
            
            # 권한 설정 옵션
            st.subheader("권한 설정")
            
            col1, col2 = st.columns(2)
            with col1:
                new_role = st.radio("권한", options=["일반", "관리자"], index=0 if user_info["권한"] == "일반" else 1)
            with col2:
                new_status = st.radio("상태", options=["활성", "비활성"], index=0 if user_info["상태"] == "활성" else 1)
            
            # 메뉴별 접근 권한
            st.subheader("메뉴별 접근 권한")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**관리자 메뉴**")
                admin_auth = {
                    "사용자 관리": st.checkbox("사용자 관리", value=user_info["권한"] == "관리자"),
                    "공정 관리": st.checkbox("공정 관리", value=user_info["권한"] == "관리자"),
                    "검사 관리": st.checkbox("검사 관리", value=True),
                    "시스템 설정": st.checkbox("시스템 설정", value=user_info["권한"] == "관리자")
                }
            
            with col2:
                st.markdown("**리포트 메뉴**")
                report_auth = {
                    "종합 대시보드": st.checkbox("종합 대시보드", value=True),
                    "일간 리포트": st.checkbox("일간 리포트", value=True),
                    "주간 리포트": st.checkbox("주간 리포트", value=True),
                    "월간 리포트": st.checkbox("월간 리포트", value=user_info["권한"] == "관리자")
                }
            
            # 권한 저장 버튼
            if st.button("권한 설정 저장"):
                # 세션 상태에서 해당 사용자의 권한과 상태 업데이트
                idx = st.session_state.admin_users["아이디"].index(selected_user)
                user_name = st.session_state.admin_users["이름"][idx]
                old_role = st.session_state.admin_users["권한"][idx]  # 이전 권한 저장
                
                # 권한과 상태 업데이트
                st.session_state.admin_users["권한"][idx] = new_role
                st.session_state.admin_users["상태"][idx] = new_status
                
                # 파일에 저장
                save_admin_data(st.session_state.admin_users)
                
                # 성공 메시지 및 시각적 효과
                st.success(f"사용자 '{selected_user}'의 권한이 성공적으로 업데이트되었습니다.")
                time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                
                # 업데이트에 따른 메시지 커스터마이징
                message = f"✅ {user_name}님의 "
                if old_role != new_role:
                    message += f"권한이 {old_role}에서 {new_role}로 변경되었습니다"
                else:
                    message += f"상태가 업데이트되었습니다"
                
                st.toast(message, icon="🔵")
                
                # 권한 설정 효과를 위한 플래그 설정
                if 'updated_admin' not in st.session_state:
                    st.session_state.updated_admin = True
                
                # 페이지 리로드
                st.experimental_rerun()
                
        # 권한 설정 효과 표시
        if 'updated_admin' in st.session_state and st.session_state.updated_admin:
            st.session_state.updated_admin = False
            st.success("✨ 권한 설정이 성공적으로 적용되었습니다!")

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
        
        # 세션 상태에 관리자 목록 초기화 (처음 접속 시에만)
        if 'admin_users' not in st.session_state:
            # JSON 파일에서 관리자 데이터 로드
            st.session_state.admin_users = load_admin_data()
        
        # 사용자 데이터프레임 생성 (manager_auth 페이지와 동일한 데이터 사용)
        admin_df = pd.DataFrame(st.session_state.admin_users)
        
        # 관리자 목록 필터링
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("부서 필터", options=["전체", "관리부", "생산부", "품질부", "기술부"])
        with col2:
            status_filter = st.selectbox("상태 필터", options=["전체", "활성", "비활성"])
        
        # 필터 적용
        filtered_df = admin_df.copy()
        if dept_filter != "전체" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["부서"] == dept_filter]
        if status_filter != "전체" and not filtered_df.empty:
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
                st.metric("권한", admin_info["권한"])
            with col2:
                st.metric("부서", admin_info["부서"])
                st.metric("상태", admin_info["상태"])
            with col3:
                st.metric("최근접속일", admin_info["최근접속일"])
            
            # 계정 활성화/비활성화 버튼
            col1, col2 = st.columns(2)
            with col1:
                if admin_info["상태"] == "활성":
                    if st.button(f"'{admin_info['이름']}' 계정 비활성화", key="deactivate_admin"):
                        # 세션 상태에서 해당 관리자의 상태 업데이트
                        idx = st.session_state.admin_users["아이디"].index(selected_admin)
                        st.session_state.admin_users["상태"][idx] = "비활성"
                        
                        # 파일에 저장
                        save_admin_data(st.session_state.admin_users)
                        
                        st.warning(f"'{admin_info['이름']}' 계정이 비활성화되었습니다.")
                        time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                        st.experimental_rerun()
                else:
                    if st.button(f"'{admin_info['이름']}' 계정 활성화", key="activate_admin"):
                        # 세션 상태에서 해당 관리자의 상태 업데이트
                        idx = st.session_state.admin_users["아이디"].index(selected_admin)
                        st.session_state.admin_users["상태"][idx] = "활성"
                        
                        # 파일에 저장
                        save_admin_data(st.session_state.admin_users)
                        
                        st.success(f"'{admin_info['이름']}' 계정이 활성화되었습니다.")
                        time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                        st.experimental_rerun()
            
            with col2:
                if st.button(f"'{admin_info['이름']}' 비밀번호 초기화", key="reset_admin_pwd"):
                    st.success(f"'{admin_info['이름']}' 계정의 비밀번호가 초기화되었습니다.")
                    st.code("임시 비밀번호: Admin@1234")
            
            # 권한 변경
            st.subheader("권한 변경")
            new_role = st.radio(
                "권한 선택",
                options=["일반", "관리자"],
                index=0 if admin_info["권한"] == "일반" else 1
            )
            
            if st.button("권한 변경 저장"):
                # 세션 상태에서 해당 관리자의 권한 업데이트
                idx = st.session_state.admin_users["아이디"].index(selected_admin)
                user_name = st.session_state.admin_users["이름"][idx]
                old_role = st.session_state.admin_users["권한"][idx]  # 이전 권한 저장
                
                # 권한 업데이트
                st.session_state.admin_users["권한"][idx] = new_role
                
                # 파일에 저장
                save_admin_data(st.session_state.admin_users)
                
                # 성공 메시지 및 시각적 효과
                st.success(f"관리자 '{selected_admin}'의 권한이 성공적으로 변경되었습니다.")
                time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                
                # 업데이트에 따른 메시지 커스터마이징
                if old_role != new_role:
                    message = f"✅ {user_name}님의 권한이 {old_role}에서 {new_role}로 변경되었습니다"
                    st.toast(message, icon="🔵")
                
                # 페이지 리로드
                st.experimental_rerun()
    
    with tab2:
        # 관리자 등록 섹션
        st.subheader("새 관리자 등록")
        
        # 폼 입력값 초기화를 위한 세션 상태 초기화
        if 'new_admin_id' not in st.session_state:
            st.session_state.new_admin_id = ""
        if 'new_admin_name' not in st.session_state:
            st.session_state.new_admin_name = ""
        if 'new_admin_password' not in st.session_state:
            st.session_state.new_admin_password = ""
        if 'new_admin_password_confirm' not in st.session_state:
            st.session_state.new_admin_password_confirm = ""
        if 'new_admin_dept' not in st.session_state:
            st.session_state.new_admin_dept = "관리부"
        
        with st.form("new_admin_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_admin_id = st.text_input("아이디", value=st.session_state.new_admin_id)
                new_admin_name = st.text_input("이름", value=st.session_state.new_admin_name)
                new_admin_dept = st.selectbox("부서", options=["관리부", "생산부", "품질부", "기술부"], index=["관리부", "생산부", "품질부", "기술부"].index(st.session_state.new_admin_dept) if st.session_state.new_admin_dept in ["관리부", "생산부", "품질부", "기술부"] else 0)
            with col2:
                new_admin_pwd = st.text_input("비밀번호", type="password", value=st.session_state.new_admin_password)
                new_admin_pwd_confirm = st.text_input("비밀번호 확인", type="password", value=st.session_state.new_admin_password_confirm)
                new_admin_role = st.selectbox("권한", options=["일반", "관리자"], index=0)
            
            submit_admin = st.form_submit_button("관리자 등록")
        
        if submit_admin:
            if not new_admin_id or not new_admin_name or not new_admin_pwd:
                st.error("필수 항목을 모두 입력하세요.")
            elif new_admin_pwd != new_admin_pwd_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif new_admin_id in st.session_state.admin_users["아이디"]:
                st.error("이미 존재하는 아이디입니다.")
            else:
                # 세션 상태에 새 관리자 추가
                st.session_state.admin_users["아이디"].append(new_admin_id)
                st.session_state.admin_users["이름"].append(new_admin_name)
                st.session_state.admin_users["권한"].append(new_admin_role)
                st.session_state.admin_users["부서"].append(new_admin_dept)
                st.session_state.admin_users["최근접속일"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.admin_users["상태"].append("활성")
                
                # 파일에 저장
                save_admin_data(st.session_state.admin_users)
                
                # 성공 메시지 및 시각적 효과
                st.success(f"관리자 '{new_admin_name}'이(가) 성공적으로 등록되었습니다.")
                time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                
                # 추가 효과를 위한 플래그 설정
                if 'added_admin' not in st.session_state:
                    st.session_state.added_admin = True
                
                # 폼 입력값 리셋을 위한 세션 상태 설정
                st.session_state.new_admin_id = ""
                st.session_state.new_admin_name = ""
                st.session_state.new_admin_password = ""
                st.session_state.new_admin_password_confirm = ""
                
                # 페이지 리로드
                st.experimental_rerun()
        
        # 추가 효과 표시
        if 'added_admin' in st.session_state and st.session_state.added_admin:
            st.session_state.added_admin = False
            st.balloons()  # 풍선 효과 추가

elif st.session_state.page == "user_auth":
    # 검사자 등록 및 관리 페이지
    st.markdown("<div class='title-area'><h1>🔑 검사자 등록 및 관리</h1></div>", unsafe_allow_html=True)
    
    # 관리자 권한 확인
    if st.session_state.user_role != "관리자":
        st.warning("이 페이지는 관리자만 접근할 수 있습니다.")
        st.stop()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["👥 검사자 목록", "➕ 신규 검사자 등록", "📊 검사자 통계"])
    
    with tab1:
        # 사용자 목록 섹션
        st.subheader("등록된 검사자 목록")
        
        try:
            # 세션 상태에 사용자 목록 초기화 (처음 접속 시에만)
            if 'user_data' not in st.session_state:
                # JSON 파일에서 사용자 데이터 로드
                st.session_state.user_data = load_user_data()
            
            # 사용자 데이터가 올바른 형식인지 확인
            if not isinstance(st.session_state.user_data, dict) or "아이디" not in st.session_state.user_data:
                # 잘못된 형식의 데이터인 경우 초기화
                st.session_state.user_data = load_user_data()
                st.warning("사용자 데이터가 올바른 형식이 아닙니다. 데이터를 재설정했습니다.")
            
            # 사용자 데이터프레임 생성
            user_df = pd.DataFrame(st.session_state.user_data)
            
            # DataFrame이 비어있는 경우 빈 DataFrame을 만들어주기
            if user_df.empty:
                user_df = pd.DataFrame({
                    "아이디": [],
                    "이름": [],
                    "부서": [],
                    "직급": [],
                    "공정": [],
                    "계정생성일": [],
                    "최근접속일": [],
                    "상태": []
                })
        
        except Exception as e:
            st.error(f"사용자 데이터를 불러오는데 실패했습니다: {str(e)}")
        
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
        if dept_filter != "전체" and not filtered_user_df.empty and "부서" in filtered_user_df.columns:
            filtered_user_df = filtered_user_df[filtered_user_df["부서"] == dept_filter]
        if process_filter != "전체" and not filtered_user_df.empty and "공정" in filtered_user_df.columns:
            filtered_user_df = filtered_user_df[filtered_user_df["공정"] == process_filter]
        if status_filter != "전체" and not filtered_user_df.empty and "상태" in filtered_user_df.columns:
            filtered_user_df = filtered_user_df[filtered_user_df["상태"] == status_filter]
        
        # 필터링된 사용자 목록 표시
        if filtered_user_df.empty:
            st.info("등록된 검사자가 없습니다. 먼저 검사자를 등록해주세요.")
        else:
            st.dataframe(filtered_user_df, use_container_width=True, hide_index=True)
        
        # 사용자 검색
        search_query = st.text_input("검사자 검색 (이름 또는 아이디)", key="user_search")
        if search_query and not user_df.empty:
            try:
                if "이름" in user_df.columns and "아이디" in user_df.columns:
                    search_results = user_df[
                        user_df["이름"].str.contains(search_query) | 
                        user_df["아이디"].str.contains(search_query)
                    ]
                    if not search_results.empty:
                        st.subheader("검색 결과")
                        st.dataframe(search_results, use_container_width=True, hide_index=True)
                    else:
                        st.info("검색 결과가 없습니다.")
                else:
                    st.warning("사용자 데이터에 필요한 열이 없습니다.")
            except Exception as e:
                st.error(f"검색 중 오류가 발생했습니다: {str(e)}")
        
        # 선택한 사용자 상세 정보 및 관리
        if not user_df.empty:
            try:
                if "아이디" in user_df.columns:
                    selected_user_id = st.selectbox(
                        "상세 정보를 볼 검사자 선택",
                        options=user_df["아이디"].tolist(),
                        format_func=lambda x: f"{x} ({user_df[user_df['아이디'] == x]['이름'].values[0] if not user_df[user_df['아이디'] == x].empty and '이름' in user_df.columns else '알 수 없음'})"
                    )
                    
                    if selected_user_id:
                        st.subheader(f"검사자 상세 정보: {selected_user_id}")
                        
                        # 선택된 사용자 정보
                        user_info_df = user_df[user_df["아이디"] == selected_user_id]
                        if not user_info_df.empty:
                            user_info = user_info_df.iloc[0]
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("이름", user_info["이름"] if "이름" in user_info and pd.notna(user_info["이름"]) else "정보 없음")
                                st.metric("부서", user_info["부서"] if "부서" in user_info and pd.notna(user_info["부서"]) else "정보 없음")
                            with col2:
                                st.metric("직급", user_info["직급"] if "직급" in user_info and pd.notna(user_info["직급"]) else "정보 없음")
                                st.metric("공정", user_info["공정"] if "공정" in user_info and pd.notna(user_info["공정"]) else "정보 없음")
                            with col3:
                                st.metric("계정생성일", user_info["계정생성일"] if "계정생성일" in user_info and pd.notna(user_info["계정생성일"]) else "정보 없음")
                                st.metric("최근접속일", user_info["최근접속일"] if "최근접속일" in user_info and pd.notna(user_info["최근접속일"]) else "정보 없음")
                            
                            # 계정 상태 관리
                            st.subheader("계정 상태 관리")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                current_status = user_info["상태"] if "상태" in user_info and pd.notna(user_info["상태"]) else "활성"
                                new_status = st.radio(
                                    "계정 상태",
                                    options=["활성", "비활성", "휴면"],
                                    index=0 if current_status == "활성" else 
                                        1 if current_status == "비활성" else 2,
                                    key="user_status_change"
                                )
                            
                            with col2:
                                if st.button("비밀번호 초기화", key="user_reset_pwd"):
                                    user_name = user_info["이름"] if "이름" in user_info and pd.notna(user_info["이름"]) else selected_user_id
                                    st.success(f"'{user_name}' 계정의 비밀번호가 초기화되었습니다.")
                                    st.code("임시 비밀번호: User@1234")
                                
                                if st.button("상태 변경 저장", key="save_user_status"):
                                    try:
                                        # 세션 상태에서 해당 사용자의 상태 업데이트
                                        if "아이디" in st.session_state.user_data and selected_user_id in st.session_state.user_data["아이디"]:
                                            idx = st.session_state.user_data["아이디"].index(selected_user_id)
                                            user_name = st.session_state.user_data["이름"][idx] if "이름" in st.session_state.user_data and idx < len(st.session_state.user_data["이름"]) else selected_user_id
                                            old_status = st.session_state.user_data["상태"][idx] if "상태" in st.session_state.user_data and idx < len(st.session_state.user_data["상태"]) else "알 수 없음"
                                            
                                            # 상태 업데이트
                                            if "상태" in st.session_state.user_data:
                                                if idx < len(st.session_state.user_data["상태"]):
                                                    st.session_state.user_data["상태"][idx] = new_status
                                                else:
                                                    # 인덱스가 범위를 벗어나면 필요한 만큼 확장
                                                    st.session_state.user_data["상태"].extend([None] * (idx - len(st.session_state.user_data["상태"]) + 1))
                                                    st.session_state.user_data["상태"][idx] = new_status
                                            else:
                                                # "상태" 키가 없으면 생성
                                                st.session_state.user_data["상태"] = ["활성"] * len(st.session_state.user_data["아이디"])
                                                st.session_state.user_data["상태"][idx] = new_status
                                            
                                            # 파일에 저장
                                            save_user_data(st.session_state.user_data)
                                            
                                            # 성공 메시지 및 시각적 효과
                                            st.success(f"사용자 '{user_name}'의 상태가 '{new_status}'로 성공적으로 변경되었습니다.")
                                            time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                                            
                                            # 업데이트에 따른 메시지 커스터마이징
                                            if old_status != new_status:
                                                message = f"✅ {user_name}님의 상태가 {old_status}에서 {new_status}로 변경되었습니다"
                                                st.toast(message, icon="🔵")
                                            
                                            # 페이지 리로드
                                            st.experimental_rerun()
                                        else:
                                            st.error("사용자 데이터에서 선택한 사용자를 찾을 수 없습니다.")
                                    except Exception as e:
                                        st.error(f"상태 변경 중 오류가 발생했습니다: {str(e)}")
                        
                        # 사용자 삭제 섹션
                        st.subheader("검사자 삭제")
                        delete_confirm = st.checkbox("삭제를 확인합니다", key="delete_user_confirm")
                        
                        if st.button("검사자 삭제", type="primary", disabled=not delete_confirm):
                            if delete_confirm:
                                try:
                                    # 세션 상태에서 사용자 삭제
                                    idx = st.session_state.user_data["아이디"].index(selected_user_id)
                                    deleted_name = st.session_state.user_data["이름"][idx] if "이름" in st.session_state.user_data and idx < len(st.session_state.user_data["이름"]) else selected_user_id
                                    
                                    # 사용자 삭제
                                    for key in st.session_state.user_data:
                                        if idx < len(st.session_state.user_data[key]):
                                            st.session_state.user_data[key].pop(idx)
                                    
                                    # 파일에 저장
                                    save_user_data(st.session_state.user_data)
                                    
                                    # 성공 메시지 및 시각적 효과 - 페이지 리로드 전에 표시
                                    st.warning(f"검사자 '{selected_user_id}'가 시스템에서 삭제되었습니다.")
                                    time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                                    st.toast(f"🗑️ {deleted_name} 검사자가 삭제되었습니다", icon="🔴")
                                    
                                    # 삭제 효과를 위한 플래그 설정
                                    if 'deleted_user' not in st.session_state:
                                        st.session_state.deleted_user = True
                                    
                                    # 페이지 리로드
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"검사자 삭제 중 오류가 발생했습니다: {str(e)}")
                            else:
                                st.error("삭제를 확인해주세요.")
                else:
                    st.warning("선택한 검사자의 정보를 찾을 수 없습니다.")
            except Exception as e:
                st.error(f"검사자 정보 표시 중 오류가 발생했습니다: {str(e)}")
                st.info("검사자 데이터에 문제가 있을 수 있습니다. 데이터를 확인해주세요.")
            
            # 삭제 효과 표시
            if 'deleted_user' in st.session_state and st.session_state.deleted_user:
                st.session_state.deleted_user = False
                st.snow()  # 삭제 임팩트 효과

    with tab2:
        # 사용자 등록 섹션
        st.subheader("신규 검사자 등록")
        
        # 폼 입력값 초기화를 위한 세션 상태 초기화
        if 'new_user_id' not in st.session_state:
            st.session_state.new_user_id = ""
        if 'new_user_name' not in st.session_state:
            st.session_state.new_user_name = ""
        if 'new_user_pwd' not in st.session_state:
            st.session_state.new_user_pwd = ""
        if 'new_user_pwd_confirm' not in st.session_state:
            st.session_state.new_user_pwd_confirm = ""
        if 'new_user_dept' not in st.session_state:
            st.session_state.new_user_dept = "생산부"
        if 'new_user_position' not in st.session_state:
            st.session_state.new_user_position = "사원"
        if 'new_user_process' not in st.session_state:
            st.session_state.new_user_process = "선삭"
        
        with st.form("new_user_form_2"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("아이디", value=st.session_state.new_user_id, key="new_user_id_2")
                new_user_name = st.text_input("이름", value=st.session_state.new_user_name, key="new_user_name_2")
                new_user_dept = st.selectbox("부서", options=["생산부", "품질부", "기술부", "관리부"], index=["생산부", "품질부", "기술부", "관리부"].index(st.session_state.new_user_dept) if st.session_state.new_user_dept in ["생산부", "품질부", "기술부", "관리부"] else 0, key="new_user_dept_2")
            with col2:
                new_user_pwd = st.text_input("비밀번호", type="password", value=st.session_state.new_user_pwd, key="new_user_pwd_2")
                new_user_pwd_confirm = st.text_input("비밀번호 확인", type="password", value=st.session_state.new_user_pwd_confirm, key="new_user_pwd_confirm_2")
                new_user_position = st.selectbox("직급", options=["사원", "주임", "대리", "과장", "부장"], index=["사원", "주임", "대리", "과장", "부장"].index(st.session_state.new_user_position) if st.session_state.new_user_position in ["사원", "주임", "대리", "과장", "부장"] else 0, key="new_user_position_2")
            
            new_user_process = st.selectbox("담당 공정", options=["선삭", "밀링", "검사", "설계", "관리"], index=["선삭", "밀링", "검사", "설계", "관리"].index(st.session_state.new_user_process) if st.session_state.new_user_process in ["선삭", "밀링", "검사", "설계", "관리"] else 0, key="new_user_process_2")
            new_user_memo = st.text_area("메모 (선택사항)", max_chars=200, key="new_user_memo_2")
            
            submit_user = st.form_submit_button("검사자 등록")
        
        if submit_user:
            if not new_user_id or not new_user_name or not new_user_pwd:
                st.error("필수 항목을 모두 입력하세요.")
            elif new_user_pwd != new_user_pwd_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
            elif 'user_data' in st.session_state and "아이디" in st.session_state.user_data and new_user_id in st.session_state.user_data["아이디"]:
                st.error("이미 존재하는 아이디입니다.")
            else:
                # 세션 상태에 새 사용자 추가
                if 'user_data' not in st.session_state:
                    st.session_state.user_data = load_user_data()
                
                # 필수 키 확인
                required_keys = ["아이디", "이름", "부서", "직급", "공정", "계정생성일", "최근접속일", "상태"]
                for key in required_keys:
                    if key not in st.session_state.user_data:
                        st.session_state.user_data[key] = []
                
                st.session_state.user_data["아이디"].append(new_user_id)
                st.session_state.user_data["이름"].append(new_user_name)
                st.session_state.user_data["부서"].append(new_user_dept)
                st.session_state.user_data["직급"].append(new_user_position)
                st.session_state.user_data["공정"].append(new_user_process)
                st.session_state.user_data["계정생성일"].append(datetime.now().strftime("%Y-%m-%d"))
                st.session_state.user_data["최근접속일"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.user_data["상태"].append("활성")
                
                # 파일에 저장
                save_user_data(st.session_state.user_data)
                
                # 성공 메시지 및 시각적 효과
                st.success(f"사용자 '{new_user_name}'이(가) 성공적으로 등록되었습니다.")
                time.sleep(0.5)  # 효과를 볼 수 있도록 짧은 대기시간 추가
                
                # 추가 효과를 위한 플래그 설정
                if 'added_user' not in st.session_state:
                    st.session_state.added_user = True
                
                # 폼 입력값 리셋을 위한 세션 상태 설정
                st.session_state.new_user_id = ""
                st.session_state.new_user_name = ""
                st.session_state.new_user_pwd = ""
                st.session_state.new_user_pwd_confirm = ""
                
                # 페이지 리로드
                st.experimental_rerun()
        
        # 추가 효과 표시
        if 'added_user' in st.session_state and st.session_state.added_user:
            st.session_state.added_user = False
            st.balloons()  # 풍선 효과 추가
    
    with tab3:
        # 사용 통계 섹션
        st.subheader("검사자 통계")
        
        if 'user_data' not in st.session_state or not isinstance(st.session_state.user_data, dict) or "아이디" not in st.session_state.user_data or len(st.session_state.user_data["아이디"]) == 0:
            st.info("등록된 사용자가 없습니다. 통계를 표시하려면 사용자를 등록해주세요.")
        else:
            user_df = pd.DataFrame(st.session_state.user_data)
            
            try:
                # 부서별 사용자 분포
                if "부서" in user_df.columns and not user_df["부서"].empty:
                    dept_counts = user_df["부서"].value_counts().reset_index()
                    dept_counts.columns = ["부서", "검사자 수"]
                    
                    # 공정별 사용자 분포
                    process_counts = None
                    if "공정" in user_df.columns and not user_df["공정"].empty:
                        process_counts = user_df["공정"].value_counts().reset_index()
                        process_counts.columns = ["공정", "검사자 수"]
                    
                    # 상태별 사용자 분포
                    status_counts = None
                    if "상태" in user_df.columns and not user_df["상태"].empty:
                        status_counts = user_df["상태"].value_counts().reset_index()
                        status_counts.columns = ["상태", "검사자 수"]
                    
                    # 차트 표시
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='emoji-title'>👥 부서별 검사자 분포</div>", unsafe_allow_html=True)
                        
                        fig = px.bar(
                            dept_counts, 
                            x="부서", 
                            y="검사자 수",
                            color="부서",
                            color_discrete_sequence=px.colors.qualitative.Bold
                        )
                        
                        fig.update_layout(
                            height=300,
                            margin=dict(l=20, r=20, t=10, b=20),
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        if process_counts is not None:
                            st.markdown("<div class='card'>", unsafe_allow_html=True)
                            st.markdown("<div class='emoji-title'>🔧 공정별 검사자 분포</div>", unsafe_allow_html=True)
                            
                            fig = px.bar(
                                process_counts, 
                                x="공정", 
                                y="검사자 수",
                                color="공정",
                                color_discrete_sequence=px.colors.qualitative.Pastel
                            )
                            
                            fig.update_layout(
                                height=300,
                                margin=dict(l=20, r=20, t=10, b=20),
                                plot_bgcolor="rgba(0,0,0,0)",
                                paper_bgcolor="rgba(0,0,0,0)",
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 상태별 사용자 분포 (파이 차트)
                    if status_counts is not None:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='emoji-title'>🔄 상태별 검사자 분포</div>", unsafe_allow_html=True)
                        
                        fig = px.pie(
                            status_counts, 
                            values="검사자 수", 
                            names="상태",
                            hole=0.4,
                            color="상태",
                            color_discrete_map={
                                "활성": "#4CAF50",
                                "비활성": "#F44336",
                                "휴면": "#FFC107"
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
                        
                        # 간단한 현황 요약
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='emoji-title'>📊 검사자 현황 요약</div>", unsafe_allow_html=True)
                        
                        active_users = len(user_df[user_df["상태"] == "활성"]) if "상태" in user_df.columns else 0
                        inactive_users = len(user_df[user_df["상태"] != "활성"]) if "상태" in user_df.columns else 0
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("활성 검사자", active_users)
                        with col2:
                            st.metric("비활성/휴면 검사자", inactive_users)
                        
                        # 최근 등록된 사용자
                        if "계정생성일" in user_df.columns and len(user_df) > 0:
                            try:
                                user_df["계정생성일"] = pd.to_datetime(user_df["계정생성일"], errors='coerce')
                                recent_users = user_df.sort_values("계정생성일", ascending=False).head(3)
                                
                                st.subheader("최근 등록된 검사자")
                                for _, user in recent_users.iterrows():
                                    user_name = user["이름"] if "이름" in user and pd.notna(user["이름"]) else "이름 없음"
                                    user_dept = user["부서"] if "부서" in user and pd.notna(user["부서"]) else "부서 없음"
                                    user_date = user["계정생성일"].strftime("%Y-%m-%d") if pd.notna(user["계정생성일"]) else "날짜 없음"
                                    
                                    st.markdown(f"**{user_name}** ({user_dept}) - {user_date}")
                            except Exception as e:
                                st.warning(f"최근 사용자 정보 표시 중 오류 발생: {str(e)}")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("사용자 데이터에 '부서' 필드가 없거나 비어있어 통계를 생성할 수 없습니다.")
            except Exception as e:
                st.error(f"통계 생성 중 오류가 발생했습니다: {str(e)}")
                st.info("사용자 데이터 구조를 확인해주세요.")

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
            # 실제 데이터에서 공정 목록 추출
            inspection_data = load_inspection_data()
            process_options = ["전체"]
            if not inspection_data.empty and "공정" in inspection_data.columns:
                process_options += sorted(inspection_data["공정"].unique().tolist())
            process_filter = st.selectbox("공정 필터", options=process_options, key="prod_process")
        
        # 데이터 로드 후 표시
        if inspection_data.empty:
            st.info("저장된 검사 실적 데이터가 없습니다. '실적 데이터 입력' 탭에서 데이터를 입력해주세요.")
        else:
            # 필요한 경우 날짜 열 변환
            if "검사일자" in inspection_data.columns and inspection_data["검사일자"].dtype == 'object':
                try:
                    inspection_data["검사일자"] = pd.to_datetime(inspection_data["검사일자"])
                except:
                    pass
            
            # 필터 적용
            filtered_df = inspection_data.copy()
            
            # 날짜 필터 적용
            if "검사일자" in filtered_df.columns:
                # 날짜 형식 확인
                if filtered_df["검사일자"].dtype == 'datetime64[ns]':
                    filtered_df = filtered_df[
                        (filtered_df["검사일자"].dt.date >= pd.Timestamp(start_date).date()) & 
                        (filtered_df["검사일자"].dt.date <= pd.Timestamp(end_date).date())
                    ]
                else:
                    # 문자열인 경우 처리
                    filtered_df = filtered_df[
                        (pd.to_datetime(filtered_df["검사일자"]).dt.date >= pd.Timestamp(start_date).date()) & 
                        (pd.to_datetime(filtered_df["검사일자"]).dt.date <= pd.Timestamp(end_date).date())
                    ]
            
            # 공정 필터 적용
            if process_filter != "전체" and "공정" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["공정"] == process_filter]
            
            # 검색 기능
            search_query = st.text_input("모델명 또는 LOT번호 검색", key="prod_search")
            if search_query:
                search_condition = False
                if "모델명" in filtered_df.columns:
                    search_condition |= filtered_df["모델명"].astype(str).str.contains(search_query, case=False, na=False)
                if "LOT번호" in filtered_df.columns:
                    search_condition |= filtered_df["LOT번호"].astype(str).str.contains(search_query, case=False, na=False)
                
                filtered_df = filtered_df[search_condition]
            
            # 데이터 정렬 옵션
            sort_columns = ["검사일자"]
            if "불량률(%)" in filtered_df.columns:
                sort_columns.append("불량률(%)")
            
            sort_options = []
            if "검사일자" in filtered_df.columns:
                sort_options += ["날짜(최신순)", "날짜(오래된순)"]
            if "불량률(%)" in filtered_df.columns:
                sort_options += ["불량률(높은순)", "불량률(낮은순)"]
            
            sort_option = st.selectbox(
                "정렬 기준",
                options=sort_options,
                index=0 if sort_options else 0
            )
            
            # 정렬 적용
            if sort_option == "날짜(최신순)" and "검사일자" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="검사일자", ascending=False)
            elif sort_option == "날짜(오래된순)" and "검사일자" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="검사일자", ascending=True)
            elif sort_option == "불량률(높은순)" and "불량률(%)" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="불량률(%)", ascending=False)
            elif sort_option == "불량률(낮은순)" and "불량률(%)" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="불량률(%)", ascending=True)
            
            # 필터링된 생산 실적 표시
            if filtered_df.empty:
                st.warning("검색 조건에 맞는 데이터가 없습니다.")
            else:
                # 날짜 형식 변환 (표시용)
                if "검사일자" in filtered_df.columns and filtered_df["검사일자"].dtype == 'datetime64[ns]':
                    filtered_df["검사일자"] = filtered_df["검사일자"].dt.strftime("%Y-%m-%d")
                
                # 컬럼 구성 설정
                column_config = {}
                
                # 불량률 프로그레스 바 설정
                if "불량률(%)" in filtered_df.columns:
                    column_config["불량률(%)"] = st.column_config.ProgressColumn(
                        "불량률(%)",
                        help="검사 수량 중 불량 비율",
                        format="%.2f%%",
                        min_value=0,
                        max_value=10,
                    )
                
                # 달성률 프로그레스 바 설정 (계획수량 대비 검사수량)
                if "계획수량" in filtered_df.columns and "검사수량" in filtered_df.columns:
                    # 달성률 계산이 안 되어있으면 계산
                    if "달성률(%)" not in filtered_df.columns:
                        filtered_df["달성률(%)"] = (filtered_df["검사수량"] / filtered_df["계획수량"] * 100).round(2)
                    
                    column_config["달성률(%)"] = st.column_config.ProgressColumn(
                        "달성률(%)",
                        help="계획 대비 검사 달성률",
                        format="%.2f%%",
                        min_value=0,
                        max_value=120,
                        width="medium"
                    )
                
                # 데이터 표시
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )
    
    # 나머지 탭은 구현이 복잡하므로 간단한 안내 메시지로 대체
    with tab2:
        # 실적 데이터 입력 폼 구현
        st.subheader("검사실적 데이터 입력")
        
        # 기본 정보 입력 폼
        col1, col2 = st.columns(2)
        with col1:
            # 세션에 저장된 검사원 목록 사용 또는 가져오기
            if 'inspectors' not in st.session_state or len(st.session_state.inspectors) == 0:
                try:
                    st.session_state.inspectors = load_inspectors()
                except Exception as e:
                    st.error(f"검사원 목록을 불러오는데 실패했습니다: {str(e)}")
                    # 백업 검사원 목록 설정
                    default_inspectors = [
                        {"id": "INS001", "name": "홍길동", "department": "CNC_1"},
                        {"id": "INS002", "name": "김철수", "department": "CNC_2"},
                        {"id": "INS003", "name": "이영희", "department": "PQC_LINE"},
                        {"id": "INS004", "name": "박민수", "department": "CNC_1"},
                        {"id": "INS005", "name": "최지훈", "department": "CNC_2"}
                    ]
                    st.session_state.inspectors = pd.DataFrame(default_inspectors)
            
            # 검사원 이름 목록 추출
            inspector_names = ["검사원을 선택하세요"] + st.session_state.inspectors["name"].tolist()
            
            inspector_name = st.selectbox(
                "검사원 이름",
                options=inspector_names,
                index=0,
                key="input_inspector_name"
            )
            
            # 검사원 ID 자동 입력
            inspector_id = ""
            if inspector_name != "검사원을 선택하세요":
                inspector_row = st.session_state.inspectors[st.session_state.inspectors["name"] == inspector_name]
                if not inspector_row.empty:
                    inspector_id = inspector_row.iloc[0]["id"]
            
            st.text_input("검사원 ID", value=inspector_id, key="input_inspector_id", disabled=True)
            
            process = st.selectbox(
                "공정",
                options=["공정을 선택하세요", "IQC", "CNC1_PQC", "CNC2_PQC", "OQC", "CNC OQC"],
                index=0,
                key="input_process"
            )
            
            # 모델명 선택 - 생산모델 데이터에서 가져오기
            models_df = load_product_models()
            model_options = ["모델을 선택하세요"]
            
            if not models_df.empty and "모델명" in models_df.columns:
                model_options += sorted(models_df["모델명"].unique().tolist())
            else:
                # 기본 모델 이름 목록
                model_options += ["BY2", "PA1", "PS SUB6", "E1", "PA3", "B7DUALSIM", "Y2", 
                         "B7R SUB6", "B6S6", "B5S6", "B7SUB", "B6", "B7MMW", "B7R MMW", "PA2", 
                         "B5M", "B7RR", "B7R SUB", "B7R", "B6M", "B7SUB6"]
            
            model_name = st.selectbox(
                "모델명",
                options=model_options,
                index=0,
                key="input_model"
            )
            
        with col2:
            inspection_date = st.date_input("검사일자", datetime.now(), key="input_date")
            
            lot_number = st.text_input("LOT 번호", placeholder="LOT 번호를 입력하세요", key="input_lot")
            
            work_time = st.number_input("작업 시간(분)", min_value=0, value=60, placeholder="작업 시간을 분 단위로 입력하세요", key="input_work_time")
        
        # 수량 정보 입력
        col1, col2, col3 = st.columns(3)
        with col1:
            plan_quantity = st.number_input("계획 수량", min_value=0, value=100, placeholder="계획 수량을 입력하세요", key="input_plan_qty")
        with col2:
            total_quantity = st.number_input("총 검사 수량", min_value=0, value=0, placeholder="총 검사 수량을 입력하세요", key="input_total_qty")
        with col3:
            defect_quantity = st.number_input("불량 수량", min_value=0, value=0, placeholder="불량 수량을 입력하세요", key="input_defect_qty")
        
        # 불량 정보 입력 섹션
        if defect_quantity > 0:
            st.subheader("불량 정보")
            
            # 불량 유형 선택
            defect_types = st.multiselect(
                "불량 유형 선택",
                options=["ĂN MÒN", "ATN CRACK", "CẮT SÂU, GỜ BẬC", "CHƯA GIA CÔNG HẾT", "CHƯA GIA CÔNG USB", 
                         "CRACK", "ĐỘ DẦY MAX", "ĐỘ DẦY MIN", "GÃY TOOL", "GỜ BẬC KHE SÓNG", 
                         "HOLE KÍCH THƯỚC", "KÍCH THƯỚC KHE SÓNG", "LỆCH USB", "Lỗi Khác", "MÒN TOOL, hết CNC", 
                         "NG 3D (MÁY)", "NG CHIỀU DÀI PHÔI", "NG CHIỀU RỘNG PHÔI", "NG ĐỘ DẦY PHÔI", "NG KÍCH THƯỚC", 
                         "NG PHÔI", "NG T CUT", "ø1 CRACK", "ø1 CRACK PIN JIG", "SETTING", 
                         "TẮC NƯỚC", "TÊN LỖI", "THAO TÁC1", "THAO TÁC2", "THAO TÁC3", 
                         "TOOL RUNG LẮC", "TRÀN NHỰA", "TRỤC A", "VẾT ĐÂM"],
                placeholder="불량 유형을 선택하세요",
                key="defect_types"
            )
            
            if defect_types:
                # 불량 유형별 수량 입력
                cols = st.columns(min(len(defect_types), 3))
                defect_details = []
                total_defects = 0
                
                for i, defect_type in enumerate(defect_types):
                    with cols[i % 3]:
                        qty = st.number_input(
                            f"{defect_type} 수량",
                            min_value=0,
                            max_value=defect_quantity,
                            key=f"defect_{i}"
                        )
                        if qty > 0:
                            defect_details.append({"type": defect_type, "quantity": qty})
                            total_defects += qty
                
                if total_defects != defect_quantity:
                    st.warning(f"입력한 불량 수량 합계 ({total_defects})가 총 불량 수량 ({defect_quantity})과 일치하지 않습니다.")
            
            # 불량 세부정보를 세션에 저장
            st.session_state.defect_details = defect_details if defect_types else []
        else:
            # 불량이 없는 경우 세션에서 불량 세부정보 초기화
            st.session_state.defect_details = []
        
        # 지표 계산 및 표시
        if total_quantity > 0:
            st.subheader("검사 지표")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                # 불량률 계산
                defect_rate = round((defect_quantity / total_quantity * 100), 2) if total_quantity > 0 else 0
                st.metric("불량률", f"{defect_rate}%")
            
            with col2:
                # 목표 대비 검사율 계산
                inspection_rate = round((total_quantity / plan_quantity * 100), 2) if plan_quantity > 0 else 0
                inspection_status = "✅ 목표 달성" if inspection_rate >= 100 else "⏳ 진행 중"
                st.metric("목표대비 검사율", f"{inspection_rate}%", delta=f"{inspection_status}")
            
            with col3:
                # 시간당 검사량 및 목표 달성 예상 시간
                if work_time > 0:
                    hourly_rate = round((total_quantity / work_time * 60), 1)
                    time_to_complete = round((plan_quantity - total_quantity) / hourly_rate * 60) if hourly_rate > 0 else 0
                    
                    if total_quantity < plan_quantity:
                        st.metric("시간당 검사량", f"{hourly_rate}개/시간", 
                                 delta=f"목표 달성까지 약 {time_to_complete}분 소요 예상")
                    else:
                        st.metric("시간당 검사량", f"{hourly_rate}개/시간", delta="목표 달성 완료")
        
        # 비고 입력
        memo = st.text_area("비고", placeholder="특이사항이 있으면 입력하세요", key="input_memo", help="추가 특이사항이 있으면 입력하세요.")
        
        # 저장 버튼
        if st.button("데이터 저장", use_container_width=True):
            # 입력 검증
            if inspector_name == "검사원을 선택하세요":
                st.error("검사원을 선택해주세요.")
            elif process == "공정을 선택하세요":
                st.error("공정을 선택해주세요.")    
            elif model_name == "모델을 선택하세요":
                st.error("모델을 선택해주세요.")
            elif total_quantity <= 0:
                st.error("검사 수량을 입력해주세요.")
            elif defect_quantity > total_quantity:
                st.error("불량 수량은 총 검사 수량보다 클 수 없습니다.")
            else:
                # 데이터 준비
                inspection_data = {
                    "검사원": inspector_name,
                    "공정": process,
                    "모델명": model_name,
                    "검사일자": inspection_date.strftime("%Y-%m-%d"),
                    "검사시간": time.strftime("%H:%M"),
                    "LOT번호": lot_number,
                    "작업시간(분)": work_time,
                    "계획수량": plan_quantity,
                    "검사수량": total_quantity,
                    "불량수량": defect_quantity,
                    "불량률(%)": defect_rate if total_quantity > 0 else 0,
                    "달성률(%)": inspection_rate if plan_quantity > 0 else 0,
                    "비고": memo
                }
                
                # 불량 세부정보가 있는 경우 함께 저장
                if defect_quantity > 0 and hasattr(st.session_state, 'defect_details') and st.session_state.defect_details:
                    inspection_data["불량세부"] = st.session_state.defect_details
                
                try:
                    # 데이터베이스에 저장 시도
                    response = save_inspection_data(inspection_data)
                    
                    # 불량 상세 저장 (각 불량 유형별로)
                    if defect_quantity > 0 and hasattr(st.session_state, 'defect_details'):
                        for defect_item in st.session_state.defect_details:
                            defect_data = {
                                "불량유형": defect_item["type"],
                                "수량": defect_item["quantity"],
                                "검사ID": inspection_data.get("id", ""),  # 검사 ID가 있는 경우
                                "등록일자": datetime.now().strftime("%Y-%m-%d"),
                                "등록자": inspector_name,
                                "비고": memo
                            }
                            try:
                                save_defect_data(defect_data)
                            except Exception as e:
                                st.warning(f"불량 세부 데이터 저장 중 오류: {str(e)}")
                    
                    st.success("검사실적 데이터가 성공적으로 저장되었습니다!")
                    
                    # 저장 성공 시 입력 필드 초기화 또는 다른 액션
                    st.balloons()
                    time.sleep(1)
                    st.experimental_rerun()  # 페이지 새로고침
                except Exception as e:
                    # 로컬 세션에 저장 (데이터베이스 연결 실패 시)
                    if 'saved_inspections' not in st.session_state:
                        st.session_state.saved_inspections = []
                    
                    st.session_state.saved_inspections.append(inspection_data)
                    st.success("검사실적 데이터가 세션에 저장되었습니다. (데이터베이스 연결이 되면 자동으로 동기화됩니다)")
                    st.info(f"참고: {str(e)}")
                    time.sleep(1)
                    st.experimental_rerun()  # 페이지 새로고침
    
    with tab3:
        # 간단한 데이터 검증 기능 구현
        st.subheader("데이터 검증")
        
        # 날짜 범위 선택
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", datetime.now() - timedelta(days=30), key="verify_start_date")
        with col2:
            end_date = st.date_input("종료일", datetime.now(), key="verify_end_date")
        
        # 검증 유형 선택
        verification_type = st.selectbox(
            "검증 유형",
            options=["검증 유형을 선택하세요", "누락 데이터 검사", "불량률 이상치 검사", "LOT 중복 검사", "전체 검사"],
            index=0,
            key="verification_type"
        )
        
        # 데이터 로드 및 검증 버튼
        if st.button("데이터 검증 실행", key="run_verification"):
            # 로딩 표시
            with st.spinner("데이터 검증 중..."):
                time.sleep(1)  # 검증 작업 시뮬레이션
                
                # 실제 검사 데이터 로드
                inspection_data = load_inspection_data()
                
                if not inspection_data.empty:
                    df = inspection_data.copy()
                    
                    # 날짜 필터 적용
                    if "검사일자" in df.columns:
                        try:
                            # 날짜 형식 확인 및 변환
                            if df["검사일자"].dtype != 'datetime64[ns]':
                                df["검사일자"] = pd.to_datetime(df["검사일자"])
                            
                            # 필터링
                            df = df[
                                (df["검사일자"].dt.date >= pd.Timestamp(start_date).date()) & 
                                (df["검사일자"].dt.date <= pd.Timestamp(end_date).date())
                            ]
                        except Exception as e:
                            st.warning(f"날짜 필터링 중 오류 발생: {str(e)}")
                    
                    st.success(f"총 {len(df)}개의 검사 데이터를 검증했습니다.")
                    
                    # 선택한 검증 유형에 따른 결과 표시
                    if verification_type == "누락 데이터 검사" or verification_type == "전체 검사":
                        # 필수 필드 정의
                        required_fields = ["검사원", "공정", "모델명", "검사일자", "검사수량"]
                        
                        # 필수 필드 누락 검사
                        missing_mask = df[required_fields].isnull().any(axis=1)
                        missing_data = df[missing_mask]
                        
                        if len(missing_data) > 0:
                            st.warning(f"{len(missing_data)}개의 검사 데이터에 필수 값이 누락되었습니다.")
                            st.dataframe(missing_data)
                        else:
                            st.info("누락된 필수 데이터가 없습니다.")
                    
                    if verification_type == "불량률 이상치 검사" or verification_type == "전체 검사":
                        if "불량률(%)" in df.columns:
                            # 이상치 기준: 불량률 5% 초과
                            outlier_threshold = 5.0
                            outliers = df[df["불량률(%)"] > outlier_threshold]
                            
                            if len(outliers) > 0:
                                st.warning(f"{len(outliers)}개의 검사 데이터에 불량률 이상치가 있습니다. (기준: {outlier_threshold}% 초과)")
                                display_cols = ["검사일자", "모델명", "공정", "검사수량", "불량수량", "불량률(%)"]
                                display_cols = [col for col in display_cols if col in outliers.columns]
                                st.dataframe(outliers[display_cols])
                            else:
                                st.info("불량률 이상치가 없습니다.")
                    
                    if verification_type == "LOT 중복 검사" or verification_type == "전체 검사":
                        if "LOT번호" in df.columns:
                            # LOT번호가 비어있지 않은 데이터만 고려
                            df_with_lot = df[df["LOT번호"].notna() & (df["LOT번호"] != "")]
                            duplicates = df_with_lot[df_with_lot.duplicated("LOT번호", keep=False)]
                            
                            if len(duplicates) > 0:
                                st.warning(f"{len(duplicates)}개의 검사 데이터에 LOT 번호 중복이 있습니다.")
                                display_cols = ["검사일자", "LOT번호", "모델명", "공정", "검사수량"]
                                display_cols = [col for col in display_cols if col in duplicates.columns]
                                st.dataframe(duplicates[display_cols].sort_values(by="LOT번호"))
                            else:
                                st.info("LOT 번호 중복이 없습니다.")
                else:
                    # 데이터가 없을 경우
                    st.info("검사 데이터가 없습니다. '실적 데이터 입력' 탭에서 데이터를 입력해주세요.")
            
            # 검증 완료 후 요약 정보
            if not inspection_data.empty:
                st.subheader("검증 요약")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # 검사 데이터 수
                    filtered_count = len(df) if 'df' in locals() else 0
                    total_count = len(inspection_data)
                    st.metric("총 검사 데이터", f"{total_count}건", f"조회 기간: {filtered_count}건")
                
                with col2:
                    # 평균 불량률
                    if "불량률(%)" in inspection_data.columns:
                        avg_defect_rate = inspection_data["불량률(%)"].mean()
                        st.metric("평균 불량률", f"{avg_defect_rate:.2f}%")
                    else:
                        st.metric("평균 불량률", "데이터 없음")
                
                with col3:
                    # 가장 많은 모델
                    if "모델명" in inspection_data.columns and not inspection_data.empty:
                        top_model = inspection_data["모델명"].value_counts().idxmax()
                        model_count = inspection_data["모델명"].value_counts().max()
                        st.metric("최다 검사 모델", f"{top_model}", f"{model_count}건")
                    else:
                        st.metric("최다 검사 모델", "데이터 없음")
                
                # 어제와 오늘의 검사 데이터 비교
                today = datetime.now().date()
                yesterday = today - timedelta(days=1)
                
                if "검사일자" in inspection_data.columns:
                    try:
                        # 날짜 형식 변환 (필요한 경우)
                        if inspection_data["검사일자"].dtype != 'datetime64[ns]':
                            date_column = pd.to_datetime(inspection_data["검사일자"])
                        else:
                            date_column = inspection_data["검사일자"]
                        
                        # 오늘과 어제 데이터 카운트
                        today_count = sum(date_column.dt.date == today)
                        yesterday_count = sum(date_column.dt.date == yesterday)
                        
                        # 변화율 계산
                        if yesterday_count > 0:
                            change_pct = ((today_count - yesterday_count) / yesterday_count) * 100
                            change_text = f"{change_pct:.1f}% ({yesterday_count}건 대비)"
                        else:
                            change_text = "어제 데이터 없음"
                        
                        st.metric("오늘 검사 건수", f"{today_count}건", change_text)
                    except Exception as e:
                        st.metric("오늘 검사 건수", "계산 오류", f"오류: {str(e)}")
                else:
                    st.metric("오늘 검사 건수", "데이터 없음")

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

def save_inspector(inspector_data):
    try:
        response = supabase.table('inspectors').insert(inspector_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"검사원 정보 저장 중 오류: {str(e)}")
        # 세션에 데이터 저장(백업)
        if 'saved_inspectors' not in st.session_state:
            st.session_state.saved_inspectors = []
        st.session_state.saved_inspectors.append(inspector_data)
        raise e

def update_inspector(inspector_id, updated_data):
    try:
        response = supabase.table('inspectors').update(updated_data).eq('id', inspector_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"검사원 정보 업데이트 중 오류: {str(e)}")
        raise e

def delete_inspector(inspector_id):
    try:
        response = supabase.table('inspectors').delete().eq('id', inspector_id).execute()
        return True
    except Exception as e:
        st.error(f"검사원 정보 삭제 중 오류: {str(e)}")
        return False

def inspector_management_ui():
    st.title("검사원 관리")
    
    # 검사원 목록 표시
    inspectors = load_inspectors()
    st.dataframe(inspectors)
    
    # 새 검사원 등록 폼
    with st.form("new_inspector_form"):
        st.subheader("새 검사원 등록")
        col1, col2 = st.columns(2)
        
        with col1:
            new_id = st.text_input("검사원 ID")
            new_name = st.text_input("이름")
        
        with col2:
            new_dept = st.selectbox("부서", options=["CNC_1", "CNC_2", "PQC_LINE"])
            new_process = st.selectbox("공정", options=["선삭", "밀링", "검사", "기타"])
        
        new_years = st.number_input("근속년수", min_value=0.0, step=0.5)
        submitted = st.form_submit_button("등록")
        
        if submitted:
            if not new_id or not new_name:
                st.error("검사원 ID와 이름은 필수입니다.")
            else:
                new_inspector = {
                    "id": new_id,
                    "name": new_name,
                    "department": new_dept,
                    "process": new_process,
                    "years_of_service": new_years
                }
                
                try:
                    save_inspector(new_inspector)
                    st.success(f"{new_name} 검사원이 성공적으로 등록되었습니다.")
                    st.rerun()  # 페이지 새로고침
                except Exception as e:
                    st.error(f"등록 실패: {str(e)}")

def sync_offline_data():
    if 'saved_inspectors' in st.session_state and st.session_state.saved_inspectors:
        with st.spinner("오프라인 데이터 동기화 중..."):
            success_count = 0
            for inspector in st.session_state.saved_inspectors[:]:
                try:
                    save_inspector(inspector)
                    st.session_state.saved_inspectors.remove(inspector)
                    success_count += 1
                except Exception:
                    continue
            
            if success_count > 0:
                st.success(f"{success_count}개의 검사원 데이터가 동기화되었습니다.")
            
            if st.session_state.saved_inspectors:
                st.warning(f"{len(st.session_state.saved_inspectors)}개의 데이터는 여전히 동기화되지 않았습니다.")

# 생산모델 데이터 가져오기
def load_product_models():
    """
    생산모델 데이터를 로드합니다.
    """
    try:
        # CSV 파일이 있는지 먼저 확인
        if os.path.exists("data/product_models.csv"):
            df = pd.read_csv("data/product_models.csv")
            return df
        # JSON 파일이 있는지 확인
        elif (DATA_DIR / "product_models.json").exists():
            with open(DATA_DIR / "product_models.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "models" in data:
                    df = pd.DataFrame(data["models"])
                    # 저장 형식을 CSV로 통일
                    df.to_csv("data/product_models.csv", index=False)
                    return df
        
        # 데이터가 없으면 빈 DataFrame 생성
        return pd.DataFrame(columns=["id", "모델명", "공정"])
    except Exception as e:
        print(f"생산모델 데이터 로드 중 오류: {str(e)}")
        return pd.DataFrame(columns=["id", "모델명", "공정"])

# 생산모델 데이터 저장
def save_product_models(df):
    """
    생산모델 데이터를 저장합니다.
    
    Args:
        df (pandas.DataFrame): 저장할 생산모델 데이터
        
    Returns:
        bool: 저장 성공 여부
    """
    try:
        # 데이터 디렉토리 확인
        if not os.path.exists("data"):
            os.makedirs("data")
            
        # 데이터 저장 (CSV 형식)
        df.to_csv("data/product_models.csv", index=False)
        return True
    except Exception as e:
        print(f"생산모델 데이터 저장 중 오류: {str(e)}")
        return False

# 여기서부터 제품 모델 관리 페이지 코드

if st.session_state.page == "product_model":
    # 생산모델 관리 페이지
    st.markdown("<div class='title-area'><h1>📦 생산모델 관리</h1></div>", unsafe_allow_html=True)
    
    # 관리자 권한 확인
    if st.session_state.user_role != "관리자":
        st.warning("이 페이지는 관리자만 접근할 수 있습니다.")
        st.stop()
    
    # 생산모델 데이터 로드
    product_models_df = load_product_models()
    
    # 탭 생성
    tab1, tab2 = st.tabs(["📋 생산모델 목록", "➕ 생산모델 추가/수정"])
    
    with tab1:
        st.subheader("생산모델 목록")
        
        # 검색 필터
        col1, col2 = st.columns(2)
        with col1:
            search_model = st.text_input("모델명 검색", placeholder="검색어를 입력하세요")
        with col2:
            process_options = ["전체"]
            if not product_models_df.empty and "공정" in product_models_df.columns:
                process_options += sorted(product_models_df["공정"].unique().tolist())
            process_filter = st.selectbox("공정 필터", options=process_options)
        
        # 필터링 적용
        filtered_df = product_models_df.copy()
        if search_model and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["모델명"].str.contains(search_model, case=False)]
        if process_filter != "전체" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["공정"] == process_filter]
        
        # 결과 표시
        if not filtered_df.empty:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", format="%d"),
                    "모델명": st.column_config.TextColumn("모델명"),
                    "공정": st.column_config.TextColumn("공정")
                }
            )
        else:
            st.info("검색 조건에 맞는 생산모델이 없습니다.")
    
    with tab2:
        st.subheader("생산모델 추가/수정")
        
        # 작업 선택을 별도 컴포넌트로 분리
        edit_mode = st.radio(
            "작업 선택", 
            ["새 모델 추가", "기존 모델 수정", "모델 삭제"], 
            horizontal=True
        )
        
        st.markdown("---")
        
        # 새 모델 추가 양식
        if edit_mode == "새 모델 추가":
            st.subheader("새 모델 추가")
            
            with st.form("add_model_form"):
                # 새 ID 생성 (기존 최대 ID + 1)
                new_id = 1
                if not product_models_df.empty and "id" in product_models_df.columns:
                    new_id = int(product_models_df["id"].max()) + 1
                
                st.number_input("모델 ID", value=new_id, disabled=True, key="new_model_id")
                model_name = st.text_input("모델명", placeholder="예: PA1, B7SUB6", key="new_model_name")
                process_name = st.text_input("공정", placeholder="예: C1, C2, 연삭", key="new_process")
                
                add_button = st.form_submit_button("생산모델 추가", use_container_width=True)
                
                if add_button:
                    if not model_name or not process_name:
                        st.error("모든 필드를 입력해주세요.")
                    else:
                        # 새 모델 추가
                        new_model = {"id": new_id, "모델명": model_name, "공정": process_name}
                        updated_df = pd.concat([product_models_df, pd.DataFrame([new_model])], ignore_index=True)
                        
                        # 저장
                        if save_product_models(updated_df):
                            st.success("생산모델이 성공적으로 추가되었습니다!")
                            st.experimental_rerun()
                        else:
                            st.error("생산모델 저장 중 오류가 발생했습니다.")
        
        # 기존 모델 수정 양식
        elif edit_mode == "기존 모델 수정":
            st.subheader("기존 모델 수정")
            
            # 수정할 모델이 있는지 확인
            if product_models_df.empty:
                st.warning("수정할 생산모델이 없습니다. 먼저 모델을 추가해주세요.")
            else:
                # 수정할 모델 선택
                model_ids = product_models_df["id"].astype(str).tolist()
                model_labels = [f"{row['id']} - {row['모델명']} ({row['공정']})" for _, row in product_models_df.iterrows()]
                
                selected_id_index = st.selectbox(
                    "수정할 모델 선택", 
                    range(len(model_ids)), 
                    format_func=lambda i: model_labels[i],
                    key="edit_model_select"
                )
                
                selected_id = int(model_ids[selected_id_index])
                selected_row = product_models_df[product_models_df["id"] == selected_id].iloc[0]
                
                with st.form("edit_model_form"):
                    st.number_input("모델 ID", value=selected_id, disabled=True, key="edit_model_id")
                    edited_model_name = st.text_input("모델명", value=selected_row["모델명"], key="edit_model_name")
                    edited_process = st.text_input("공정", value=selected_row["공정"], key="edit_process")
                    
                    edit_button = st.form_submit_button("변경사항 저장", use_container_width=True)
                    
                    if edit_button:
                        if not edited_model_name or not edited_process:
                            st.error("모든 필드를 입력해주세요.")
                        else:
                            # 모델 업데이트
                            updated_df = product_models_df.copy()
                            updated_df.loc[updated_df["id"] == selected_id, "모델명"] = edited_model_name
                            updated_df.loc[updated_df["id"] == selected_id, "공정"] = edited_process
                            
                            # 저장
                            if save_product_models(updated_df):
                                st.success("생산모델이 성공적으로 수정되었습니다!")
                                st.experimental_rerun()
                            else:
                                st.error("생산모델 수정 중 오류가 발생했습니다.")
        
        # 모델 삭제 양식
        else:  # 모델 삭제
            st.subheader("모델 삭제")
            
            # 삭제할 모델이 있는지 확인
            if product_models_df.empty:
                st.warning("삭제할 생산모델이 없습니다.")
            else:
                # 삭제할 모델 선택
                model_ids = product_models_df["id"].astype(str).tolist()
                model_labels = [f"{row['id']} - {row['모델명']} ({row['공정']})" for _, row in product_models_df.iterrows()]
                
                selected_id_index = st.selectbox(
                    "삭제할 모델 선택", 
                    range(len(model_ids)), 
                    format_func=lambda i: model_labels[i],
                    key="delete_model_select"
                )
                
                selected_id = int(model_ids[selected_id_index])
                selected_row = product_models_df[product_models_df["id"] == selected_id].iloc[0]
                
                st.info(f"선택한 모델: {selected_row['모델명']} (공정: {selected_row['공정']})")
                
                with st.form("delete_model_form"):
                    confirm_delete = st.checkbox("삭제를 확인합니다", key="confirm_delete")
                    delete_button = st.form_submit_button("모델 삭제", use_container_width=True)
                    
                    if delete_button:
                        if not confirm_delete:
                            st.error("삭제를 확인하려면 체크박스를 선택해주세요.")
                        else:
                            # 모델 삭제
                            updated_df = product_models_df[product_models_df["id"] != selected_id].reset_index(drop=True)
                            
                            # 저장
                            if save_product_models(updated_df):
                                st.success("생산모델이 성공적으로 삭제되었습니다!")
                                st.experimental_rerun()
                            else:
                                st.error("생산모델 삭제 중 오류가 발생했습니다.")

elif st.session_state.page == "another_page":
    # 다른 페이지 로직
    pass

# 검사 데이터 불러오기
def load_inspection_data():
    try:
        # Supabase에서 데이터 가져오기
        response = supabase.table('inspection_data').select('*').execute()
        data = response.data
        
        # 데이터가 없으면 빈 DataFrame 반환
        if not data:
            return pd.DataFrame()
        
        # 영문 필드명을 한글로 변환
        field_mapping = {
            "inspector_name": "검사원",
            "process": "공정",
            "model_name": "모델명",
            "inspection_date": "검사일자",
            "inspection_time": "검사시간",
            "lot_number": "LOT번호",
            "work_time_minutes": "작업시간(분)",
            "planned_quantity": "계획수량",
            "total_inspected": "검사수량",
            "total_defects": "불량수량",
            "defect_rate": "불량률(%)",
            "achievement_rate": "달성률(%)",
            "remarks": "비고"
        }
        
        # DataFrame 변환
        df = pd.DataFrame(data)
        
        # 필드명 변환
        renamed_columns = {}
        for eng, kor in field_mapping.items():
            if eng in df.columns:
                renamed_columns[eng] = kor
        
        # 컬럼 이름 변경
        df = df.rename(columns=renamed_columns)
        
        # 불량 세부정보 처리
        if "defect_details" in df.columns:
            try:
                df["불량세부"] = df["defect_details"].apply(lambda x: json.loads(x) if x and isinstance(x, str) else [])
                df = df.drop(columns=["defect_details"])
            except:
                df["불량세부"] = [[]]
        
        return df
    
    except Exception as e:
        # 오류 발생시 세션 데이터 반환(백업)
        if 'saved_inspections' in st.session_state and st.session_state.saved_inspections:
            return pd.DataFrame(st.session_state.saved_inspections)
        # 아무 데이터도 없는 경우
        return pd.DataFrame()

# 불량 데이터 불러오기
def load_defect_data():
    try:
        # Supabase에서 데이터 가져오기
        response = supabase.table('defect_data').select('*').execute()
        data = response.data
        
        # 데이터가 없으면 빈 DataFrame 반환
        if not data:
            return pd.DataFrame()
        
        # 영문 필드명을 한글로 변환
        field_mapping = {
            "defect_type": "불량유형",
            "quantity": "수량",
            "inspection_id": "검사ID",
            "registration_date": "등록일자",
            "registered_by": "등록자",
            "remarks": "비고"
        }
        
        # DataFrame 변환
        df = pd.DataFrame(data)
        
        # 필드명 변환
        renamed_columns = {}
        for eng, kor in field_mapping.items():
            if eng in df.columns:
                renamed_columns[eng] = kor
        
        # 컬럼 이름 변경
        df = df.rename(columns=renamed_columns)
        
        return df
    
    except Exception as e:
        # 오류 발생시 세션 데이터 반환(백업)
        if 'saved_defects' in st.session_state and st.session_state.saved_defects:
            return pd.DataFrame(st.session_state.saved_defects)
        # 아무 데이터도 없는 경우
        return pd.DataFrame()

# 실적 데이터 입력 탭에서 불량 유형 선택 및 수량 입력 UI 수정
def load_defect_types():
    try:
        # 데이터베이스에서 불량 유형 목록 불러오기
        response = supabase.table('defect_types').select('*').execute()
        data = response.data
        
        if data:
            return [item['type_name'] for item in data]
        else:
            # 기본 불량 유형 목록
            return ["ATN CRACK", "BONG BIA", "BULONG", "BUỒN", "BỤI NƯỚC", "CHỎM", "DA BEO", "DÂY", 
                    "DẬP", "DP - KÝ", "DẬP - TRỤC A", "DẬP PHÔI", "GIOĂNG", "HẤP", "KẼM", "KHẤC",
                    "KHUYẾT", "LỒI", "LỬNG", "NHẤN", "NƯỚC NGOÀI", "OV VÍT", "ĂN MÒN", "CHAI CẠNH", 
                    "CHẾT MÁY", "CHÊNH", "CỬA NƯỚC", "DROP", "KẸP", "NG PHÔI", "NG T CUT", 
                    "ø1 CRACK", "ø1 CRACK PIN JIG", "SETTING", "TẮC NƯỚC", "TÊN LỖI", 
                    "THAO TÁC1", "THAO TÁC2", "THAO TÁC3", "TOOL RUNG LẮC", "TRÀN NHỰA", 
                    "TRỤC A", "VẾT ĐÂM"]
    except Exception as e:
        # 오류 발생시 기본 목록 반환
        return ["규격 불량", "외관 불량", "기능 불량", "치수 불량", "기타"]

# 불량 유형 입력 UI 부분
def render_defect_input():
    defect_types = load_defect_types()
    
    st.subheader("불량 상세 정보")
    
    defect_types = st.multiselect(
        "불량 유형 선택",
        options=defect_types,
        placeholder="불량 유형을 선택하세요",
        key="defect_types"
    )
    
    if defect_types:
        # 불량 유형별 수량 입력
        cols = st.columns(len(defect_types))
        defect_details = []
        
        for i, defect_type in enumerate(defect_types):
            with cols[i]:
                st.write(f"**{defect_type}**")
                quantity = st.number_input(
                    "수량",
                    min_value=0,
                    max_value=1000,
                    value=1,
                    key=f"defect_quantity_{i}"
                )
                defect_details.append({
                    "type": defect_type,
                    "quantity": quantity
                })
        
        return defect_details
    return []

# 데이터 검증 함수
def validate_inspection_data(df):
    validation_results = []
    
    # 데이터가 없는 경우
    if df.empty:
        return [{"severity": "info", "message": "검증할 데이터가 없습니다."}]
    
    # 필수 컬럼 확인
    required_columns = ["검사원", "공정", "모델명", "검사일자", "검사수량"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        validation_results.append({
            "severity": "error",
            "message": f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}"
        })
    
    # 컬럼 존재하는 경우에만 검증 수행
    if "검사일자" in df.columns:
        # 날짜 형식 검증
        invalid_dates = df[~df["검사일자"].astype(str).str.match(r'^\d{4}-\d{2}-\d{2}$')]["검사일자"].tolist()
        if invalid_dates:
            validation_results.append({
                "severity": "warning",
                "message": f"올바르지 않은 날짜 형식이 {len(invalid_dates)}건 발견되었습니다."
            })
    
    if "검사수량" in df.columns and "불량수량" in df.columns:
        # 불량수량 > 검사수량 검증
        invalid_defects = df[df["불량수량"] > df["검사수량"]]
        if not invalid_defects.empty:
            validation_results.append({
                "severity": "error",
                "message": f"불량수량이 검사수량보다 큰 데이터가 {len(invalid_defects)}건 발견되었습니다."
            })
    
    if "불량률(%)" in df.columns:
        # 불량률 계산 오류 검증
        if "검사수량" in df.columns and "불량수량" in df.columns:
            # 계산된 불량률
            calculated_rates = df.apply(
                lambda row: round((row["불량수량"] / row["검사수량"]) * 100, 2) if row["검사수량"] > 0 else 0, 
                axis=1
            )
            
            # 저장된 불량률과 계산된 불량률 비교 (소수점 둘째자리까지 반올림하여 비교)
            rate_errors = df[abs(calculated_rates - df["불량률(%)"]) > 0.02]
            
            if not rate_errors.empty:
                validation_results.append({
                    "severity": "warning",
                    "message": f"불량률 계산이 일치하지 않는 데이터가 {len(rate_errors)}건 발견되었습니다."
                })
    
    # 검증 결과가 없으면 정상
    if not validation_results:
        validation_results.append({
            "severity": "success",
            "message": "모든 데이터가 정상적으로 검증되었습니다."
        })
    
    return validation_results

# 데이터 검증 결과 표시 함수
def display_validation_results(validation_results):
    for result in validation_results:
        severity = result["severity"]
        message = result["message"]
        
        if severity == "error":
            st.error(message)
        elif severity == "warning":
            st.warning(message)
        elif severity == "info":
            st.info(message)
        elif severity == "success":
            st.success(message)

# 데이터 검증 탭 UI
def inspection_data_validation_ui():
    st.subheader("실적 데이터 검증")
    
    # 데이터 불러오기
    df = load_inspection_data()
    
    # 필터링 옵션
    st.write("#### 필터링 옵션")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "시작 날짜",
            datetime.date.today() - datetime.timedelta(days=30),
            key="validation_start_date"
        )
    
    with col2:
        end_date = st.date_input(
            "종료 날짜",
            datetime.date.today(),
            key="validation_end_date"
        )
    
    # 모델 필터
    if "모델명" in df.columns and not df.empty:
        model_options = ["모두"] + sorted(df["모델명"].unique().tolist())
        selected_model = st.selectbox("모델 선택", model_options, key="validation_model")
    else:
        selected_model = "모두"
    
    # 검사원 필터
    if "검사원" in df.columns and not df.empty:
        inspector_options = ["모두"] + sorted(df["검사원"].unique().tolist())
        selected_inspector = st.selectbox("검사원 선택", inspector_options, key="validation_inspector")
    else:
        selected_inspector = "모두"
    
    # 데이터 필터링
    filtered_df = df.copy()
    
    if not df.empty and "검사일자" in df.columns:
        # 날짜 필터링
        filtered_df = filtered_df[
            (pd.to_datetime(filtered_df["검사일자"]).dt.date >= start_date) &
            (pd.to_datetime(filtered_df["검사일자"]).dt.date <= end_date)
        ]
        
        # 모델 필터링
        if selected_model != "모두" and "모델명" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["모델명"] == selected_model]
        
        # 검사원 필터링
        if selected_inspector != "모두" and "검사원" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["검사원"] == selected_inspector]
    
    # 검증 실행 버튼
    if st.button("데이터 검증 실행", key="run_validation"):
        with st.spinner("데이터 검증 중..."):
            validation_results = validate_inspection_data(filtered_df)
            
            st.write("#### 검증 결과")
            display_validation_results(validation_results)
            
            # 검증 결과 표시
            if not filtered_df.empty:
                st.write(f"검증 데이터: {len(filtered_df)}건")
                
                # 테이블로 표시
                st.dataframe(filtered_df, use_container_width=True)
            else:
                st.info("필터링 조건에 맞는 데이터가 없습니다.")
    
    # 데이터 수정 안내
    st.markdown("""
    **데이터 수정이 필요한 경우:**
    1. '실적 데이터 조회' 탭에서 해당 데이터를 찾아 수정할 수 있습니다.
    2. 대량 수정이 필요한 경우 관리자에게 문의하세요.
    """)

# 검사실적 관리 메인 UI에 데이터 검증 탭 추가
def inspection_data_management_ui():
    st.title("검사실적 관리")
    
    tabs = st.tabs(["실적 데이터 조회", "실적 데이터 입력", "데이터 검증"])
    
    with tabs[0]:
        inspection_data_query_ui()
    
    with tabs[1]:
        inspection_data_input_ui()
    
    with tabs[2]:
        inspection_data_validation_ui()
