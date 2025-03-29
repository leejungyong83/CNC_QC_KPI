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
        st.session_state.page = "dashboard"
        st.rerun()
        return True
    
    if "login_attempts" not in st.session_state:
        st.session_state.login_attempts = 0

    if st.session_state.login_attempts >= 3:
        st.error("로그인 시도 횟수를 초과했습니다. 잠시 후 다시 시도해주세요.")
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
                st.session_state.page = "dashboard"
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

# 여기서부터 로그인 성공 후 표시되는 내용
st.sidebar.success(f"{st.session_state.username}님 환영합니다!")
st.sidebar.write(f"역할: {st.session_state.user_role}")

# 로그아웃 버튼
if st.sidebar.button("로그아웃"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = "일반"
    st.session_state.page = "login"
    st.rerun()

# 페이지 네비게이션
pages = {
    "대시보드": "dashboard",
    "검사 데이터 입력": "input_inspection",
    "검사 데이터 조회": "view_inspection",
}

if st.session_state.user_role == "관리자":
    pages["검사원 관리"] = "manage_inspectors"
    pages["시스템 설정"] = "settings"

selected_page = st.sidebar.radio("메뉴", list(pages.keys()))
st.session_state.page = pages[selected_page]

# 검사원 정보 가져오기
def load_inspectors():
    try:
        response = supabase.table('inspectors').select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            # 기본 검사원 데이터 추가
            default_inspectors = [
                {"id": "INS001", "name": "홍길동", "department": "CNC_1", "process": "선삭", "years_of_service": 5.5},
                {"id": "INS002", "name": "김철수", "department": "CNC_2", "process": "밀링", "years_of_service": 3.2},
                {"id": "INS003", "name": "이영희", "department": "PQC_LINE", "process": "검사", "years_of_service": 7.1}
            ]
            for inspector in default_inspectors:
                supabase.table('inspectors').insert(inspector).execute()
            return pd.DataFrame(default_inspectors)
    except Exception as e:
        st.error(f"검사원 정보 로딩 중 오류: {str(e)}")
        return pd.DataFrame({"id": [], "name": [], "department": [], "process": [], "years_of_service": []})

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

# 현재 페이지에 따라 다른 내용 표시
if st.session_state.page == "dashboard":
    st.title("CNC 품질관리 시스템 - 대시보드")
    
    # 날짜 필터
    start_date = st.date_input("시작일", datetime.now() - timedelta(days=30))
    end_date = st.date_input("종료일", datetime.now())
    
    # 대시보드 콘텐츠
    st.write("### 주요 품질 지표")
    
    # 샘플 데이터
    cols = st.columns(4)
    with cols[0]:
        st.metric("총 검사 건수", "152", "+12")
    with cols[1]:
        st.metric("평균 불량률", "0.8%", "-0.2%")
    with cols[2]:
        st.metric("최다 불량 유형", "치수불량", "")
    with cols[3]:
        st.metric("진행 중인 작업", "3", "+1")
    
    st.write("### 공정별 불량률 추이")
    # 샘플 차트 데이터
    chart_data = pd.DataFrame({
        "날짜": pd.date_range(start=start_date, end=end_date, freq="D"),
        "선삭": np.random.rand(len(pd.date_range(start=start_date, end=end_date, freq="D"))) * 2,
        "밀링": np.random.rand(len(pd.date_range(start=start_date, end=end_date, freq="D"))) * 1.5,
    }).melt("날짜", var_name="공정", value_name="불량률")
    
    fig = px.line(chart_data, x="날짜", y="불량률", color="공정", 
                 title="공정별 불량률 추이")
    st.plotly_chart(fig, use_container_width=True)
    
    # 불량 유형 분포
    st.write("### 불량 유형 분포")
    defect_types = ["치수", "표면거칠기", "칩핑", "기타"]
    defect_counts = np.random.randint(5, 30, size=len(defect_types))
    
    fig = px.pie(values=defect_counts, names=defect_types, 
                title="불량 유형 분포")
    st.plotly_chart(fig, use_container_width=True)

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
            
            try:
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
                    supabase.table('inspectors').insert(new_inspector).execute()
                    st.success(f"{name} 검사원이 성공적으로 등록되었습니다.")
                    st.session_state.inspectors = load_inspectors()
                    st.rerun()
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