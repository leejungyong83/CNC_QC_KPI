import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import numpy as np
import time
import json
from pathlib import Path

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

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None

# 데이터 저장 경로 설정
DATA_PATH = Path("data")
DATA_PATH.mkdir(exist_ok=True)

INSPECTION_DATA_FILE = DATA_PATH / "inspection_data.json"
INSPECTOR_DATA_FILE = DATA_PATH / "inspector_data.json"
USER_DATA_FILE = DATA_PATH / "user_data.json"

# 데이터 저장/로드 함수 추가
def save_json_data(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)

def load_json_data(file_path, default_data):
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return default_data

# 검사 데이터 관련 함수
def save_inspection_data(data):
    save_json_data(INSPECTION_DATA_FILE, data)

def load_inspection_data():
    return load_json_data(INSPECTION_DATA_FILE, {"inspections": []})

# 검사원 데이터 관련 함수
def save_inspector_data(data):
    save_json_data(INSPECTOR_DATA_FILE, data)

def load_inspector_data():
    return load_json_data(INSPECTOR_DATA_FILE, {"inspectors": []})

# 사용자 데이터 관련 함수
def save_user_data(data):
    save_json_data(USER_DATA_FILE, data)

def load_user_data():
    default_users = {
        "users": [
            {
                "email": "dlwjddyd83@gmail.com",
                "password": "11112222",
                "name": "관리자",
                "role": "admin",
                "registered_date": "2024-01-01",
                "last_login": "2024-01-15"
            },
            {
                "email": "user",
                "password": "1234",
                "name": "일반사용자1",
                "role": "user",
                "registered_date": "2024-01-02",
                "last_login": "2024-01-14"
            }
        ]
    }
    return load_json_data(USER_DATA_FILE, default_users)

# 로그인 검증 함수 수정
def verify_login(username, password):
    if username == "dlwjddyd83@gmail.com" and password == "11112222":
        return True, "admin"
    elif username == "user" and password == "1234":
        return True, "user"
    return False, None

# 로그인 페이지 함수 수정
def show_login():
    st.markdown(
        """
        <style>
        .block-container { max-width: 400px; padding-top: 2rem; }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.title("📊 품질검사 KPI 관리 시스템")
    
    with st.form("login_form"):
        username = st.text_input(
            "아이디",
            placeholder="이메일 주소를 입력하세요"
        )
        
        password = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호를 입력하세요"
        )
        
        submit = st.form_submit_button(
            "로그인",
            use_container_width=True
        )
        
        if submit:
            if not username or not password:
                st.error("아이디와 비밀번호를 모두 입력해주세요.")
            else:
                is_valid, role = verify_login(username, password)
                if is_valid:
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.markdown(
        """
        <div style='text-align: center; color: #6B7280; font-size: 0.875rem; margin-top: 2rem;'>
            © 2024 품질검사 KPI 관리 시스템 v1.0.0
        </div>
        """,
        unsafe_allow_html=True
    )

# 사이드바 함수 수정
def show_sidebar():
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
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'user_role' not in st.session_state:
        st.session_state.user_role = None

    # 페이지 라우팅
    if not st.session_state.logged_in:
        show_login()
    else:
        if st.session_state.page == "dashboard":
            show_dashboard()
        elif st.session_state.page == "daily_performance":
            show_daily_performance()
        elif st.session_state.page == "report":
            show_report()
        elif st.session_state.page == "inspector_management":
            show_inspector_form()
        elif st.session_state.page == "user_management":
            if st.session_state.user_role == "admin":
                show_user_management()
            else:
                st.error("접근 권한이 없습니다.")
                st.session_state.page = "dashboard"

# 대시보드 페이지
def show_dashboard():
    # 메트릭 카드 스타일 적용
    st.markdown("""
        <style>
            [data-testid="metric-container"] {
                background-color: white;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.05);
                width: 100%;
                min-width: 200px;
                border: 1px solid #e5e7eb;
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
    
    st.markdown("### 📊 실시간 모니터링")
    
    # 차트 영역 - 컬럼 비율 조정
    col1, col2 = st.columns([1.6, 1])
    
    with col1:
        st.markdown("#### 📅 일일 검사현황")
        
        # 일일 데이터 로드
        data = load_inspection_data()
        if data["inspections"]:
            df = pd.DataFrame(data["inspections"])
            df['날짜'] = pd.to_datetime(df['날짜'])
            
            # 최근 7일간의 데이터 필터링
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=6)
            mask = (df['날짜'].dt.date >= start_date) & (df['날짜'].dt.date <= end_date)
            daily_df = df[mask].copy()
            
            if not daily_df.empty:
                # 일별 집계
                daily_data = daily_df.groupby(daily_df['날짜'].dt.date).agg({
                    '검사수량': 'sum',
                    '불량수량': 'sum',
                    '작업시간': 'sum'
                }).reset_index()
                
                # 불량률과 효율 계산
                daily_data['불량률'] = (daily_data['불량수량'] / daily_data['검사수량'] * 100).round(2)
                daily_data['시간당효율'] = (daily_data['검사수량'] / (daily_data['작업시간']/60)).round(1)
                daily_data['효율률'] = (daily_data['시간당효율'] / 200 * 100).round(1)
                
                # 날짜 포맷 변경
                daily_data['날짜_표시'] = daily_data['날짜'].apply(
                    lambda x: f"{x.strftime('%m/%d')}\n{['월','화','수','목','금','토','일'][x.weekday()]}"
                )
                
                # 차트 생성
                fig = go.Figure()
                
                # 검사량 바 차트
                fig.add_trace(go.Bar(
                    x=daily_data['날짜_표시'],
                    y=daily_data['검사수량'],
                    name='검사량',
                    marker_color='rgba(59, 130, 246, 0.7)',
                    hovertemplate='%{x}<br>검사량: %{y:,.0f}개<extra></extra>',
                    text=daily_data['검사수량'].apply(lambda x: f'{x:,}'),
                    textposition='outside',
                    textfont=dict(
                        size=11,
                        color='rgba(55, 65, 81, 0.8)'
                    )
                ))
                
                # 불량률 라인 차트
                fig.add_trace(go.Scatter(
                    x=daily_data['날짜_표시'],
                    y=daily_data['불량률'],
                    name='불량률',
                    line=dict(color='#EF4444', width=2),
                    yaxis='y2',
                    hovertemplate='%{x}<br>불량률: %{y:.1f}%<extra></extra>',
                    text=daily_data['불량률'].apply(lambda x: f'{x:.1f}%'),
                    textposition='top center',
                    mode='lines+markers+text',
                    textfont=dict(
                        size=11,
                        color='#EF4444'
                    )
                ))
                
                # 효율률 라인 차트
                fig.add_trace(go.Scatter(
                    x=daily_data['날짜_표시'],
                    y=daily_data['효율률'],
                    name='효율률',
                    line=dict(color='#10B981', width=2, dash='dot'),
                    yaxis='y2',
                    hovertemplate='%{x}<br>효율률: %{y:.1f}%<extra></extra>',
                    text=daily_data['효율률'].apply(lambda x: f'{x:.1f}%'),
                    textposition='bottom center',
                    mode='lines+markers+text',
                    textfont=dict(
                        size=11,
                        color='#10B981'
                    )
                ))
                
                # 차트 레이아웃 설정
                fig.update_layout(
                    height=400,
                    yaxis=dict(
                        title='검사량(개)',
                        gridcolor='rgba(0,0,0,0.1)',
                        showgrid=True,
                        zeroline=False,
                        tickformat=',d',
                        range=[0, daily_data['검사수량'].max() * 1.2]
                    ),
                    yaxis2=dict(
                        title='비율(%)',
                        overlaying='y',
                        side='right',
                        gridcolor='rgba(0,0,0,0.1)',
                        showgrid=False,
                        zeroline=False,
                        range=[0, max(100, daily_data['효율률'].max() * 1.1)]
                    ),
                    xaxis=dict(
                        showgrid=False,
                        zeroline=False,
                        tickangle=0
                    ),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1,
                        bgcolor='rgba(255,255,255,0.8)',
                        bordercolor='rgba(0,0,0,0.1)',
                        borderwidth=1
                    ),
                    margin=dict(l=0, r=0, t=40, b=0),
                    showlegend=True,
                    hoverlabel=dict(
                        bgcolor='white',
                        font_size=12,
                        font_family="Arial"
                    )
                )
                
                # 차트 표시
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("📊 최근 7일간의 검사 데이터가 없습니다.")
        else:
            st.info("📊 저장된 검사 데이터가 없습니다.")
    
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
        .applymap(lambda x: color_defect_rate(x) if isinstance(x, (int, float)) and x < 5 else '', subset=['불량률'])\
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
    
    # 검사원 등록 폼
    st.markdown("### 📝 검사원 등록")
    
    with st.form("inspector_form", clear_on_submit=True):
        col1, col2 = st.columns([1,1])
        
        with col1:
            inspector_id = st.text_input("🆔 검사원 ID", 
                                       placeholder="검사원 ID를 입력하세요",
                                       help="예: INS001")
            
            name = st.text_input("👤 이름", 
                               placeholder="이름을 입력하세요")
            
            department = st.selectbox("🏢 소속부서", 
                                    options=["CNC_1", "CNC_2", "CDC", "PQC_LINE"],
                                    key="department_select")
        
        with col2:
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
                    grade = "수석"
                elif months_of_service >= 60:  # 5년 이상
                    grade = "선임"
                else:
                    grade = "사원"
                
                st.markdown(f"""
                    <div style="
                        background-color: rgba(255,255,255,0.1);
                        padding: 0.5rem;
                        border-radius: 4px;
                        margin-top: 0.5rem;
                    ">
                        <span style="color: {
                            '#FFD700' if grade == '수석' else 
                            '#C0C0C0' if grade == '선임' else 
                            '#CD7F32'
                        }; font-weight: bold;">
                            {grade}
                        </span>
                        <span style="color: #666; font-size: 0.9rem; margin-left: 0.5rem;">
                            ({years}년 {months}개월)
                        </span>
                    </div>
                """, unsafe_allow_html=True)
        
        # 저장 버튼
        cols = st.columns([3, 1, 3])
        with cols[1]:
            submitted = st.form_submit_button("💾 저장", type="primary")
        
        if submitted:
            if not inspector_id or not name:
                st.error("⚠️ 필수 항목을 모두 입력해주세요.")
            else:
                # 검사원 데이터 저장
                inspector_data = load_inspector_data()
                new_inspector = {
                    "id": inspector_id,
                    "name": name,
                    "department": department,
                    "months_of_service": months_of_service,
                    "grade": grade if months_of_service > 0 else "사원",
                    "registered_date": datetime.now().strftime("%Y-%m-%d")
                }
                inspector_data["inspectors"].append(new_inspector)
                save_inspector_data(inspector_data)
                
                with st.spinner("저장 중..."):
                    time.sleep(0.5)
                st.success("✅ 검사원 정보가 저장되었습니다!")
                time.sleep(1)
                st.rerun()  # 페이지 새로고침하여 목록 업데이트
    
    # 구분선
    st.markdown("---")
    
    # 검사원 목록 표시
    st.markdown("### 📋 전체 검사원 목록")
    
    # 저장된 검사원 데이터 로드
    inspector_data = load_inspector_data()
    if inspector_data["inspectors"]:
        df = pd.DataFrame(inspector_data["inspectors"])
        
        # 컬럼 이름 한글로 변경
        df = df.rename(columns={
            "id": "검사원 ID",
            "name": "이름",
            "department": "소속부서",
            "months_of_service": "근속개월수",
            "grade": "등급"
        })
        
        # 등급별 스타일 적용
        def style_grade(val):
            if val == '수석':
                return 'background-color: #FFD70020; color: #1F2937; font-weight: 500'
            elif val == '선임':
                return 'background-color: #C0C0C020; color: #1F2937; font-weight: 500'
            return 'background-color: #CD7F3220; color: #374151; font-weight: 500'
        
        # 스타일이 적용된 데이터프레임 생성
        styled_df = df.style\
            .format({'근속개월수': '{:,.0f}개월'})\
            .applymap(style_grade, subset=['등급'])\
            .set_properties(**{
                'font-size': '0.9rem',
                'text-align': 'center',
                'padding': '0.5rem'
            })
        
        # 데이터프레임 표시
        st.dataframe(
            styled_df,
            hide_index=True,
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
    else:
        st.info("👈 등록된 검사원이 없습니다. 왼쪽 폼에서 검사원을 등록해주세요.")

# 일일 성과 입력 페이지
def show_daily_performance():
    st.title("📝 일일 성과 입력")
    
    # 날짜 선택
    date = st.date_input(
        "📅 날짜",
        value=datetime.now(),
        format="YYYY-MM-DD"
    )
    
    # 검사원 정보 입력
    st.markdown("### 👤 검사원 정보")
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        inspector_id = st.text_input(
            "🆔 검사원 ID",
            placeholder="예: INS001",
            help="등록된 검사원 ID를 입력하세요"
        )
    
    with col2:
        inspector_name = st.text_input(
            "👤 검사원 이름",
            placeholder="이름을 입력하세요"
        )
    
    with col3:
        department = st.selectbox(
            "🏢 소속부서",
            options=["CNC_1", "CNC_2", "CDC", "PQC_LINE"]
        )
    
    # 출근 상태 선택
    st.markdown("### 📊 출근 상태")
    attendance_status = st.selectbox(
        "출근 상태 선택",
        options=["출근", "결근"],
        key="attendance_status"
    )
    
    # 결근인 경우 사유 입력
    if attendance_status == "결근":
        absence_reason = st.text_area(
            "결근 사유",
            placeholder="결근 사유를 입력하세요",
            height=100
        )
        
        # 결근 시 저장 버튼
        if st.button("저장", key="absence_save", type="primary"):
            if not inspector_id or not inspector_name:
                st.error("⚠️ 검사원 정보를 모두 입력해주세요.")
            elif not absence_reason:
                st.error("⚠️ 결근 사유를 입력해주세요.")
            else:
                # 결근 데이터 저장
                absence_data = {
                    "날짜": str(date),
                    "검사원ID": inspector_id,
                    "검사원이름": inspector_name,
                    "공정": department,
                    "출근상태": "결근",
                    "결근사유": absence_reason,
                    "검사수량": 0,
                    "불량수량": 0,
                    "작업시간": 0
                }
                
                data = load_inspection_data()
                data["inspections"].append(absence_data)
                save_inspection_data(data)
                
                st.success("✅ 결근 정보가 저장되었습니다.")
                st.rerun()
    
    else:  # 출근인 경우
        # 검사 실적 입력
        st.markdown("### 📈 검사 실적")
        col1, col2 = st.columns(2)
        
        with col1:
            inspection_count = st.number_input(
                "📦 검사 수량",
                min_value=0,
                value=0,
                step=1,
                help="총 검사 수량을 입력하세요"
            )
        
        with col2:
            work_minutes = st.number_input(
                "⏱️ 작업 시간(분)",
                min_value=0,
                max_value=1440,
                value=0,
                step=10,
                help="실제 작업 시간을 분 단위로 입력하세요"
            )
        
        # 불량 정보 입력 (기존 코드 유지)
        st.markdown("### ⚠️ 불량 정보")
        # ... (기존 불량 정보 입력 코드)
        
        # 저장 버튼 (출근 시)
        if st.button("저장", key="attendance_save", type="primary"):
            # ... (기존 저장 로직)
            pass

# 리포트 페이지
def show_report():
    st.title("📊 KPI 리포트")
    
    try:
        # 1. 데이터 로드 및 기본 검증
        data = load_inspection_data()
        if not data.get("inspections"):
            st.warning("⚠️ 저장된 검사 데이터가 없습니다.")
            return
        
        # 2. DataFrame 생성 및 날짜 처리
        df = pd.DataFrame(data["inspections"])
        df['날짜'] = pd.to_datetime(df['날짜'])
        
        # 3. 리포트 유형 선택
        report_type = st.radio(
            "📅 리포트 유형",
            options=["월간 리포트", "주간 리포트"],
            horizontal=True,
            key="report_type"
        )
        
        # 4. 기간 설정
        today = datetime.now()
        
        if report_type == "월간 리포트":
            # 월간 리포트의 경우 년/월만 선택하도록 설정
            col1, col2 = st.columns([1, 3])
            with col1:
                month_options = [f"{today.year}/{m:02d}" for m in range(1, 13)]
                selected_month = st.selectbox(
                    "월 선택",
                    options=month_options,
                    index=today.month - 1,
                    key="month_selector"
                )
                
            year, month = map(int, selected_month.split('/'))
            start_date = datetime(year, month, 1).date()
            if month == 12:
                end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
            period = start_date.strftime("%Y년 %m월")
        else:
            # 주간 리포트의 경우 특정 날짜를 선택하면 해당 주의 월~일 표시
            selected_date = st.date_input(
                "날짜 선택",
                value=today.date(),
                format="YYYY-MM-DD"  # 형식 변경
            )
            start_date = selected_date - timedelta(days=selected_date.weekday())
            end_date = start_date + timedelta(days=6)
            period = f"{start_date.strftime('%Y년 %m월 %d일')} ~ {end_date.strftime('%m월 %d일')}"

        # 5. 데이터 필터링
        mask = (df['날짜'].dt.date >= start_date) & (df['날짜'].dt.date <= end_date)
        period_df = df[mask].copy()
        
        if period_df.empty:
            st.warning(f"⚠️ {period} 기간의 데이터가 없습니다.")
            return

        st.markdown(f"### 📈 {period} 실적 현황")
        
        # 6. KPI 지표 계산
        total_inspections = period_df['검사수량'].astype(float).sum()
        total_defects = period_df['불량수량'].astype(float).sum()
        avg_defect_rate = (total_defects / total_inspections * 100) if total_inspections > 0 else 0
        
        # 효율 계산 (시간당 효율)
        period_df['시간당효율'] = period_df.apply(
            lambda x: (x['검사수량'] / (x['작업시간']/60)) if x['작업시간'] > 0 else 0,  # 쉼표 위치 수정
            axis=1
        )
        avg_efficiency = period_df['시간당효율'].mean()
        avg_efficiency_rate = (avg_efficiency / 200 * 100) if avg_efficiency > 0 else 0  # 목표 200개/시간 기준
        
        inspector_count = period_df['검사원ID'].nunique()
        
        # KPI 지표 표시
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 총 검사량",
                value=f"{int(total_inspections):,}개",
                delta=None
            )
        
        with col2:
            st.metric(
                label="⚠️ 평균 불량률",
                value=f"{avg_defect_rate:.1f}%",
                delta=None
            )
        
        with col3:
            st.metric(
                label="⚡ 평균 효율률",
                value=f"{avg_efficiency_rate:.1f}%",
                delta=None
            )
        
        with col4:
            st.metric(
                label="👥 검사원 수",
                value=f"{inspector_count}명",
                delta=None
            )

        # 차트 데이터 준비
        daily_data = period_df.groupby(period_df['날짜'].dt.date).agg({
            '검사수량': 'sum',
            '불량수량': 'sum',
            '시간당효율': 'mean'  # 효율률 대신 시간당효율 사용
        }).reset_index()
        
        daily_data['불량률'] = (daily_data['불량수량'] / daily_data['검사수량'] * 100).round(2)
        daily_data['효율률'] = (daily_data['시간당효율'] / 200 * 100).round(2)  # 목표 200개/시간 기준
        
        # 차트 생성
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=daily_data['날짜'],
            y=daily_data['검사수량'],
            name='검사량',
            marker_color='rgba(59, 130, 246, 0.7)'
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_data['날짜'],
            y=daily_data['불량률'],
            name='불량률',
            line=dict(color='#EF4444', width=2),
            yaxis='y2'
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_data['날짜'],
            y=daily_data['효율률'],
            name='효율률',
            line=dict(color='#10B981', width=2, dash='dot'),
            yaxis='y2'
        ))
        
        fig.update_layout(
            height=400,
            yaxis=dict(
                title='검사량(개)',
                gridcolor='rgba(0,0,0,0.1)'
            ),
            yaxis2=dict(
                title='비율(%)',
                overlaying='y',
                side='right',
                gridcolor='rgba(0,0,0,0.1)'
            ),
            plot_bgcolor='white',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")

def show_user_management():
    st.title("🔑 사용자 관리")
    
    # 사용자 데이터 로드
    user_data = load_user_data()
    
    # 사용자 목록을 데이터프레임으로 변환
    if user_data["users"]:
        df = pd.DataFrame(user_data["users"])
        st.dataframe(df)
    else:
        st.info("등록된 사용자가 없습니다.")

if __name__ == "__main__":
    main() 