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

# 페이지 설정을 가장 먼저 실행
st.set_page_config(
    page_title="품질검사 KPI 관리 시스템",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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
    # 디버그 모드 - 개발 환경에서만 사용 (프로덕션에서는 제거 필요)
    if st.sidebar.button("디버그 모드로 로그인"):
        st.session_state.logged_in = True
        st.session_state.user_role = "관리자"
        st.session_state.username = "admin_debug"
        st.session_state.login_attempts = 0
        st.session_state.show_welcome_popup = True
        st.session_state.page = "dashboard"
        st.rerun()
        return True
    
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    if st.session_state.login_attempts >= 3:
        st.error("로그인 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.")
        time.sleep(1)  # 잠시 지연
        st.session_state.login_attempts = 0  # 제한 시간 후 리셋
        return False

    # 로그인 폼
    with st.form("login_form"):
        username = st.text_input("아이디")
        password = st.text_input("비밀번호", type="password")
        submitted = st.form_submit_button("로그인")

        if submitted:
            if not username:
                st.error("아이디를 입력하세요.")
                return False
            if not password:
                st.error("비밀번호를 입력하세요.")
                return False

            success, user_role = verify_login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user_role = user_role
                st.session_state.username = username
                st.session_state.login_attempts = 0
                st.session_state.show_welcome_popup = True
                st.session_state.page = "dashboard"
                st.success(f"{username}님 환영합니다!")
                time.sleep(1)  # 잠시 환영 메시지 보여주기
                st.rerun()
                return True
            else:
                st.session_state.login_attempts += 1
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                if st.session_state.login_attempts >= 3:
                    st.warning("로그인을 3회 이상 실패했습니다. 계정 정보를 확인하세요.")
                return False

    return False

if not check_password():
    st.stop()

# 검사원 정보 가져오기
def load_inspectors():
    response = supabase.table('inspectors').select("*").execute()
    return pd.DataFrame(response.data)

# 검사 데이터 저장
def save_inspection_data(data):
    response = supabase.table('inspection_data').insert(data).execute()
    return response

# 불량 데이터 저장
def save_defect_data(data):
    response = supabase.table('defect_data').insert(data).execute()
    return response

# 세션 상태 초기화
if 'inspectors' not in st.session_state:
    st.session_state.inspectors = load_inspectors()

if 'registered_defects' not in st.session_state:
    st.session_state.registered_defects = []

# 메인 앱 UI
st.title("CNC 품질관리 시스템")

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
        st.rerun()
        
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
            
            # 검사 데이터 저장
            inspection_response = save_inspection_data(inspection_data)
            inspection_id = inspection_response.data[0]['id']
            
            # 불량 데이터 저장
            for defect in st.session_state.registered_defects:
                defect_data = {
                    "inspection_id": inspection_id,
                    "defect_type": defect['type'],
                    "quantity": defect['quantity']
                }
                save_defect_data(defect_data)
            
            st.success("검사 데이터가 성공적으로 저장되었습니다.")
            st.session_state.registered_defects = []
            st.rerun()
        else:
            st.warning("저장할 불량 데이터가 없습니다.")

def password_entered():
    try:
        # Streamlit Cloud에서 secrets를 사용하는 경우
        credentials_usernames = st.secrets["credentials"]["usernames"]
        credentials_passwords = st.secrets["credentials"]["passwords"]
    except KeyError:
        # 기본 인증 정보
        credentials_usernames = ["admin"]
        credentials_passwords = ["admin123"]
        
    if st.session_state["username"] in credentials_usernames and st.session_state["password"] == credentials_passwords[credentials_usernames.index(st.session_state["username"])]:
        st.session_state["password_correct"] = True
        del st.session_state["password"]
    else:
        st.session_state["password_correct"] = False 