﻿import streamlit as st
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

# Supabase ì´ˆê¸°í™”
try:
    # Supabase ì—°ê²° (ê°€ìž¥ ê¸°ë³¸ì ì¸ í˜•íƒœ)
    # ë§¤ê°œë³€ìˆ˜ë¥¼ ìœ„ì¹˜ ê¸°ë°˜ìœ¼ë¡œë§Œ ì „ë‹¬
    supabase = create_client(
        "https://czfvtkbndsfoznmknwsx.supabase.co",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN6ZnZ0a2JuZHNmb3pubWtud3N4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMxNTE1NDIsImV4cCI6MjA1ODcyNzU0Mn0.IpbN__1zImksnMo22CghSLTA-UCGoI67hHoDkrNpQGE"
    )
except Exception as e:
    st.error(f"ë°ì´í„°ë² ì´ìŠ¤ ì—°ê²°ì— ì‹¤íŒ¨í–ˆìŠµë‹ˆë‹¤: {str(e)}")
    st.stop()

# íŽ˜ì´ì§€ ì„¤ì •
st.set_page_config(
    page_title="CNC í’ˆì§ˆê´€ë¦¬ ì‹œìŠ¤í…œ", 
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/leejungyong83/CNC_QC_KPI',
        'Report a bug': 'https://github.com/leejungyong83/CNC_QC_KPI/issues',
        'About': '# CNC í’ˆì§ˆê´€ë¦¬ ì‹œìŠ¤í…œ\n í’ˆì§ˆ ë°ì´í„° ìˆ˜ì§‘ ë° ë¶„ì„ì„ ìœ„í•œ ì•±ìž…ë‹ˆë‹¤.'
    }
)

# ì¹´ë“œ ìŠ¤íƒ€ì¼ CSS ì¶”ê°€
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
    /* ê° ì§€í‘œë³„ ìƒ‰ìƒ */
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

# ë°ì´í„° íŒŒì¼ ê²½ë¡œ ì„¤ì •
if 'data_path' in st.secrets.get('database', {}):
    DATA_DIR = Path(st.secrets['database']['data_path'])
else:
    DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ë°ì´í„° íŒŒì¼ ê²½ë¡œ
INSPECTION_DATA_FILE = DATA_DIR / "inspection_data.json"
INSPECTOR_DATA_FILE = DATA_DIR / "inspector_data.json"
DEFECT_DATA_FILE = DATA_DIR / "defect_data.json"
ADMIN_DATA_FILE = DATA_DIR / "admin_data.json"
USER_DATA_FILE = DATA_DIR / "user_data.json"

def load_admin_data():
    """ê´€ë¦¬ìž ë°ì´í„° íŒŒì¼ì—ì„œ ë¡œë“œí•˜ëŠ” í•¨ìˆ˜"""
    try:
        with open(ADMIN_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # íŒŒì¼ì´ ì—†ê±°ë‚˜ ë‚´ìš©ì´ ì—†ì„ ê²½ìš° ê¸°ë³¸ êµ¬ì¡° ë°˜í™˜
        return {
            "ì•„ì´ë””": [],
            "ì´ë¦„": [],
            "ê¶Œí•œ": [],
            "ë¶€ì„œ": [],
            "ìµœê·¼ì ‘ì†ì¼": [],
            "ìƒíƒœ": []
        }

def save_admin_data(admin_data):
    """ê´€ë¦¬ìž ë°ì´í„°ë¥¼ íŒŒì¼ì— ì €ìž¥í•˜ëŠ” í•¨ìˆ˜"""
    # ë””ë ‰í† ë¦¬ê°€ ì—†ìœ¼ë©´ ìƒì„±
    os.makedirs(DATA_DIR, exist_ok=True)
    
    with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(admin_data, f, ensure_ascii=False, indent=2)

def load_user_data():
    """ì‚¬ìš©ìž ë°ì´í„° íŒŒì¼ì—ì„œ ë¡œë“œí•˜ëŠ” í•¨ìˆ˜"""
    try:
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
            
            # ìƒˆë¡œìš´ í˜•ì‹ê³¼ ê¸°ì¡´ í˜•ì‹ ëª¨ë‘ ì²˜ë¦¬
            if isinstance(raw_data, dict) and "users" in raw_data:
                # ê¸°ì¡´ í˜•ì‹: {"users": [{"email": "...", "name": "...", ...}, ...]}
                users_list = raw_data["users"]
                data = {
                    "ì•„ì´ë””": [],
                    "ì´ë¦„": [],
                    "ë¶€ì„œ": [],
                    "ì§ê¸‰": [],
                    "ê³µì •": [],
                    "ê³„ì •ìƒì„±ì¼": [],
                    "ìµœê·¼ì ‘ì†ì¼": [],
                    "ìƒíƒœ": []
                }
                
                for user in users_list:
                    data["ì•„ì´ë””"].append(user.get("email", ""))
                    data["ì´ë¦„"].append(user.get("name", ""))
                    data["ë¶€ì„œ"].append("ê´€ë¦¬ë¶€")  # ê¸°ë³¸ê°’
                    data["ì§ê¸‰"].append("ì‚¬ì›")    # ê¸°ë³¸ê°’
                    data["ê³µì •"].append("ê´€ë¦¬")    # ê¸°ë³¸ê°’
                    data["ê³„ì •ìƒì„±ì¼"].append(user.get("registered_date", ""))
                    data["ìµœê·¼ì ‘ì†ì¼"].append(user.get("last_login", ""))
                    data["ìƒíƒœ"].append("í™œì„±")    # ê¸°ë³¸ê°’
                
                return data
            elif isinstance(raw_data, dict):
                # ëˆ„ë½ëœ í‚¤ê°€ ìžˆëŠ”ì§€ í™•ì¸í•˜ê³  í•„ìš”í•˜ë©´ ì´ˆê¸°í™”
                required_keys = ["ì•„ì´ë””", "ì´ë¦„", "ë¶€ì„œ", "ì§ê¸‰", "ê³µì •", "ê³„ì •ìƒì„±ì¼", "ìµœê·¼ì ‘ì†ì¼", "ìƒíƒœ"]
                for key in required_keys:
                    if key not in raw_data:
                        raw_data[key] = []
                return raw_data
            else:
                return {
                    "ì•„ì´ë””": [],
                    "ì´ë¦„": [],
                    "ë¶€ì„œ": [],
                    "ì§ê¸‰": [],
                    "ê³µì •": [],
                    "ê³„ì •ìƒì„±ì¼": [],
                    "ìµœê·¼ì ‘ì†ì¼": [],
                    "ìƒíƒœ": []
                }
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "ì•„ì´ë””": [],
            "ì´ë¦„": [],
            "ë¶€ì„œ": [],
            "ì§ê¸‰": [],
            "ê³µì •": [],
            "ê³„ì •ìƒì„±ì¼": [],
            "ìµœê·¼ì ‘ì†ì¼": [],
            "ìƒíƒœ": []
        }

def save_user_data(user_data):
    """ì‚¬ìš©ìž ë°ì´í„°ë¥¼ íŒŒì¼ì— ì €ìž¥í•˜ëŠ” í•¨ìˆ˜"""
    # ë””ë ‰í† ë¦¬ê°€ ì—†ìœ¼ë©´ ìƒì„±
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # ì˜¬ë°”ë¥¸ í‚¤ê°€ ìžˆëŠ”ì§€ í™•ì¸
    required_keys = ["ì•„ì´ë””", "ì´ë¦„", "ë¶€ì„œ", "ì§ê¸‰", "ê³µì •", "ê³„ì •ìƒì„±ì¼", "ìµœê·¼ì ‘ì†ì¼", "ìƒíƒœ"]
    for key in required_keys:
        if key not in user_data:
            user_data[key] = []
    
    # ë°ì´í„° ì €ìž¥ - ì´ í˜•ì‹ì€ load_user_data()ì™€ ì¼ê´€ë˜ì–´ì•¼ í•¨
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(user_data, f, ensure_ascii=False, indent=2)

def init_db():
    """JSON íŒŒì¼ ê¸°ë°˜ ë°ì´í„°ë² ì´ìŠ¤ ì´ˆê¸°í™”"""
    try:
        # ë””ë ‰í† ë¦¬ê°€ ì—†ìœ¼ë©´ ìƒì„±
        os.makedirs(DATA_DIR, exist_ok=True)
        
        # ê²€ì‚¬ì› ë°ì´í„° ì´ˆê¸°í™”
        if not INSPECTOR_DATA_FILE.exists():
            with open(INSPECTOR_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"inspectors": []}, f, ensure_ascii=False, indent=2)
        
        # ê²€ì‚¬ ë°ì´í„° ì´ˆê¸°í™”
        if not INSPECTION_DATA_FILE.exists():
            with open(INSPECTION_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"inspections": []}, f, ensure_ascii=False, indent=2)
        
        # ë¶ˆëŸ‰ ë°ì´í„° ì´ˆê¸°í™”
        if not DEFECT_DATA_FILE.exists():
            with open(DEFECT_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"defects": []}, f, ensure_ascii=False, indent=2)
        
        # ìƒì‚°ëª¨ë¸ ë°ì´í„° ì´ˆê¸°í™” - ê¸°ì¡´ ë°ì´í„° ë³´ì¡´
        if not (DATA_DIR / "product_models.json").exists():
            # ìƒ˜í”Œ ëª¨ë¸ ë°ì´í„°
            default_models = {
                "models": [
                    {"id": 1, "ëª¨ë¸ëª…": "PA1", "ê³µì •": "C1"},
                    {"id": 2, "ëª¨ë¸ëª…": "PA1", "ê³µì •": "C2"},
                    {"id": 3, "ëª¨ë¸ëª…": "PA2", "ê³µì •": "C1"},
                    {"id": 4, "ëª¨ë¸ëª…": "PA2", "ê³µì •": "C2"},
                    {"id": 5, "ëª¨ë¸ëª…": "PA3", "ê³µì •": "C1"},
                    {"id": 6, "ëª¨ë¸ëª…": "PA3", "ê³µì •": "C2"},
                    {"id": 7, "ëª¨ë¸ëª…": "PA3", "ê³µì •": "C2-1"},
                    {"id": 8, "ëª¨ë¸ëª…": "B6", "ê³µì •": "C1"},
                    {"id": 9, "ëª¨ë¸ëª…": "B6", "ê³µì •": "C2"},
                    {"id": 10, "ëª¨ë¸ëª…": "B6M", "ê³µì •": "C1"}
                ]
            }
            with open(DATA_DIR / "product_models.json", 'w', encoding='utf-8') as f:
                json.dump(default_models, f, ensure_ascii=False, indent=2)
        
        # ê´€ë¦¬ìž ë°ì´í„° ì´ˆê¸°í™” - ê¸°ì¡´ ë°ì´í„° ë³´ì¡´
        if not ADMIN_DATA_FILE.exists():
            default_admin_data = {
                "ì•„ì´ë””": ["admin"],
                "ì´ë¦„": ["ê´€ë¦¬ìž"],
                "ê¶Œí•œ": ["ê´€ë¦¬ìž"],
                "ë¶€ì„œ": ["ê´€ë¦¬ë¶€"],
                "ìµœê·¼ì ‘ì†ì¼": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "ìƒíƒœ": ["í™œì„±"]
            }
            with open(ADMIN_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_admin_data, f, ensure_ascii=False, indent=2)
        
        # ì‚¬ìš©ìž ë°ì´í„° ì´ˆê¸°í™” - ê¸°ì¡´ ë°ì´í„° ë³´ì¡´
        if not USER_DATA_FILE.exists():
            default_user_data = {
                "ì•„ì´ë””": [],
                "ì´ë¦„": [],
                "ë¶€ì„œ": [],
                "ì§ê¸‰": [],
                "ê³µì •": [],
                "ê³„ì •ìƒì„±ì¼": [],
                "ìµœê·¼ì ‘ì†ì¼": [],
                "ìƒíƒœ": []
            }
            with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_user_data, f, ensure_ascii=False, indent=2)
        
        print("ë°ì´í„°ë² ì´ìŠ¤ ì´ˆê¸°í™” ì™„ë£Œ!")
    except Exception as e:
        print(f"ë°ì´í„°ë² ì´ìŠ¤ ì´ˆê¸°í™” ì¤‘ ì˜¤ë¥˜ ë°œìƒ: {str(e)}")
        import traceback
        traceback.print_exc()

# ì•± ì‹œìž‘ ì‹œ ë°ì´í„°ë² ì´ìŠ¤ ì´ˆê¸°í™”
init_db()

def init_session_state():
    """ì„¸ì…˜ ìƒíƒœ ì´ˆê¸°í™”"""
    if 'page' not in st.session_state:
        st.session_state.page = 'login'
    
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if 'username' not in st.session_state:
        st.session_state.username = ""
    
    if 'user_role' not in st.session_state:
        st.session_state.user_role = "ì¼ë°˜"
    
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
            "ì™¸ê´€ë¶ˆëŸ‰", "ì¹˜ìˆ˜ë¶ˆëŸ‰", "ê¸°ëŠ¥ë¶ˆëŸ‰", "ëˆ„ë½ë¶ˆëŸ‰", "ë¼ë²¨ë¶ˆëŸ‰",
            "í¬ìž¥ë¶ˆëŸ‰", "ì¼€ì´ë¸”ë¶ˆëŸ‰", "ì¡°ë¦½ë¶ˆëŸ‰", "ê¸°íƒ€ë¶ˆëŸ‰"
        ]
    
    if 'basic_info_valid' not in st.session_state:
        st.session_state.basic_info_valid = False
    
    if 'registered_defects' not in st.session_state:
        st.session_state.registered_defects = []

# ì„¸ì…˜ ìƒíƒœ ì´ˆê¸°í™” ì‹¤í–‰
init_session_state()

# ì•±ì´ ìž ìžê¸° ëª¨ë“œë¡œ ë“¤ì–´ê°€ì§€ ì•Šë„ë¡ í•˜ëŠ” í•¨ìˆ˜
def prevent_sleep():
    # ë°±ê·¸ë¼ìš´ë“œ ë¡œê¹… - ìŠ¤ë ˆë”© ì‚¬ìš©í•˜ì§€ ì•ŠìŒ
    print("ì•± í™œì„± ìƒíƒœ ìœ ì§€ ëª¨ë“œ í™œì„±í™”")

# ì„¸ì…˜ ìœ ì§€ë¥¼ ìœ„í•œ ìˆ¨ê²¨ì§„ ìš”ì†Œ ì¶”ê°€
def add_keep_alive_element():
    # íƒ€ìž„ìŠ¤íƒ¬í”„ í‘œì‹œ (ìž‘ê²Œ í‘œì‹œ)
    current_time = datetime.now().strftime("%H:%M:%S")
    st.sidebar.markdown(f"<small>ì„¸ì…˜ í™œì„± ìƒíƒœ: {current_time}</small>", unsafe_allow_html=True)

# ì•± ì‹œìž‘ ì‹œ prevent_sleep í•¨ìˆ˜ í˜¸ì¶œ
prevent_sleep()

def verify_login(username, password):
    """ë¡œê·¸ì¸ ê²€ì¦"""
    # í•˜ë“œì½”ë”©ëœ ì‚¬ìš©ìž ì •ë³´ë¡œ ë¨¼ì € í™•ì¸
    if username == "admin" and password == "admin123":
        return True, "ê´€ë¦¬ìž"
        
    try:
        # ê¸°ë³¸ ì‚¬ìš©ìž ì •ë³´
        default_users = {"admin": "admin123"}
        default_roles = {"admin": "ê´€ë¦¬ìž"}
        
        # Streamlit Cloudì˜ secretsì—ì„œ ì‚¬ìš©ìž ì •ë³´ ê°€ì ¸ì˜¤ê¸°
        try:
            users = st.secrets.get("users", default_users)
            roles = st.secrets.get("roles", default_roles)
        except:
            users = default_users
            roles = default_roles
            
        if username in users:
            if password == users[username]:
                user_role = roles.get(username, "ì¼ë°˜")
                return True, user_role
        return False, None
    except Exception as e:
        st.error(f"ë¡œê·¸ì¸ ê²€ì¦ ì¤‘ ì˜¤ë¥˜ ë°œìƒ: {str(e)}")
        return False, None

def check_password():
    """ë¹„ë°€ë²ˆí˜¸ í™•ì¸ ë° ë¡œê·¸ì¸ ì²˜ë¦¬"""
    # ì´ë¯¸ ë¡œê·¸ì¸ë˜ì–´ ìžˆë‹¤ë©´ ë°”ë¡œ ì„±ê³µ ë°˜í™˜
    if st.session_state.get('logged_in', False):
        return True
        
    # ì„¸ì…˜ ìœ ì§€ë¥¼ ìœ„í•œ ìš”ì†Œ ì¶”ê°€
    add_keep_alive_element()
    
    # ë””ë²„ê·¸ ëª¨ë“œ - ê°œë°œ í™˜ê²½ì—ì„œë§Œ ì‚¬ìš© (í”„ë¡œë•ì…˜ì—ì„œëŠ” ì œê±° í•„ìš”)
    if st.sidebar.button("ë””ë²„ê·¸ ëª¨ë“œë¡œ ë¡œê·¸ì¸"):
        # ë¡œê·¸ì¸ ì„±ê³µ ìƒíƒœ ì„¤ì •
        st.session_state.logged_in = True
        st.session_state.user_role = "ê´€ë¦¬ìž"
        st.session_state.username = "admin_debug"
        st.session_state.login_attempts = 0
        st.session_state.page = "dashboard"
        # íŽ˜ì´ì§€ ìƒˆë¡œê³ ì¹¨
        st.rerun()
        return True
    
    # ë¡œê·¸ì¸ ì‹œë„ íšŸìˆ˜ í™•ì¸
    login_attempts = st.session_state.get('login_attempts', 0)
    if login_attempts >= 3:
        st.error("ë¡œê·¸ì¸ ì‹œë„ íšŸìˆ˜ë¥¼ ì´ˆê³¼í–ˆìŠµë‹ˆë‹¤. ìž ì‹œ í›„ ë‹¤ì‹œ ì‹œë„í•´ì£¼ì„¸ìš”.")
        st.session_state.login_attempts = 0  # ì œí•œ ì‹œê°„ í›„ ë¦¬ì…‹
        return False

    # ë¡œê·¸ì¸ UI
    st.title("CNC í’ˆì§ˆê´€ë¦¬ ì‹œìŠ¤í…œ")
    st.subheader("ë¡œê·¸ì¸")
    
    # ë¡œê·¸ì¸ ìž…ë ¥ í•„ë“œ
    username = st.text_input("ì•„ì´ë””", key="login_username")
    password = st.text_input("ë¹„ë°€ë²ˆí˜¸", type="password", key="login_password")
    login_button = st.button("ë¡œê·¸ì¸", key="login_button")
    
    if login_button:
        if not username:
            st.error("ì•„ì´ë””ë¥¼ ìž…ë ¥í•˜ì„¸ìš”.")
            return False
        if not password:
            st.error("ë¹„ë°€ë²ˆí˜¸ë¥¼ ìž…ë ¥í•˜ì„¸ìš”.")
            return False

        success, user_role = verify_login(username, password)
        if success:
            # ë¡œê·¸ì¸ ì„±ê³µ ìƒíƒœ ì„¤ì •
            st.session_state.logged_in = True
            st.session_state.user_role = user_role
            st.session_state.username = username
            st.session_state.login_attempts = 0
            st.session_state.page = "dashboard"
            st.success(f"{username}ë‹˜ í™˜ì˜í•©ë‹ˆë‹¤!")
            time.sleep(1)  # 1ì´ˆ í›„ ë¦¬ë¡œë“œ
            st.rerun()
            return True
        else:
            # ë¡œê·¸ì¸ ì‹¤íŒ¨ ì²˜ë¦¬
            st.session_state.login_attempts = login_attempts + 1
            st.error("ì•„ì´ë”” ë˜ëŠ” ë¹„ë°€ë²ˆí˜¸ê°€ ì˜¬ë°”ë¥´ì§€ ì•ŠìŠµë‹ˆë‹¤.")
            if st.session_state.login_attempts >= 3:
                st.warning("ë¡œê·¸ì¸ì„ 3íšŒ ì´ìƒ ì‹¤íŒ¨í–ˆìŠµë‹ˆë‹¤. ê³„ì • ì •ë³´ë¥¼ í™•ì¸í•˜ì„¸ìš”.")
            return False

    return False

# ë¡œê·¸ì¸ ìƒíƒœ í™•ì¸ ë° íŽ˜ì´ì§€ í‘œì‹œ
if not check_password():
    # ë¡œê·¸ì¸ ì‹¤íŒ¨ ì‹œ ì—¬ê¸°ì„œ ë©ˆì¶¤
    st.stop()

# ì—¬ê¸°ì„œë¶€í„° ë¡œê·¸ì¸ ì„±ê³µ í›„ í‘œì‹œë˜ëŠ” ë‚´ìš©
st.sidebar.success(f"{st.session_state.username}ë‹˜ í™˜ì˜í•©ë‹ˆë‹¤!")
st.sidebar.write(f"ì—­í• : {st.session_state.user_role}")

# ì„¸ì…˜ ìœ ì§€ë¥¼ ìœ„í•œ ìš”ì†Œ ì¶”ê°€
add_keep_alive_element()

# ë¡œê·¸ì•„ì›ƒ ë²„íŠ¼
if st.sidebar.button("ë¡œê·¸ì•„ì›ƒ"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = "ì¼ë°˜"
    st.session_state.page = "login"
    st.rerun()

# ì–¸ì–´ ì„ íƒ (í•œêµ­ì–´/ë² íŠ¸ë‚¨ì–´)
TRANSLATIONS = {
    "ko": {
        "title": "ALMUS TECH CNC ìž‘ì—…ìž KPI ê´€ë¦¬ ì‹œìŠ¤í…œ",
        "menu_groups": {
            "admin": "ê´€ë¦¬ìž ë©”ë‰´",
            "report": "ë¦¬í¬íŠ¸ ë©”ë‰´"
        },
        "admin_menu": {
            "manager_auth": "ðŸ‘¥ ê´€ë¦¬ìž ë° ì‚¬ìš©ìž ê´€ë¦¬",
            "process_auth": "âš™ï¸ ê´€ë¦¬ìž ë“±ë¡ ë° ê´€ë¦¬",
            "user_auth": "ðŸ”‘ ê²€ì‚¬ìž ë“±ë¡ ë° ê´€ë¦¬",
            "inspection_data": "ðŸ“Š ê²€ì‚¬ì‹¤ì  ê´€ë¦¬",
            "product_model": "ðŸ“¦ ìƒì‚°ëª¨ë¸ ê´€ë¦¬"
        },
        "report_menu": {
            "total_dashboard": "ðŸ“ˆ ì¢…í•© ëŒ€ì‹œë³´ë“œ",
            "daily_report": "ðŸ“Š ì¼ê°„ ë¦¬í¬íŠ¸",
            "weekly_report": "ðŸ“… ì£¼ê°„ ë¦¬í¬íŠ¸",
            "monthly_report": "ðŸ“† ì›”ê°„ ë¦¬í¬íŠ¸",
            "quality_report": "â­ ì›”ê°„ í’ˆì§ˆ ë¦¬í¬íŠ¸"
        }
    },
    "vi": {
        "title": "Há»‡ thá»‘ng quáº£n lÃ½ KPI cho cÃ´ng nhÃ¢n CNC ALMUS TECH",
        "menu_groups": {
            "admin": "Menu quáº£n trá»‹",
            "report": "Menu bÃ¡o cÃ¡o"
        },
        "admin_menu": {
            "manager_auth": "ðŸ‘¥ Quáº£n lÃ½ quáº£n trá»‹ viÃªn vÃ  ngÆ°á»i dÃ¹ng",
            "process_auth": "âš™ï¸ ÄÄƒng kÃ½ vÃ  quáº£n lÃ½ quáº£n trá»‹ viÃªn",
            "user_auth": "ðŸ”‘ ÄÄƒng kÃ½ vÃ  quáº£n lÃ½ ngÆ°á»i dÃ¹ng",
            "inspection_data": "ðŸ“Š Quáº£n lÃ½ dá»¯ liá»‡u kiá»ƒm tra",
            "product_model": "ðŸ“¦ Quáº£n lÃ½ mÃ´ hÃ¬nh sáº£n xuáº¥t"
        },
        "report_menu": {
            "total_dashboard": "ðŸ“ˆ Báº£ng Ä‘iá»u khiá»ƒn tá»•ng há»£p",
            "daily_report": "ðŸ“Š BÃ¡o cÃ¡o hÃ ng ngÃ y",
            "weekly_report": "ðŸ“… BÃ¡o cÃ¡o hÃ ng tuáº§n",
            "monthly_report": "ðŸ“† BÃ¡o cÃ¡o hÃ ng thÃ¡ng",
            "quality_report": "â­ BÃ¡o cÃ¡o cháº¥t lÆ°á»£ng hÃ ng thÃ¡ng"
        }
    }
}

# ì´ˆê¸° ì–¸ì–´ ì„¤ì •
if 'language' not in st.session_state:
    st.session_state.language = 'ko'

# ì‚¬ì´ë“œë°”ì— ì–¸ì–´ ì„ íƒ ì¶”ê°€
lang_col1, lang_col2 = st.sidebar.columns(2)
with lang_col1:
    if st.button("í•œêµ­ì–´", key="ko_btn"):
        st.session_state.language = 'ko'
        st.rerun()
with lang_col2:
    if st.button("Tiáº¿ng Viá»‡t", key="vi_btn"):
        st.session_state.language = 'vi'
        st.rerun()

# í˜„ìž¬ ì„ íƒëœ ì–¸ì–´ì˜ ë²ˆì—­ ê°€ì ¸ì˜¤ê¸°
curr_lang = TRANSLATIONS[st.session_state.language]

# ë©”ë‰´ íŽ˜ì´ì§€ ì •ì˜
if 'page' not in st.session_state:
    st.session_state.page = "total_dashboard"

# ê´€ë¦¬ìž ë©”ë‰´ ì„¹ì…˜
st.sidebar.markdown(f"### {curr_lang['menu_groups']['admin']}")
admin_menu = curr_lang['admin_menu']
selected_admin = st.sidebar.radio(
    label="",
    options=list(admin_menu.keys()),
    format_func=lambda x: admin_menu[x],
    key="admin_menu", 
    index=0
)

# ë¦¬í¬íŠ¸ ë©”ë‰´ ì„¹ì…˜
st.sidebar.markdown(f"### {curr_lang['menu_groups']['report']}")
report_menu = curr_lang['report_menu']
selected_report = st.sidebar.radio(
    label="",
    options=list(report_menu.keys()),
    format_func=lambda x: report_menu[x],
    key="report_menu",
    index=0
)

# ì„ íƒëœ ë©”ë‰´ì— ë”°ë¼ íŽ˜ì´ì§€ ìƒíƒœ ì—…ë°ì´íŠ¸
if selected_admin in admin_menu:
    st.session_state.page = selected_admin
elif selected_report in report_menu:
    st.session_state.page = selected_report

# ê²€ì‚¬ì› ì •ë³´ ê°€ì ¸ì˜¤ê¸°
def load_inspectors():
    try:
        response = supabase.table('inspectors').select("*").execute()
        if response.data:
            return pd.DataFrame(response.data)
        else:
            # ìƒ˜í”Œ ë°ì´í„° ë°˜í™˜
            default_inspectors = [
                {"id": "INS001", "name": "í™ê¸¸ë™", "department": "CNC_1", "process": "ì„ ì‚­", "years_of_service": 5.5},
                {"id": "INS002", "name": "ê¹€ì² ìˆ˜", "department": "CNC_2", "process": "ë°€ë§", "years_of_service": 3.2},
                {"id": "INS003", "name": "ì´ì˜í¬", "department": "PQC_LINE", "process": "ê²€ì‚¬", "years_of_service": 7.1}
            ]
            return pd.DataFrame(default_inspectors)
    except Exception as e:
        # ì˜¤ë¥˜ ë°œìƒ ì‹œ ê¸°ë³¸ ë°ì´í„° ë°˜í™˜
        st.error(f"ê²€ì‚¬ì› ì •ë³´ ë¡œë”© ì¤‘ ì˜¤ë¥˜: {str(e)}")
        default_inspectors = [
            {"id": "INS001", "name": "í™ê¸¸ë™", "department": "CNC_1"},
            {"id": "INS002", "name": "ê¹€ì² ìˆ˜", "department": "CNC_2"},
            {"id": "INS003", "name": "ì´ì˜í¬", "department": "PQC_LINE"}
        ]
        return pd.DataFrame(default_inspectors)

# ê²€ì‚¬ ë°ì´í„° ì €ìž¥
def save_inspection_data(data):
    try:
        # í•œê¸€ í•„ë“œëª…ì„ ì˜ë¬¸ìœ¼ë¡œ ë³€í™˜
        field_mapping = {
            "ê²€ì‚¬ì›": "inspector_name",
            "ê³µì •": "process",
            "ëª¨ë¸ëª…": "model_name",
            "ê²€ì‚¬ì¼ìž": "inspection_date",
            "ê²€ì‚¬ì‹œê°„": "inspection_time",
            "LOTë²ˆí˜¸": "lot_number",
            "ìž‘ì—…ì‹œê°„(ë¶„)": "work_time_minutes",
            "ê³„íšìˆ˜ëŸ‰": "planned_quantity",
            "ê²€ì‚¬ìˆ˜ëŸ‰": "total_inspected",
            "ë¶ˆëŸ‰ìˆ˜ëŸ‰": "total_defects",
            "ë¶ˆëŸ‰ë¥ (%)": "defect_rate",
            "ë¹„ê³ ": "remarks"
        }
        
        # ë°ì´í„° ë³€í™˜
        english_data = {}
        for k, v in data.items():
            if k in field_mapping:
                english_data[field_mapping[k]] = v
            else:
                english_data[k] = v
        
        # ì˜ë¬¸ í•„ë“œëª…ìœ¼ë¡œ ì €ìž¥
        response = supabase.table('inspection_data').insert(english_data).execute()
        return response
    except Exception as e:
        # Supabase í…Œì´ë¸”ì´ ì—†ëŠ” ê²½ìš°ë‚˜ ë‹¤ë¥¸ ì˜¤ë¥˜ ì²˜ë¦¬
        st.error(f"ë°ì´í„° ì €ìž¥ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
        # ì„¸ì…˜ì— ë°ì´í„° ì €ìž¥(ë°±ì—…)
        if 'saved_inspections' not in st.session_state:
            st.session_state.saved_inspections = []
        st.session_state.saved_inspections.append(data)
        raise e

# ë¶ˆëŸ‰ ë°ì´í„° ì €ìž¥
def save_defect_data(data):
    try:
        # í•œê¸€ í•„ë“œëª…ì„ ì˜ë¬¸ìœ¼ë¡œ ë³€í™˜
        field_mapping = {
            "ë¶ˆëŸ‰ìœ í˜•": "defect_type",
            "ìˆ˜ëŸ‰": "quantity",
            "ê²€ì‚¬ID": "inspection_id",
            "ë“±ë¡ì¼ìž": "registration_date",
            "ë“±ë¡ìž": "registered_by",
            "ë¹„ê³ ": "remarks"
        }
        
        # ë°ì´í„° ë³€í™˜
        english_data = {}
        for k, v in data.items():
            if k in field_mapping:
                english_data[field_mapping[k]] = v
            else:
                english_data[k] = v
        
        # ì˜ë¬¸ í•„ë“œëª…ìœ¼ë¡œ ì €ìž¥
        response = supabase.table('defect_data').insert(english_data).execute()
        return response
    except Exception as e:
        # Supabase í…Œì´ë¸”ì´ ì—†ëŠ” ê²½ìš°ë‚˜ ë‹¤ë¥¸ ì˜¤ë¥˜ ì²˜ë¦¬
        st.error(f"ë¶ˆëŸ‰ ë°ì´í„° ì €ìž¥ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
        # ì„¸ì…˜ì— ë°ì´í„° ì €ìž¥(ë°±ì—…)
        if 'saved_defects' not in st.session_state:
            st.session_state.saved_defects = []
        st.session_state.saved_defects.append(data)
        raise e

# ì„¸ì…˜ ìƒíƒœ ì´ˆê¸°í™” (ì•± ìµœì´ˆ ë¡œë“œ ì‹œ í•œ ë²ˆë§Œ ì‹¤í–‰)
if 'inspectors' not in st.session_state:
    st.session_state.inspectors = load_inspectors()

if 'registered_defects' not in st.session_state:
    st.session_state.registered_defects = []

# í˜„ìž¬ íŽ˜ì´ì§€ì— ë”°ë¼ ë‹¤ë¥¸ ë‚´ìš© í‘œì‹œ
if st.session_state.page == "total_dashboard":
    # ìƒë‹¨ í—¤ë” ì„¹ì…˜
    st.markdown("<div class='title-area'><h1>ðŸ­ CNC í’ˆì§ˆê´€ë¦¬ ì‹œìŠ¤í…œ - ëŒ€ì‹œë³´ë“œ</h1></div>", unsafe_allow_html=True)
    
    # ìƒë‹¨ ë©”íŠ¸ë¦­ ì„¹ì…˜ (2x2 ê·¸ë¦¬ë“œ)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("ðŸ“ ì´ ê²€ì‚¬ ê±´ìˆ˜", "152", "+12")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("âš ï¸ í‰ê·  ë¶ˆëŸ‰ë¥ ", "0.8%", "-0.2%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("ðŸ” ìµœë‹¤ ë¶ˆëŸ‰ ìœ í˜•", "ì¹˜ìˆ˜ë¶ˆëŸ‰", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("âš™ï¸ ì§„í–‰ ì¤‘ì¸ ìž‘ì—…", "3", "+1")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ë‚ ì§œ í•„í„° (ë©”íŠ¸ë¦­ ì¹´ë“œ ì•„ëž˜ì— í†µí•©)
    col1, col2 = st.columns([1, 1])
    with col1:
        start_date = st.date_input("ðŸ“… ì‹œìž‘ì¼", datetime.now() - timedelta(days=30))
    with col2:
        end_date = st.date_input("ðŸ“… ì¢…ë£Œì¼", datetime.now())
    
    # ì°¨íŠ¸ ì„¹ì…˜ (2x1 ê·¸ë¦¬ë“œ)
    col1, col2 = st.columns(2)
    
    with col1:
        # ì¼ë³„ ë¶ˆëŸ‰ë¥  ì¶”ì´ ì°¨íŠ¸
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>ðŸ“Š ì¼ë³„ ë¶ˆëŸ‰ë¥  ì¶”ì´ (ìµœê·¼ 7ì¼)</div>", unsafe_allow_html=True)
        
        # ì¼ì£¼ì¼ ë°ì´í„° ì¤€ë¹„ (í˜„ìž¬ ë‚ ì§œë¶€í„° 7ì¼ ì „ê¹Œì§€)
        last_week = pd.date_range(end=datetime.now(), periods=7)
        weekdays = [d.strftime("%a") for d in last_week]  # ìš”ì¼ ì•½ìž (ì›”,í™”,ìˆ˜...)
        dates_str = [d.strftime("%m/%d") for d in last_week]  # ë‚ ì§œ í˜•ì‹ (ì›”/ì¼)
        
        # ë‚ ì§œì™€ ìš”ì¼ ê²°í•©
        x_labels = [f"{d} ({w})" for d, w in zip(dates_str, weekdays)]
        
        # ë°€ë§ ë°ì´í„° (ë§‰ëŒ€ ê·¸ëž˜í”„)
        milling_data = np.random.rand(7) * 1.5
        # ì„ ì‚­ ë°ì´í„° (ë¼ì¸ ì°¨íŠ¸)
        turning_data = np.random.rand(7) * 2
        
        # ë³µí•© ê·¸ëž˜í”„ ìƒì„±
        fig = go.Figure()
        
        # ë°€ë§ ê³µì • (ë§‰ëŒ€ ê·¸ëž˜í”„)
        fig.add_trace(go.Bar(
            x=x_labels,
            y=milling_data,
            name="ë°€ë§",
            marker_color="#4361ee",
            opacity=0.7
        ))
        
        # ì„ ì‚­ ê³µì • (ì„  ê·¸ëž˜í”„)
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=turning_data,
            mode='lines+markers',
            name='ì„ ì‚­',
            line=dict(color='#fb8c00', width=3),
            marker=dict(size=8)
        ))
        
        # í‰ê·  ë¶ˆëŸ‰ë¥  (ì ì„ )
        avg_defect = np.mean(np.concatenate([milling_data, turning_data]))
        fig.add_trace(go.Scatter(
            x=x_labels,
            y=[avg_defect] * 7,
            mode='lines',
            name='í‰ê· ',
            line=dict(color='#4cb782', width=2, dash='dash'),
        ))
        
        # ë ˆì´ì•„ì›ƒ ì—…ë°ì´íŠ¸
        fig.update_layout(
            title=None,
            margin=dict(l=20, r=20, t=10, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False,
                title="ë‚ ì§œ (ìš”ì¼)",
                tickangle=-30,
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor="rgba(0,0,0,0.05)",
                title="ë¶ˆëŸ‰ë¥  (%)"
            ),
            hovermode="x unified",
            barmode='group'
        )
        
        # ë¶ˆëŸ‰ë¥  ëª©í‘œì„  (ì˜ˆ: 1%)
        target_rate = 1.0
        fig.add_shape(
            type="line",
            x0=x_labels[0],
            y0=target_rate,
            x1=x_labels[-1],
            y1=target_rate,
            line=dict(color="red", width=1, dash="dot"),
        )
        
        # ëª©í‘œì„  ì£¼ì„ ì¶”ê°€
        fig.add_annotation(
            x=x_labels[1],
            y=target_rate,
            text="ëª©í‘œì„  (1%)",
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
        # ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬ ì°¨íŠ¸
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>ðŸ© ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬</div>", unsafe_allow_html=True)
        
        # ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬
        defect_types = ["ì¹˜ìˆ˜ ë¶ˆëŸ‰", "í‘œë©´ ê±°ì¹ ê¸°", "ì¹©í•‘", "ê¸°íƒ€"]
        defect_counts = np.random.randint(5, 30, size=len(defect_types))
        
        # ë„ë„› ì°¨íŠ¸ì— ì•„ì´ì½˜ ì§€ì • (ì´ëª¨í‹°ì½˜)
        defect_icons = ["ðŸ“", "ðŸ”", "ðŸ”¨", "â“"]
        custom_labels = [f"{icon} {label}" for icon, label in zip(defect_icons, defect_types)]
        
        fig = px.pie(
            values=defect_counts, 
            names=custom_labels, 
            hole=0.6,
            color_discrete_sequence=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"]
        )
        
        # ì¤‘ì•™ì— ì´ ë¶ˆëŸ‰ ìˆ˜ í‘œì‹œ
        total_defects = sum(defect_counts)
        fig.add_annotation(
            text=f"ì´ ë¶ˆëŸ‰<br>{total_defects}ê±´",
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
            hovertemplate='%{label}<br>ìˆ˜ëŸ‰: %{value}<br>ë¹„ìœ¨: %{percent}',
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # ìµœê·¼ ê²€ì‚¬ ë°ì´í„° ì„¹ì…˜ (ì „ì²´ ë„ˆë¹„)
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“‹ ìµœê·¼ ê²€ì‚¬ ë°ì´í„°</div>", unsafe_allow_html=True)
    
    # ìµœê·¼ ë°ì´í„°ë¥¼ ìœ„í•œ ìƒ˜í”Œ í…Œì´ë¸”
    recent_data = {
        "ðŸ“… ê²€ì‚¬ì¼ìž": pd.date_range(end=datetime.now(), periods=5).strftime("%Y-%m-%d"),
        "ðŸ”¢ LOTë²ˆí˜¸": [f"LOT{i:04d}" for i in range(1, 6)],
        "ðŸ‘¨â€ðŸ”§ ê²€ì‚¬ì›": np.random.choice(["í™ê¸¸ë™", "ê¹€ì² ìˆ˜", "ì´ì˜í¬"], 5),
        "âš™ï¸ ê³µì •": np.random.choice(["ì„ ì‚­", "ë°€ë§"], 5),
        "ðŸ“¦ ì „ì²´ìˆ˜ëŸ‰": np.random.randint(50, 200, 5),
        "âš ï¸ ë¶ˆëŸ‰ìˆ˜ëŸ‰": np.random.randint(0, 10, 5),
    }
    
    df = pd.DataFrame(recent_data)
    df["ðŸ“Š ë¶ˆëŸ‰ë¥ (%)"] = (df["âš ï¸ ë¶ˆëŸ‰ìˆ˜ëŸ‰"] / df["ðŸ“¦ ì „ì²´ìˆ˜ëŸ‰"] * 100).apply(lambda x: round(x, 2))
    
    # ë°ì´í„°í”„ë ˆìž„ì— ìŠ¤íƒ€ì¼ ì ìš©
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "ðŸ“Š ë¶ˆëŸ‰ë¥ (%)": st.column_config.ProgressColumn(
                "ðŸ“Š ë¶ˆëŸ‰ë¥ (%)",
                help="ë¶ˆëŸ‰ë¥  í¼ì„¼íŠ¸",
                format="%.1f%%",
                min_value=0,
                max_value=5,  # ëŒ€ë¶€ë¶„ì˜ ë¶ˆëŸ‰ë¥ ì€ 5% ì´í•˜ë¡œ ê°€ì •
            ),
        }
    )
    
    # ìµœê·¼ ê²€ì‚¬ ë°ì´í„° ìš”ì•½ ì§€í‘œ
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_defect_rate = df["ðŸ“Š ë¶ˆëŸ‰ë¥ (%)"].mean()
        st.metric("âš ï¸ í‰ê·  ë¶ˆëŸ‰ë¥ ", f"{avg_defect_rate:.2f}%")
    with col2:
        min_defect_rate = df["ðŸ“Š ë¶ˆëŸ‰ë¥ (%)"].min()
        st.metric("ðŸŸ¢ ìµœì†Œ ë¶ˆëŸ‰ë¥ ", f"{min_defect_rate:.2f}%")
    with col3:
        max_defect_rate = df["ðŸ“Š ë¶ˆëŸ‰ë¥ (%)"].max()
        st.metric("ðŸ”´ ìµœëŒ€ ë¶ˆëŸ‰ë¥ ", f"{max_defect_rate:.2f}%")
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "input_inspection":
    st.title("ðŸ“ ê²€ì‚¬ ë°ì´í„° ìž…ë ¥")
    
    # ê¸°ë³¸ ì •ë³´ ìž…ë ¥
    with st.form("basic_info"):
        st.subheader("ðŸ“‹ ê¸°ë³¸ ì •ë³´ ìž…ë ¥")
        
        col1, col2 = st.columns(2)
        with col1:
            inspector = st.selectbox("ðŸ‘¤ ê²€ì‚¬ì›", options=st.session_state.inspectors['name'].tolist())
            process = st.selectbox("âš™ï¸ ê³µì •", options=["ì„ ì‚­", "ë°€ë§"])
            
        with col2:
            date = st.date_input("ðŸ“… ê²€ì‚¬ì¼ìž")
            time = st.time_input("â° ê²€ì‚¬ì‹œê°„")
            
        lot_number = st.text_input("ðŸ”¢ LOT ë²ˆí˜¸")
        total_quantity = st.number_input("ðŸ“¦ ì „ì²´ ìˆ˜ëŸ‰", min_value=1, value=1)
        
        submit_basic = st.form_submit_button("âœ… ê¸°ë³¸ ì •ë³´ ë“±ë¡")
        
    if submit_basic:
        st.session_state.basic_info_valid = True
        st.success("âœ… ê¸°ë³¸ ì •ë³´ê°€ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤.")
    else:
        st.session_state.basic_info_valid = False

    # ë¶ˆëŸ‰ ì •ë³´ ìž…ë ¥
    if st.session_state.get('basic_info_valid', False):
        with st.form("defect_info"):
            st.subheader("âš ï¸ ë¶ˆëŸ‰ ì •ë³´ ìž…ë ¥")
            
            col1, col2 = st.columns(2)
            with col1:
                defect_type = st.selectbox("ðŸ” ë¶ˆëŸ‰ ìœ í˜•", 
                    options=["ì¹˜ìˆ˜", "í‘œë©´ê±°ì¹ ê¸°", "ì¹©í•‘", "ê¸°íƒ€"])
            
            with col2:
                defect_quantity = st.number_input("ðŸ“Š ë¶ˆëŸ‰ ìˆ˜ëŸ‰", 
                    min_value=1, max_value=total_quantity, value=1)
                
            submit_defect = st.form_submit_button("âž• ë¶ˆëŸ‰ ë“±ë¡")
            
        if submit_defect:
            new_defect = {
                "type": defect_type,
                "quantity": defect_quantity
            }
            st.session_state.registered_defects.append(new_defect)
            st.success(f"âœ… {defect_type} ë¶ˆëŸ‰ì´ {defect_quantity}ê°œ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤.")
            
        # ë“±ë¡ëœ ë¶ˆëŸ‰ ì •ë³´ í‘œì‹œ
        if st.session_state.registered_defects:
            st.subheader("ðŸ“‹ ë“±ë¡ëœ ë¶ˆëŸ‰ ì •ë³´")
            defects_df = pd.DataFrame(st.session_state.registered_defects)
            st.dataframe(defects_df)
            
            total_defects = defects_df['quantity'].sum()
            defect_rate = round((total_defects / total_quantity * 100), 2) if total_quantity > 0 else 0
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("ðŸ“Š ì´ ë¶ˆëŸ‰ ìˆ˜ëŸ‰", f"{total_defects}ê°œ")
            with col2:
                st.metric("ðŸ“ˆ ë¶ˆëŸ‰ë¥ ", f"{defect_rate}%")
                
        # ë¶ˆëŸ‰ ëª©ë¡ ì´ˆê¸°í™” ë²„íŠ¼
        if st.button("ðŸ”„ ë¶ˆëŸ‰ ëª©ë¡ ì´ˆê¸°í™”"):
            st.session_state.registered_defects = []
            st.success("âœ… ë¶ˆëŸ‰ ëª©ë¡ì´ ì´ˆê¸°í™”ë˜ì—ˆìŠµë‹ˆë‹¤.")
            st.stop()
            
        # ê²€ì‚¬ ë°ì´í„° ì €ìž¥
        if st.button("ðŸ’¾ ê²€ì‚¬ ë°ì´í„° ì €ìž¥"):
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
                    # ê²€ì‚¬ ë°ì´í„° ì €ìž¥ (ë¡œì»¬ ì„¸ì…˜ ìƒíƒœì—ë§Œ ì €ìž¥)
                    st.session_state.last_inspection = inspection_data
                    
                    # ë¶ˆëŸ‰ ë°ì´í„° ì €ìž¥ (ë¡œì»¬ ì„¸ì…˜ ìƒíƒœì—ë§Œ ì €ìž¥)
                    if 'saved_defects' not in st.session_state:
                        st.session_state.saved_defects = []
                        
                    for defect in st.session_state.registered_defects:
                        defect_data = {
                            "inspection_id": lot_number,  # ìž„ì‹œ IDë¡œ LOT ë²ˆí˜¸ ì‚¬ìš©
                            "defect_type": defect['type'],
                            "quantity": defect['quantity']
                        }
                        st.session_state.saved_defects.append(defect_data)
                    
                    st.success("âœ… ê²€ì‚¬ ë°ì´í„°ê°€ ì„±ê³µì ìœ¼ë¡œ ì €ìž¥ë˜ì—ˆìŠµë‹ˆë‹¤.")
                    st.session_state.registered_defects = []
                    st.stop()
                except Exception as e:
                    st.error(f"âŒ ë°ì´í„° ì €ìž¥ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
            else:
                st.warning("âš ï¸ ì €ìž¥í•  ë¶ˆëŸ‰ ë°ì´í„°ê°€ ì—†ìŠµë‹ˆë‹¤.")

elif st.session_state.page == "view_inspection":
    st.title("ê²€ì‚¬ ë°ì´í„° ì¡°íšŒ")
    
    # í•„í„°ë§ ì˜µì…˜
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_process = st.selectbox("ê³µì • í•„í„°", options=["ì „ì²´", "ì„ ì‚­", "ë°€ë§"])
    with col2:
        filter_start_date = st.date_input("ì‹œìž‘ì¼", datetime.now() - timedelta(days=30))
    with col3:
        filter_end_date = st.date_input("ì¢…ë£Œì¼", datetime.now())
    
    try:
        # ê²€ì‚¬ ë°ì´í„° ì¡°íšŒ
        st.subheader("ê²€ì‚¬ ë°ì´í„° ëª©ë¡")
        
        # Supabaseì—ì„œ ë°ì´í„° ê°€ì ¸ì˜¤ê¸° (ì‹¤ì œ êµ¬í˜„ í•„ìš”)
        # ìƒ˜í”Œ ë°ì´í„° í‘œì‹œ
        sample_data = {
            "inspection_id": [f"INSP{i}" for i in range(1, 11)],
            "inspector_name": np.random.choice(["í™ê¸¸ë™", "ê¹€ì² ìˆ˜", "ì´ì˜í¬"], 10),
            "process": np.random.choice(["ì„ ì‚­", "ë°€ë§"], 10),
            "inspection_date": pd.date_range(start=filter_start_date, periods=10).strftime("%Y-%m-%d"),
            "lot_number": [f"LOT{i:04d}" for i in range(1, 11)],
            "total_quantity": np.random.randint(50, 200, 10),
            "defect_count": np.random.randint(0, 10, 10),
        }
        
        df = pd.DataFrame(sample_data)
        df["defect_rate"] = (df["defect_count"] / df["total_quantity"] * 100).apply(lambda x: round(x, 2))
        
        # ê³µì • í•„í„°ë§
        if filter_process != "ì „ì²´":
            df = df[df["process"] == filter_process]
            
        st.dataframe(df)
        
        # ì„ íƒí•œ ë°ì´í„° ìƒì„¸ ë³´ê¸° ê¸°ëŠ¥
        inspection_id = st.selectbox("ìƒì„¸ ì •ë³´ë¥¼ ë³¼ ê²€ì‚¬ ID ì„ íƒ", options=df["inspection_id"].tolist())
        
        if inspection_id:
            st.subheader(f"ê²€ì‚¬ ìƒì„¸ ì •ë³´: {inspection_id}")
            # ì„ íƒí•œ ê²€ì‚¬ì˜ ìƒì„¸ ì •ë³´ (ìƒ˜í”Œ)
            selected_row = df[df["inspection_id"] == inspection_id].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ê²€ì‚¬ì›", selected_row["inspector_name"])
                st.metric("ì´ ìˆ˜ëŸ‰", f"{selected_row['total_quantity']}ê°œ")
            with col2:
                st.metric("ê³µì •", selected_row["process"])
                st.metric("ë¶ˆëŸ‰ ìˆ˜ëŸ‰", f"{selected_row['defect_count']}ê°œ")
            with col3:
                st.metric("ê²€ì‚¬ì¼", selected_row["inspection_date"])
                st.metric("ë¶ˆëŸ‰ë¥ ", f"{selected_row['defect_rate']}%")
                
            # ë¶ˆëŸ‰ ìƒì„¸ ì •ë³´ (ìƒ˜í”Œ)
            st.subheader("ë¶ˆëŸ‰ ìƒì„¸ ì •ë³´")
            defect_detail = {
                "defect_type": np.random.choice(["ì¹˜ìˆ˜", "í‘œë©´ê±°ì¹ ê¸°", "ì¹©í•‘", "ê¸°íƒ€"], 
                                           selected_row["defect_count"]),
                "quantity": np.random.randint(1, 5, selected_row["defect_count"])
            }
            
            if selected_row["defect_count"] > 0:
                defect_df = pd.DataFrame(defect_detail)
                st.dataframe(defect_df)
                
                # ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬ ì°¨íŠ¸
                fig = px.pie(defect_df, names="defect_type", values="quantity", 
                           title="ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬")
                st.plotly_chart(fig)
            else:
                st.info("ì´ ê²€ì‚¬ì—ëŠ” ë“±ë¡ëœ ë¶ˆëŸ‰ì´ ì—†ìŠµë‹ˆë‹¤.")
    except Exception as e:
        st.error(f"ë°ì´í„° ì¡°íšŒ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")

elif st.session_state.page == "manage_inspectors":
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆëŠ” íŽ˜ì´ì§€ìž…ë‹ˆë‹¤.")
        st.stop()
        
    st.title("ê²€ì‚¬ì› ê´€ë¦¬")
    
    # ê²€ì‚¬ì› ëª©ë¡ í‘œì‹œ
    st.subheader("ë“±ë¡ëœ ê²€ì‚¬ì› ëª©ë¡")
    
    try:
        inspectors_df = load_inspectors()
        st.dataframe(inspectors_df)
        
        # ìƒˆ ê²€ì‚¬ì› ë“±ë¡ ì–‘ì‹
        st.subheader("ìƒˆ ê²€ì‚¬ì› ë“±ë¡")
        with st.form("new_inspector"):
            col1, col2 = st.columns(2)
            with col1:
                inspector_id = st.text_input("ê²€ì‚¬ì› ID")
                name = st.text_input("ì´ë¦„")
            with col2:
                department = st.selectbox("ë¶€ì„œ", options=["CNC_1", "CNC_2", "PQC_LINE", "CDC"])
                process = st.selectbox("ë‹´ë‹¹ ê³µì •", options=["ì„ ì‚­", "ë°€ë§", "ê²€ì‚¬", "ê¸°íƒ€"])
            
            years = st.number_input("ê·¼ì†ë…„ìˆ˜", min_value=0.0, step=0.5)
            
            submit_inspector = st.form_submit_button("ê²€ì‚¬ì› ë“±ë¡")
            
        if submit_inspector:
            if not inspector_id or not name:
                st.error("ê²€ì‚¬ì› IDì™€ ì´ë¦„ì€ í•„ìˆ˜ ìž…ë ¥ í•­ëª©ìž…ë‹ˆë‹¤.")
            else:
                new_inspector = {
                    "id": inspector_id,
                    "name": name,
                    "department": department,
                    "process": process,
                    "years_of_service": years
                }
                
                try:
                    # Supabase ë°ì´í„°ë² ì´ìŠ¤ ì €ìž¥ì€ RLS ì •ì±… ì„¤ì •ì„ ë¨¼ì € í™•ì¸ í›„ ì§„í–‰
                    # í˜„ìž¬ëŠ” ìž„ì‹œë¡œ ì„¸ì…˜ ìƒíƒœì—ë§Œ ì €ìž¥
                    temp_df = pd.DataFrame([new_inspector])
                    if 'inspectors_df' in st.session_state:
                        st.session_state.inspectors_df = pd.concat([st.session_state.inspectors_df, temp_df])
                    else:
                        st.session_state.inspectors_df = temp_df
                    
                    # ê¸°ì¡´ inspectors ì—…ë°ì´íŠ¸
                    if 'inspectors' in st.session_state:
                        new_inspectors = st.session_state.inspectors.copy()
                        new_inspectors = pd.concat([new_inspectors, temp_df], ignore_index=True)
                        st.session_state.inspectors = new_inspectors
                    
                    st.success(f"{name} ê²€ì‚¬ì›ì´ ì„±ê³µì ìœ¼ë¡œ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤. (ë¡œì»¬ ì €ìž¥)")
                    st.info("í˜„ìž¬ Supabase RLS ì •ì±…ìœ¼ë¡œ ì¸í•´ ë°ì´í„°ëŠ” ë¡œì»¬ ì„¸ì…˜ì—ë§Œ ì €ìž¥ë©ë‹ˆë‹¤.")
                    
                except Exception as e:
                    st.error(f"ê²€ì‚¬ì› ë“±ë¡ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
    except Exception as e:
        st.error(f"ê²€ì‚¬ì› ê´€ë¦¬ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")

elif st.session_state.page == "settings":
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆëŠ” íŽ˜ì´ì§€ìž…ë‹ˆë‹¤.")
        st.stop()
        
    st.title("ì‹œìŠ¤í…œ ì„¤ì •")
    
    # ì‹œìŠ¤í…œ ì„¤ì • ì–‘ì‹
    st.subheader("ë¶ˆëŸ‰ ìœ í˜• ì„¤ì •")
    current_defect_types = st.session_state.defect_types
    
    defect_types_str = st.text_area("ë¶ˆëŸ‰ ìœ í˜• ëª©ë¡ (ì‰¼í‘œë¡œ êµ¬ë¶„)", 
                                  value=", ".join(current_defect_types))
    
    if st.button("ë¶ˆëŸ‰ ìœ í˜• ì €ìž¥"):
        new_defect_types = [dtype.strip() for dtype in defect_types_str.split(",")]
        st.session_state.defect_types = new_defect_types
        st.success("ë¶ˆëŸ‰ ìœ í˜•ì´ ì €ìž¥ë˜ì—ˆìŠµë‹ˆë‹¤.")
        
    # ë°ì´í„°ë² ì´ìŠ¤ ì„¤ì • (ê´€ë¦¬ìž ì „ìš©)
    st.subheader("ë°ì´í„°ë² ì´ìŠ¤ ê´€ë¦¬")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ë°ì´í„°ë² ì´ìŠ¤ ë°±ì—…"):
            st.info("ë°ì´í„°ë² ì´ìŠ¤ ë°±ì—… ê¸°ëŠ¥ì€ ì¤€ë¹„ ì¤‘ìž…ë‹ˆë‹¤.")
    with col2:
        if st.button("í…ŒìŠ¤íŠ¸ ë°ì´í„° ìƒì„±"):
            st.info("í…ŒìŠ¤íŠ¸ ë°ì´í„° ìƒì„± ê¸°ëŠ¥ì€ ì¤€ë¹„ ì¤‘ìž…ë‹ˆë‹¤.")

elif st.session_state.page == "daily_report":
    # ì¼ê°„ ë¦¬í¬íŠ¸ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ“Š ì¼ê°„ ë¦¬í¬íŠ¸</h1></div>", unsafe_allow_html=True)
    
    # ë‚ ì§œ ì„ íƒ
    selected_date = st.date_input("ðŸ“… ì¡°íšŒí•  ë‚ ì§œ ì„ íƒ", datetime.now())
    
    # ë°ì´í„° ë¡œë”© í‘œì‹œ
    with st.spinner("ë°ì´í„° ë¶ˆëŸ¬ì˜¤ëŠ” ì¤‘..."):
        time.sleep(0.5)  # ë°ì´í„° ë¡œë”© ì‹œë®¬ë ˆì´ì…˜
        
    # ì¼ê°„ ìš”ì•½ ì§€í‘œ
    st.subheader("ì¼ê°„ í’ˆì§ˆ ìš”ì•½")
    
    # 4ê°œì˜ ì£¼ìš” ì§€í‘œ ì¹´ë“œ
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("ë‹¹ì¼ ê²€ì‚¬ ê±´ìˆ˜", "28", "+3")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("ë‹¹ì¼ ë¶ˆëŸ‰ë¥ ", "0.65%", "-0.1%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("ì£¼ìš” ë¶ˆëŸ‰ ìœ í˜•", "í‘œë©´ê±°ì¹ ê¸°", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("í‰ê·  ê²€ì‚¬ ì‹œê°„", "8.2ë¶„", "-0.5ë¶„")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ì‹œê°„ëŒ€ë³„ ê²€ì‚¬ ì¶”ì´
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>â° ì‹œê°„ëŒ€ë³„ ê²€ì‚¬ ê±´ìˆ˜</div>", unsafe_allow_html=True)
    
    # ì‹œê°„ëŒ€ë³„ ë°ì´í„° ì¤€ë¹„
    hours = list(range(9, 18))  # 9ì‹œë¶€í„° 17ì‹œê¹Œì§€
    hourly_inspections = np.random.randint(3, 15, size=len(hours))
    
    # ì‹œê°„ëŒ€ë³„ ê²€ì‚¬ ê±´ìˆ˜ ì°¨íŠ¸
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[f"{h}:00" for h in hours],
        y=hourly_inspections,
        marker_color="#4361ee",
        hovertemplate='ì‹œê°„: %{x}<br>ê²€ì‚¬ ê±´ìˆ˜: %{y}ê±´<extra></extra>'
    ))
    
    fig.update_layout(
        title=None,
        xaxis_title="ì‹œê°„",
        yaxis_title="ê²€ì‚¬ ê±´ìˆ˜",
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.05)")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ë¶ˆëŸ‰ ë°œìƒ í˜„í™©
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ” ë¶ˆëŸ‰ ë°œìƒ í˜„í™©</div>", unsafe_allow_html=True)
    
    # ë¶ˆëŸ‰ íƒ€ìž…ë³„ ë°ì´í„°
    defect_types = ["ì¹˜ìˆ˜ ë¶ˆëŸ‰", "í‘œë©´ ê±°ì¹ ê¸°", "ì¹©í•‘", "ê¸°íƒ€"]
    defect_counts = np.random.randint(1, 8, size=len(defect_types))
    
    # ì°¨íŠ¸
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # ë§‰ëŒ€ ê·¸ëž˜í”„
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=defect_types,
            y=defect_counts,
            orientation='h',
            marker_color=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"],
            hovertemplate='ìœ í˜•: %{y}<br>ê±´ìˆ˜: %{x}ê±´<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="ë°œìƒ ê±´ìˆ˜",
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # ë¶ˆëŸ‰ ìš”ì•½ í†µê³„
        total_defects = sum(defect_counts)
        total_inspected = sum(hourly_inspections)
        defect_rate = (total_defects / total_inspected) * 100
        
        st.markdown("<div style='text-align: center; padding: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='font-size: 24px;'>ì´ ë¶ˆëŸ‰ ê±´ìˆ˜</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2 style='font-size: 36px; color: #4361ee;'>{total_defects}ê±´</h2>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='font-size: 18px;'>ë¶ˆëŸ‰ë¥ : {defect_rate:.2f}%</h3>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ë¶ˆëŸ‰ ì„¸ë¶€ í…Œì´ë¸”
    defect_details = {
        "ì‹œê°„": [f"{np.random.choice(hours)}:00" for _ in range(total_defects)],
        "LOTë²ˆí˜¸": [f"LOT{i:04d}" for i in range(1, total_defects + 1)],
        "ë¶ˆëŸ‰ìœ í˜•": np.random.choice(defect_types, total_defects),
        "ë¶ˆëŸ‰ìˆ˜ëŸ‰": np.random.randint(1, 5, total_defects)
    }
    
    defect_df = pd.DataFrame(defect_details)
    st.dataframe(defect_df, use_container_width=True, hide_index=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "weekly_report":
    # ì£¼ê°„ ë¦¬í¬íŠ¸ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ“… ì£¼ê°„ ë¦¬í¬íŠ¸</h1></div>", unsafe_allow_html=True)
    
    # ì£¼ê°„ ì„ íƒê¸°
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    
    col1, col2 = st.columns(2)
    with col1:
        week_start = st.date_input("ðŸ“… ì£¼ê°„ ì‹œìž‘ì¼", start_of_week)
    with col2:
        week_end = st.date_input("ðŸ“… ì£¼ê°„ ì¢…ë£Œì¼", end_of_week)
    
    # ë°ì´í„° ë¡œë”© í‘œì‹œ
    with st.spinner("ì£¼ê°„ ë°ì´í„° ë¶ˆëŸ¬ì˜¤ëŠ” ì¤‘..."):
        time.sleep(0.5)  # ë°ì´í„° ë¡œë”© ì‹œë®¬ë ˆì´ì…˜
    
    # ì£¼ê°„ ìš”ì•½ ì§€í‘œ
    st.subheader("ì£¼ê°„ í’ˆì§ˆ ìš”ì•½")
    
    # ì£¼ìš” ì§€í‘œ ì¹´ë“œ
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("ì£¼ê°„ ê²€ì‚¬ ê±´ìˆ˜", "143", "+12")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("ì£¼ê°„ ë¶ˆëŸ‰ë¥ ", "0.72%", "-0.08%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("ì£¼ìš” ë¶ˆëŸ‰ ìœ í˜•", "ì¹˜ìˆ˜ë¶ˆëŸ‰", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("ì£¼ê°„ ëª©í‘œ ë‹¬ì„±", "95.2%", "+2.1%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ì¼ë³„ ì¶”ì´ ì°¨íŠ¸
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“ˆ ì¼ë³„ ê²€ì‚¬ ë° ë¶ˆëŸ‰ ì¶”ì´</div>", unsafe_allow_html=True)
    
    # ìš”ì¼ ë°ì´í„°
    weekdays = ["ì›”", "í™”", "ìˆ˜", "ëª©", "ê¸ˆ", "í† ", "ì¼"]
    inspections = np.random.randint(15, 35, size=7)
    defect_rates = np.random.rand(7) * 1.5  # 0~1.5% ì‚¬ì´ì˜ ë¶ˆëŸ‰ë¥ 
    
    # ì´ì¤‘ Yì¶• ì°¨íŠ¸
    fig = go.Figure()
    
    # ì²« ë²ˆì§¸ Yì¶•: ê²€ì‚¬ ê±´ìˆ˜ (ë§‰ëŒ€)
    fig.add_trace(go.Bar(
        x=weekdays,
        y=inspections,
        name="ê²€ì‚¬ ê±´ìˆ˜",
        marker_color="#4361ee",
        yaxis="y",
        hovertemplate='%{x}ìš”ì¼<br>ê²€ì‚¬ ê±´ìˆ˜: %{y}ê±´<extra></extra>',
        opacity=0.8
    ))
    
    # ë‘ ë²ˆì§¸ Yì¶•: ë¶ˆëŸ‰ë¥  (ì„ )
    fig.add_trace(go.Scatter(
        x=weekdays,
        y=defect_rates,
        name="ë¶ˆëŸ‰ë¥ ",
        marker=dict(size=8),
        line=dict(color="#fb8c00", width=3),
        mode="lines+markers",
        yaxis="y2",
        hovertemplate='%{x}ìš”ì¼<br>ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # ëª©í‘œ ë¶ˆëŸ‰ë¥  ë¼ì¸
    target_rate = 1.0
    fig.add_trace(go.Scatter(
        x=weekdays,
        y=[target_rate] * 7,
        name="ëª©í‘œ ë¶ˆëŸ‰ë¥ ",
        line=dict(color="red", width=2, dash="dash"),
        mode="lines",
        yaxis="y2",
        hovertemplate='ëª©í‘œ ë¶ˆëŸ‰ë¥ : %{y}%<extra></extra>'
    ))
    
    # ë ˆì´ì•„ì›ƒ ì„¤ì •
    fig.update_layout(
        title=None,
        xaxis=dict(title="ìš”ì¼"),
        yaxis=dict(
            title="ê²€ì‚¬ ê±´ìˆ˜",
            side="left",
            showgrid=False
        ),
        yaxis2=dict(
            title="ë¶ˆëŸ‰ë¥  (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, max(defect_rates) * 1.2]  # Yì¶• ë²”ìœ„ ì„¤ì •
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ë¶ˆëŸ‰ ìœ í˜• ë° ê³µì •ë³„ ë¶„ì„
    col1, col2 = st.columns(2)
    
    with col1:
        # ë¶ˆëŸ‰ ìœ í˜• ë¶„ì„
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>ðŸ” ë¶ˆëŸ‰ ìœ í˜• ë¶„ì„</div>", unsafe_allow_html=True)
        
        # ë¶ˆëŸ‰ ìœ í˜•ë³„ ë°ì´í„°
        defect_types = ["ì¹˜ìˆ˜ ë¶ˆëŸ‰", "í‘œë©´ ê±°ì¹ ê¸°", "ì¹©í•‘", "ê¸°íƒ€"]
        defect_counts = np.random.randint(5, 20, size=len(defect_types))
        
        # ìˆ˜í‰ ë§‰ëŒ€ ê·¸ëž˜í”„
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=defect_types,
            x=defect_counts,
            orientation='h',
            marker_color=["#4361ee", "#4cb782", "#fb8c00", "#7c3aed"],
            hovertemplate='ìœ í˜•: %{y}<br>ê±´ìˆ˜: %{x}ê±´<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="ë°œìƒ ê±´ìˆ˜",
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # ê³µì •ë³„ ë¶ˆëŸ‰ë¥ 
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>âš™ï¸ ê³µì •ë³„ ë¶ˆëŸ‰ë¥ </div>", unsafe_allow_html=True)
        
        # ê³µì •ë³„ ë°ì´í„°
        processes = ["ì„ ì‚­", "ë°€ë§", "ì—°ì‚­", "ì¡°ë¦½"]
        process_rates = np.random.rand(len(processes)) * 1.8  # 0~1.8% ë¶ˆëŸ‰ë¥ 
        
        # ê³µì •ë³„ ë¶ˆëŸ‰ë¥  ì°¨íŠ¸
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=processes,
            y=process_rates,
            marker_color="#4cb782",
            hovertemplate='ê³µì •: %{x}<br>ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
        ))
        
        # í‰ê·  ë¶ˆëŸ‰ë¥  ë¼ì¸
        avg_rate = np.mean(process_rates)
        fig.add_trace(go.Scatter(
            x=processes,
            y=[avg_rate] * len(processes),
            mode="lines",
            name="í‰ê· ",
            line=dict(color="#fb8c00", width=2, dash="dash"),
            hovertemplate='í‰ê·  ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=None,
            xaxis_title="ê³µì •",
            yaxis_title="ë¶ˆëŸ‰ë¥  (%)",
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ì£¼ê°„ ê²€ì‚¬ ë°ì´í„° í…Œì´ë¸”
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“‹ ì£¼ê°„ ê²€ì‚¬ ë°ì´í„° ìš”ì•½</div>", unsafe_allow_html=True)
    
    # ìƒ˜í”Œ ë°ì´í„°
    weekly_data = {
        "ìš”ì¼": weekdays,
        "ê²€ì‚¬ ê±´ìˆ˜": inspections,
        "ë¶ˆëŸ‰ ê±´ìˆ˜": [int(rate * inspection / 100) for rate, inspection in zip(defect_rates, inspections)],
        "ë¶ˆëŸ‰ë¥  (%)": defect_rates.round(2),
        "ì£¼ìš” ë¶ˆëŸ‰ ìœ í˜•": np.random.choice(defect_types, size=7)
    }
    
    weekly_df = pd.DataFrame(weekly_data)
    st.dataframe(weekly_df, use_container_width=True, hide_index=True)
    
    # ì£¼ê°„ ìš”ì•½ í†µê³„
    col1, col2, col3 = st.columns(3)
    with col1:
        avg_inspection = int(np.mean(inspections))
        st.metric("ðŸ“Š í‰ê·  ì¼ì¼ ê²€ì‚¬ ê±´ìˆ˜", f"{avg_inspection}ê±´")
    with col2:
        avg_defect_rate = np.mean(defect_rates)
        st.metric("âš ï¸ í‰ê·  ë¶ˆëŸ‰ë¥ ", f"{avg_defect_rate:.2f}%")
    with col3:
        total_inspections = sum(inspections)
        st.metric("ðŸ“ˆ ì´ ê²€ì‚¬ ê±´ìˆ˜", f"{total_inspections}ê±´")
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "monthly_report":
    # ì›”ê°„ ë¦¬í¬íŠ¸ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ“† ì›”ê°„ ë¦¬í¬íŠ¸</h1></div>", unsafe_allow_html=True)
    
    # ì›” ì„ íƒ
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("ì—°ë„ ì„ íƒ", options=list(range(current_year-2, current_year+1)), index=2)
    with col2:
        selected_month = st.selectbox("ì›” ì„ íƒ", options=list(range(1, 13)), index=current_month-1)
    
    # ì„ íƒëœ ì›”ì˜ ë¬¸ìžì—´ í‘œí˜„
    month_names = ["1ì›”", "2ì›”", "3ì›”", "4ì›”", "5ì›”", "6ì›”", "7ì›”", "8ì›”", "9ì›”", "10ì›”", "11ì›”", "12ì›”"]
    selected_month_name = month_names[selected_month-1]
    
    # ë°ì´í„° ë¡œë”© í‘œì‹œ
    with st.spinner(f"{selected_year}ë…„ {selected_month_name} ë°ì´í„° ë¶ˆëŸ¬ì˜¤ëŠ” ì¤‘..."):
        time.sleep(0.5)  # ë°ì´í„° ë¡œë”© ì‹œë®¬ë ˆì´ì…˜
    
    # ì›”ê°„ ìš”ì•½ ì§€í‘œ
    st.subheader(f"{selected_year}ë…„ {selected_month_name} í’ˆì§ˆ ìš”ì•½")
    
    # ì£¼ìš” ì§€í‘œ ì¹´ë“œ
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("ì›”ê°„ ê²€ì‚¬ ê±´ìˆ˜", "587", "+23")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("ì›”ê°„ ë¶ˆëŸ‰ë¥ ", "0.68%", "-0.12%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("ì£¼ìš” ë¶ˆëŸ‰ ìœ í˜•", "í‘œë©´ê±°ì¹ ê¸°", "")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("ì›”ê°„ ëª©í‘œ ë‹¬ì„±", "97.8%", "+1.5%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ì›”ê°„ ì¶”ì´ ì°¨íŠ¸
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“ˆ ì¼ë³„ ë¶ˆëŸ‰ë¥  ì¶”ì´</div>", unsafe_allow_html=True)
    
    # ì„ íƒëœ ì›”ì˜ ì¼ìˆ˜ ê³„ì‚°
    import calendar
    days_in_month = calendar.monthrange(selected_year, selected_month)[1]
    
    # ì¼ìž ë°ì´í„°
    days = list(range(1, days_in_month + 1))
    # ë¶ˆëŸ‰ë¥  ë°ì´í„° (í‰ê·  0.7% ì£¼ë³€ì—ì„œ ëžœë¤ ë³€ë™)
    daily_defect_rates = [0.7 + (np.random.rand() - 0.5) / 2 for _ in range(days_in_month)]
    
    # ì°¨íŠ¸ ìƒì„±
    fig = go.Figure()
    
    # ë¶ˆëŸ‰ë¥  ë¼ì¸
    fig.add_trace(go.Scatter(
        x=days,
        y=daily_defect_rates,
        mode="lines+markers",
        name="ì¼ë³„ ë¶ˆëŸ‰ë¥ ",
        line=dict(color="#4361ee", width=2),
        marker=dict(size=6),
        hovertemplate='%{x}ì¼<br>ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # í‰ê·  ë¶ˆëŸ‰ë¥  ë¼ì¸
    avg_rate = np.mean(daily_defect_rates)
    fig.add_trace(go.Scatter(
        x=[days[0], days[-1]],
        y=[avg_rate, avg_rate],
        mode="lines",
        name="í‰ê·  ë¶ˆëŸ‰ë¥ ",
        line=dict(color="#4cb782", width=2, dash="dash"),
        hovertemplate='í‰ê·  ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # ëª©í‘œ ë¶ˆëŸ‰ë¥  ë¼ì¸
    target_rate = 1.0
    fig.add_trace(go.Scatter(
        x=[days[0], days[-1]],
        y=[target_rate, target_rate],
        mode="lines",
        name="ëª©í‘œ ë¶ˆëŸ‰ë¥ ",
        line=dict(color="red", width=2, dash="dot"),
        hovertemplate='ëª©í‘œ ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # ë ˆì´ì•„ì›ƒ ì„¤ì •
    fig.update_layout(
        title=None,
        xaxis=dict(
            title="ì¼ìž",
            tickmode='linear',
            tick0=1,
            dtick=3,  # 3ì¼ ê°„ê²©ìœ¼ë¡œ í‘œì‹œ
        ),
        yaxis=dict(
            title="ë¶ˆëŸ‰ë¥  (%)",
            range=[0, max(daily_defect_rates) * 1.5]  # Yì¶• ë²”ìœ„ ì„¤ì •
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ê³µì • ë° ë¶ˆëŸ‰ ë¶„ì„
    col1, col2 = st.columns(2)
    
    with col1:
        # ê³µì •ë³„ ë¶ˆëŸ‰ë¥  ë¹„êµ
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>âš™ï¸ ê³µì •ë³„ ë¶ˆëŸ‰ë¥  ë¹„êµ</div>", unsafe_allow_html=True)
        
        # ê³µì •ë³„ ë°ì´í„°
        processes = ["ì„ ì‚­", "ë°€ë§", "ì—°ì‚­", "ë“œë¦´ë§", "ì¡°ë¦½"]
        process_inspections = np.random.randint(80, 150, size=len(processes))
        process_defect_rates = np.random.rand(len(processes)) * 1.5  # 0~1.5% ë¶ˆëŸ‰ë¥ 
        
        # ê³µì •ë³„ ë¶ˆëŸ‰ë¥  ë° ê²€ì‚¬ ê±´ìˆ˜ë¥¼ í•¨ê»˜ í‘œì‹œí•˜ëŠ” ì°¨íŠ¸
        process_df = pd.DataFrame({
            "ê³µì •": processes,
            "ê²€ì‚¬ê±´ìˆ˜": process_inspections,
            "ë¶ˆëŸ‰ë¥ ": process_defect_rates
        })
        
        # ê²€ì‚¬ê±´ìˆ˜ì— ë¹„ë¡€í•œ ë²„ë¸” í¬ê¸°ë¡œ í‘œì‹œ
        fig = px.scatter(
            process_df,
            x="ê³µì •",
            y="ë¶ˆëŸ‰ë¥ ",
            size="ê²€ì‚¬ê±´ìˆ˜",
            color="ê³µì •",
            size_max=50,
            hover_name="ê³µì •",
            hover_data={"ê³µì •": False, "ê²€ì‚¬ê±´ìˆ˜": True, "ë¶ˆëŸ‰ë¥ ": ":.2f%"},
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig.update_layout(
            title=None,
            xaxis_title=None,
            yaxis_title="ë¶ˆëŸ‰ë¥  (%)",
            showlegend=False,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=320
        )
        
        # ë¶ˆëŸ‰ë¥ ì˜ í‰ê· ì„  ì¶”ê°€
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
            text=f"í‰ê· : {avg_process_rate:.2f}%",
            showarrow=False,
            yshift=10,
            font=dict(size=12, color="#4cb782")
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        # ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='emoji-title'>ðŸ” ë¶ˆëŸ‰ ìœ í˜• ë¶„í¬</div>", unsafe_allow_html=True)
        
        # ë¶ˆëŸ‰ ìœ í˜•ë³„ ë°ì´í„°
        defect_types = ["ì¹˜ìˆ˜ ë¶ˆëŸ‰", "í‘œë©´ ê±°ì¹ ê¸°", "ì¹©í•‘", "ì†Œìž¬ ê²°í•¨", "ì¡°ë¦½ ë¶ˆëŸ‰", "ê¸°íƒ€"]
        defect_percents = np.random.rand(len(defect_types))
        defect_percents = (defect_percents / defect_percents.sum()) * 100  # ë°±ë¶„ìœ¨ë¡œ ë³€í™˜
        
        # ë¶ˆëŸ‰ ìœ í˜• íŒŒì´ ì°¨íŠ¸
        fig = go.Figure(data=[go.Pie(
            labels=defect_types,
            values=defect_percents,
            hole=.4,
            textinfo="percent+label",
            insidetextorientation="radial",
            marker=dict(colors=px.colors.qualitative.Bold),
            hovertemplate='%{label}<br>ë¹„ìœ¨: %{percent}<extra></extra>'
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
    
    # ì£¼ë³„ ì„±ëŠ¥ ì¶”ì´
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“Š ì£¼ë³„ ì„±ëŠ¥ ì¶”ì´</div>", unsafe_allow_html=True)
    
    # ì£¼ì°¨ ë°ì´í„° (ë³´í†µ í•œ ë‹¬ì— 4-5ì£¼)
    weeks = [f"{selected_month}ì›” 1ì£¼ì°¨", f"{selected_month}ì›” 2ì£¼ì°¨", 
            f"{selected_month}ì›” 3ì£¼ì°¨", f"{selected_month}ì›” 4ì£¼ì°¨"]
    if days_in_month > 28:
        weeks.append(f"{selected_month}ì›” 5ì£¼ì°¨")
    
    # ì£¼ë³„ ê²€ì‚¬ ê±´ìˆ˜ ë° ë¶ˆëŸ‰ë¥ 
    weekly_inspections = np.random.randint(120, 180, size=len(weeks))
    weekly_defect_rates = np.random.rand(len(weeks)) * 1.2  # 0~1.2% ë¶ˆëŸ‰ë¥ 
    
    # ë³µí•© ì°¨íŠ¸ (ë§‰ëŒ€ + ì„ )
    fig = go.Figure()
    
    # ê²€ì‚¬ ê±´ìˆ˜ (ë§‰ëŒ€)
    fig.add_trace(go.Bar(
        x=weeks,
        y=weekly_inspections,
        name="ê²€ì‚¬ ê±´ìˆ˜",
        marker_color="#4361ee",
        yaxis="y",
        hovertemplate='%{x}<br>ê²€ì‚¬ ê±´ìˆ˜: %{y}ê±´<extra></extra>',
        opacity=0.8
    ))
    
    # ë¶ˆëŸ‰ë¥  (ì„ )
    fig.add_trace(go.Scatter(
        x=weeks,
        y=weekly_defect_rates,
        name="ë¶ˆëŸ‰ë¥ ",
        yaxis="y2",
        line=dict(color="#fb8c00", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        hovertemplate='%{x}<br>ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # ë ˆì´ì•„ì›ƒ ì„¤ì •
    fig.update_layout(
        title=None,
        xaxis=dict(title="ì£¼ì°¨"),
        yaxis=dict(
            title="ê²€ì‚¬ ê±´ìˆ˜",
            side="left",
            showgrid=False
        ),
        yaxis2=dict(
            title="ë¶ˆëŸ‰ë¥  (%)",
            side="right",
            overlaying="y",
            showgrid=False,
            range=[0, max(weekly_defect_rates) * 1.3]  # Yì¶• ë²”ìœ„ ì„¤ì •
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=60, t=10, b=20),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ì£¼ë³„ ìš”ì•½ í…Œì´ë¸”
    weekly_summary = pd.DataFrame({
        "ì£¼ì°¨": weeks,
        "ê²€ì‚¬ ê±´ìˆ˜": weekly_inspections,
        "ë¶ˆëŸ‰ ê±´ìˆ˜": [int(rate * inspection / 100) for rate, inspection in zip(weekly_defect_rates, weekly_inspections)],
        "ë¶ˆëŸ‰ë¥  (%)": weekly_defect_rates.round(2),
        "ëª©í‘œ ë‹¬ì„± ì—¬ë¶€": [rate < 1.0 for rate in weekly_defect_rates]
    })
    
    # í…Œì´ë¸” í˜•ì‹ ì¡°ì •
    st.dataframe(
        weekly_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ë¶ˆëŸ‰ë¥  (%)": st.column_config.ProgressColumn(
                "ë¶ˆëŸ‰ë¥  (%)",
                help="ì£¼ë³„ ë¶ˆëŸ‰ë¥  í¼ì„¼íŠ¸",
                format="%.2f%%",
                min_value=0,
                max_value=2,
            ),
            "ëª©í‘œ ë‹¬ì„± ì—¬ë¶€": st.column_config.CheckboxColumn(
                "ëª©í‘œ ë‹¬ì„± ì—¬ë¶€",
                help="ë¶ˆëŸ‰ë¥  1% ì´í•˜ ëª©í‘œ ë‹¬ì„± ì—¬ë¶€"
            )
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page == "manager_auth":
    # ê´€ë¦¬ìž ë° ì‚¬ìš©ìž ê´€ë¦¬ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ‘¥ ê´€ë¦¬ìž ë° ì‚¬ìš©ìž ê´€ë¦¬</h1></div>", unsafe_allow_html=True)
    
    # ê´€ë¦¬ìž ê¶Œí•œ í™•ì¸
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ì´ íŽ˜ì´ì§€ëŠ” ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆìŠµë‹ˆë‹¤.")
        st.stop()
    
    # íƒ­ êµ¬ì„±
    tab1, tab2 = st.tabs(["ðŸ‘¤ ì‚¬ìš©ìž ê´€ë¦¬", "ðŸ”‘ ê¶Œí•œ ì„¤ì •"])
    
    with tab1:
        # ì‚¬ìš©ìž ê´€ë¦¬ ì„¹ì…˜
        st.subheader("ê´€ë¦¬ìž ë“±ë¡ í˜„í™©")
        
        # ì„¸ì…˜ ìƒíƒœì— ê´€ë¦¬ìž ëª©ë¡ ì´ˆê¸°í™” (ì²˜ìŒ ì ‘ì† ì‹œì—ë§Œ)
        if 'admin_users' not in st.session_state:
            # JSON íŒŒì¼ì—ì„œ ê´€ë¦¬ìž ë°ì´í„° ë¡œë“œ
            st.session_state.admin_users = load_admin_data()
            
            # ë°ì´í„°ê°€ ë¹„ì–´ìžˆëŠ”ì§€ í™•ì¸í•˜ê³ , ë¹„ì–´ìžˆìœ¼ë©´ ê¸°ë³¸ ê´€ë¦¬ìž ë°ì´í„° ì¶”ê°€
            if len(st.session_state.admin_users.get("ì•„ì´ë””", [])) == 0:
                st.session_state.admin_users = {
                    "ì•„ì´ë””": ["admin"],
                    "ì´ë¦„": ["ê´€ë¦¬ìž"],
                    "ê¶Œí•œ": ["ê´€ë¦¬ìž"],
                    "ë¶€ì„œ": ["ê´€ë¦¬ë¶€"],
                    "ìµœê·¼ì ‘ì†ì¼": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                    "ìƒíƒœ": ["í™œì„±"]
                }
                # ê¸°ë³¸ ê´€ë¦¬ìž ë°ì´í„° ì €ìž¥
                save_admin_data(st.session_state.admin_users)
                st.info("ê¸°ë³¸ ê´€ë¦¬ìž ê³„ì •ì´ ìƒì„±ë˜ì—ˆìŠµë‹ˆë‹¤.")
        
        # ë°ì´í„°í”„ë ˆìž„ ë³€í™˜ ì‹œ ì—ëŸ¬ ì²˜ë¦¬
        try:
            # ì‚¬ìš©ìž ë°ì´í„°í”„ë ˆìž„ ìƒì„± (manager_auth íŽ˜ì´ì§€ì™€ ë™ì¼í•œ ë°ì´í„° ì‚¬ìš©)
            admin_df = pd.DataFrame(st.session_state.admin_users)
        except Exception as e:
            st.error(f"ê´€ë¦¬ìž ë°ì´í„° ë¡œë“œ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
            # ë°ì´í„° êµ¬ì¡° ì˜¤ë¥˜ ì‹œ ìž¬ì„¤ì •
            st.session_state.admin_users = {
                "ì•„ì´ë””": ["admin"],
                "ì´ë¦„": ["ê´€ë¦¬ìž"],
                "ê¶Œí•œ": ["ê´€ë¦¬ìž"],
                "ë¶€ì„œ": ["ê´€ë¦¬ë¶€"],
                "ìµœê·¼ì ‘ì†ì¼": [datetime.now().strftime("%Y-%m-%d %H:%M")],
                "ìƒíƒœ": ["í™œì„±"]
            }
            admin_df = pd.DataFrame(st.session_state.admin_users)
            save_admin_data(st.session_state.admin_users)
            st.warning("ê´€ë¦¬ìž ë°ì´í„°ê°€ ìž¬ì„¤ì •ë˜ì—ˆìŠµë‹ˆë‹¤.")
        
        # ê´€ë¦¬ìž ëª©ë¡ í•„í„°ë§
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("ë¶€ì„œ í•„í„°", options=["ì „ì²´", "ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"])
        with col2:
            status_filter = st.selectbox("ìƒíƒœ í•„í„°", options=["ì „ì²´", "í™œì„±", "ë¹„í™œì„±"])
        
        # í•„í„° ì ìš©
        filtered_df = admin_df.copy()
        if dept_filter != "ì „ì²´" and not filtered_df.empty and "ë¶€ì„œ" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["ë¶€ì„œ"] == dept_filter]
        if status_filter != "ì „ì²´" and not filtered_df.empty and "ìƒíƒœ" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["ìƒíƒœ"] == status_filter]
        
        # í•„í„°ë§ëœ ê´€ë¦¬ìž ëª©ë¡ í‘œì‹œ
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # ê´€ë¦¬ìž ì‚­ì œ ì„¹ì…˜ (ê´€ë¦¬ìžê°€ ìžˆì„ ê²½ìš°ì—ë§Œ í‘œì‹œ)
        if not filtered_df.empty:
            st.subheader("ê´€ë¦¬ìž ì‚­ì œ")
            delete_cols = st.columns([3, 2])
            with delete_cols[0]:
                admin_to_delete = st.selectbox(
                    "ì‚­ì œí•  ê´€ë¦¬ìž ì„ íƒ",
                    options=filtered_df["ì•„ì´ë””"].tolist(),
                    format_func=lambda x: f"{x} ({filtered_df[filtered_df['ì•„ì´ë””'] == x]['ì´ë¦„'].values[0]})"
                )
            with delete_cols[1]:
                delete_confirm = st.checkbox("ì‚­ì œë¥¼ í™•ì¸í•©ë‹ˆë‹¤")
                
            if st.button("ê´€ë¦¬ìž ì‚­ì œ", type="primary", disabled=not delete_confirm):
                if delete_confirm:
                    # ì„¸ì…˜ ìƒíƒœì—ì„œ ê´€ë¦¬ìž ì‚­ì œ
                    idx = st.session_state.admin_users["ì•„ì´ë””"].index(admin_to_delete)
                    deleted_name = st.session_state.admin_users["ì´ë¦„"][idx]
                    
                    # ê´€ë¦¬ìž ì‚­ì œ
                    for key in st.session_state.admin_users:
                        st.session_state.admin_users[key].pop(idx)
                    
                    # íŒŒì¼ì— ì €ìž¥
                    save_admin_data(st.session_state.admin_users)
                    
                    # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼ - íŽ˜ì´ì§€ ë¦¬ë¡œë“œ ì „ì— í‘œì‹œ
                    st.warning(f"ê´€ë¦¬ìž '{admin_to_delete}'ê°€ ì‹œìŠ¤í…œì—ì„œ ì‚­ì œë˜ì—ˆìŠµë‹ˆë‹¤.")
                    time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                    st.toast(f"ðŸ—‘ï¸ {deleted_name} ê´€ë¦¬ìžê°€ ì‚­ì œë˜ì—ˆìŠµë‹ˆë‹¤", icon="ðŸ”´")
                    
                    # ì‚­ì œ íš¨ê³¼ë¥¼ ìœ„í•œ í”Œëž˜ê·¸ ì„¤ì •
                    if 'deleted_admin' not in st.session_state:
                        st.session_state.deleted_admin = True
                    
                    # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                    st.experimental_rerun()
                else:
                    st.error("ì‚­ì œë¥¼ í™•ì¸í•´ì£¼ì„¸ìš”.")
        
        # ì‚­ì œ íš¨ê³¼ í‘œì‹œ
        if 'deleted_admin' in st.session_state and st.session_state.deleted_admin:
            st.session_state.deleted_admin = False
            st.snow()  # ì‚­ì œ ìž„íŒ©íŠ¸ íš¨ê³¼
        
        # êµ¬ë¶„ì„ 
        st.markdown("---")
        
        # ìƒˆ ì‚¬ìš©ìž ë“±ë¡ í¼
        st.subheader("ì‹ ê·œ ê´€ë¦¬ìž ì¶”ê°€")
        
        # í¼ ìž…ë ¥ê°’ ì´ˆê¸°í™”ë¥¼ ìœ„í•œ ì„¸ì…˜ ìƒíƒœ ì´ˆê¸°í™”
        if 'new_user_id' not in st.session_state:
            st.session_state.new_user_id = ""
        if 'new_user_name' not in st.session_state:
            st.session_state.new_user_name = ""
        if 'new_user_password' not in st.session_state:
            st.session_state.new_user_password = ""
        if 'new_user_password_confirm' not in st.session_state:
            st.session_state.new_user_password_confirm = ""
        if 'new_user_dept' not in st.session_state:
            st.session_state.new_user_dept = "ê´€ë¦¬ë¶€"
        if 'new_user_role' not in st.session_state:
            st.session_state.new_user_role = "ì¼ë°˜"
            
        with st.form("new_user_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("ì•„ì´ë””", value=st.session_state.new_user_id, key="input_user_id")
                new_user_name = st.text_input("ì´ë¦„", value=st.session_state.new_user_name, key="input_user_name")
                new_user_dept = st.selectbox("ë¶€ì„œ", options=["ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"], index=["ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"].index(st.session_state.new_user_dept) if st.session_state.new_user_dept in ["ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"] else 0, key="input_user_dept")
            with col2:
                new_user_password = st.text_input("ë¹„ë°€ë²ˆí˜¸", type="password", value=st.session_state.new_user_password, key="input_user_pwd")
                new_user_password_confirm = st.text_input("ë¹„ë°€ë²ˆí˜¸ í™•ì¸", type="password", value=st.session_state.new_user_password_confirm, key="input_user_pwd_confirm")
                new_user_role = st.selectbox("ê¶Œí•œ", options=["ì¼ë°˜", "ê´€ë¦¬ìž"], index=["ì¼ë°˜", "ê´€ë¦¬ìž"].index(st.session_state.new_user_role) if st.session_state.new_user_role in ["ì¼ë°˜", "ê´€ë¦¬ìž"] else 0, key="input_user_role")
            
            submit_user = st.form_submit_button("ê´€ë¦¬ìž ì¶”ê°€")
        
        if submit_user:
            if not new_user_id or not new_user_name or not new_user_password:
                st.error("í•„ìˆ˜ í•­ëª©ì„ ëª¨ë‘ ìž…ë ¥í•˜ì„¸ìš”.")
            elif new_user_password != new_user_password_confirm:
                st.error("ë¹„ë°€ë²ˆí˜¸ê°€ ì¼ì¹˜í•˜ì§€ ì•ŠìŠµë‹ˆë‹¤.")
            elif new_user_id in st.session_state.admin_users["ì•„ì´ë””"]:
                st.error("ì´ë¯¸ ì¡´ìž¬í•˜ëŠ” ì•„ì´ë””ìž…ë‹ˆë‹¤.")
            else:
                # ì„¸ì…˜ ìƒíƒœì— ìƒˆ ê´€ë¦¬ìž ì¶”ê°€
                st.session_state.admin_users["ì•„ì´ë””"].append(new_user_id)
                st.session_state.admin_users["ì´ë¦„"].append(new_user_name)
                st.session_state.admin_users["ê¶Œí•œ"].append(new_user_role)
                st.session_state.admin_users["ë¶€ì„œ"].append(new_user_dept)
                st.session_state.admin_users["ìµœê·¼ì ‘ì†ì¼"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.admin_users["ìƒíƒœ"].append("í™œì„±")
                
                # íŒŒì¼ì— ì €ìž¥
                save_admin_data(st.session_state.admin_users)
                
                # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼
                st.success(f"ê´€ë¦¬ìž '{new_user_name}'ì´(ê°€) ì„±ê³µì ìœ¼ë¡œ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤.")
                time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                
                # ì¶”ê°€ íš¨ê³¼ë¥¼ ìœ„í•œ í”Œëž˜ê·¸ ì„¤ì •
                if 'added_admin' not in st.session_state:
                    st.session_state.added_admin = True
                
                # í¼ ìž…ë ¥ê°’ ë¦¬ì…‹ì„ ìœ„í•œ ì„¸ì…˜ ìƒíƒœ ì„¤ì •
                st.session_state.new_user_id = ""
                st.session_state.new_user_name = ""
                st.session_state.new_user_password = ""
                st.session_state.new_user_password_confirm = ""
                
                # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                st.experimental_rerun()
        
        # ì¶”ê°€ íš¨ê³¼ í‘œì‹œ
        if 'added_admin' in st.session_state and st.session_state.added_admin:
            st.session_state.added_admin = False
            st.balloons()  # í’ì„  íš¨ê³¼ ì¶”ê°€

    with tab2:
        # ê¶Œí•œ ì„¤ì • ì„¹ì…˜
        st.subheader("ì‚¬ìš©ìž ê¶Œí•œ ì„¤ì •")
        
        if users_df.empty:
            st.info("ë“±ë¡ëœ ê´€ë¦¬ìžê°€ ì—†ìŠµë‹ˆë‹¤. ë¨¼ì € ê´€ë¦¬ìžë¥¼ ë“±ë¡í•´ì£¼ì„¸ìš”.")
        else:
            # ê¶Œí•œ ì„¤ì •í•  ì‚¬ìš©ìž ì„ íƒ
            selected_user = st.selectbox(
                "ê¶Œí•œì„ ì„¤ì •í•  ì‚¬ìš©ìž ì„ íƒ",
                options=users_df["ì•„ì´ë””"].tolist(),
                format_func=lambda x: f"{x} ({users_df[users_df['ì•„ì´ë””'] == x]['ì´ë¦„'].values[0]})"
            )
            
            # ì„ íƒëœ ì‚¬ìš©ìžì˜ ì •ë³´ í‘œì‹œ
            user_info = users_df[users_df["ì•„ì´ë””"] == selected_user].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("í˜„ìž¬ ê¶Œí•œ", user_info["ê¶Œí•œ"])
            with col2:
                st.metric("ì†Œì† ë¶€ì„œ", user_info["ë¶€ì„œ"])
            with col3:
                st.metric("ê³„ì • ìƒíƒœ", user_info["ìƒíƒœ"])
            
            # ê¶Œí•œ ì„¤ì • ì˜µì…˜
            st.subheader("ê¶Œí•œ ì„¤ì •")
            
            col1, col2 = st.columns(2)
            with col1:
                new_role = st.radio("ê¶Œí•œ", options=["ì¼ë°˜", "ê´€ë¦¬ìž"], index=0 if user_info["ê¶Œí•œ"] == "ì¼ë°˜" else 1)
            with col2:
                new_status = st.radio("ìƒíƒœ", options=["í™œì„±", "ë¹„í™œì„±"], index=0 if user_info["ìƒíƒœ"] == "í™œì„±" else 1)
            
            # ë©”ë‰´ë³„ ì ‘ê·¼ ê¶Œí•œ
            st.subheader("ë©”ë‰´ë³„ ì ‘ê·¼ ê¶Œí•œ")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**ê´€ë¦¬ìž ë©”ë‰´**")
                admin_auth = {
                    "ì‚¬ìš©ìž ê´€ë¦¬": st.checkbox("ì‚¬ìš©ìž ê´€ë¦¬", value=user_info["ê¶Œí•œ"] == "ê´€ë¦¬ìž"),
                    "ê³µì • ê´€ë¦¬": st.checkbox("ê³µì • ê´€ë¦¬", value=user_info["ê¶Œí•œ"] == "ê´€ë¦¬ìž"),
                    "ê²€ì‚¬ ê´€ë¦¬": st.checkbox("ê²€ì‚¬ ê´€ë¦¬", value=True),
                    "ì‹œìŠ¤í…œ ì„¤ì •": st.checkbox("ì‹œìŠ¤í…œ ì„¤ì •", value=user_info["ê¶Œí•œ"] == "ê´€ë¦¬ìž")
                }
            
            with col2:
                st.markdown("**ë¦¬í¬íŠ¸ ë©”ë‰´**")
                report_auth = {
                    "ì¢…í•© ëŒ€ì‹œë³´ë“œ": st.checkbox("ì¢…í•© ëŒ€ì‹œë³´ë“œ", value=True),
                    "ì¼ê°„ ë¦¬í¬íŠ¸": st.checkbox("ì¼ê°„ ë¦¬í¬íŠ¸", value=True),
                    "ì£¼ê°„ ë¦¬í¬íŠ¸": st.checkbox("ì£¼ê°„ ë¦¬í¬íŠ¸", value=True),
                    "ì›”ê°„ ë¦¬í¬íŠ¸": st.checkbox("ì›”ê°„ ë¦¬í¬íŠ¸", value=user_info["ê¶Œí•œ"] == "ê´€ë¦¬ìž")
                }
            
            # ê¶Œí•œ ì €ìž¥ ë²„íŠ¼
            if st.button("ê¶Œí•œ ì„¤ì • ì €ìž¥"):
                # ì„¸ì…˜ ìƒíƒœì—ì„œ í•´ë‹¹ ì‚¬ìš©ìžì˜ ê¶Œí•œê³¼ ìƒíƒœ ì—…ë°ì´íŠ¸
                idx = st.session_state.admin_users["ì•„ì´ë””"].index(selected_user)
                user_name = st.session_state.admin_users["ì´ë¦„"][idx]
                old_role = st.session_state.admin_users["ê¶Œí•œ"][idx]  # ì´ì „ ê¶Œí•œ ì €ìž¥
                
                # ê¶Œí•œê³¼ ìƒíƒœ ì—…ë°ì´íŠ¸
                st.session_state.admin_users["ê¶Œí•œ"][idx] = new_role
                st.session_state.admin_users["ìƒíƒœ"][idx] = new_status
                
                # íŒŒì¼ì— ì €ìž¥
                save_admin_data(st.session_state.admin_users)
                
                # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼
                st.success(f"ì‚¬ìš©ìž '{selected_user}'ì˜ ê¶Œí•œì´ ì„±ê³µì ìœ¼ë¡œ ì—…ë°ì´íŠ¸ë˜ì—ˆìŠµë‹ˆë‹¤.")
                time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                
                # ì—…ë°ì´íŠ¸ì— ë”°ë¥¸ ë©”ì‹œì§€ ì»¤ìŠ¤í„°ë§ˆì´ì§•
                message = f"âœ… {user_name}ë‹˜ì˜ "
                if old_role != new_role:
                    message += f"ê¶Œí•œì´ {old_role}ì—ì„œ {new_role}ë¡œ ë³€ê²½ë˜ì—ˆìŠµë‹ˆë‹¤"
                else:
                    message += f"ìƒíƒœê°€ ì—…ë°ì´íŠ¸ë˜ì—ˆìŠµë‹ˆë‹¤"
                
                st.toast(message, icon="ðŸ”µ")
                
                # ê¶Œí•œ ì„¤ì • íš¨ê³¼ë¥¼ ìœ„í•œ í”Œëž˜ê·¸ ì„¤ì •
                if 'updated_admin' not in st.session_state:
                    st.session_state.updated_admin = True
                
                # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                st.experimental_rerun()
                
        # ê¶Œí•œ ì„¤ì • íš¨ê³¼ í‘œì‹œ
        if 'updated_admin' in st.session_state and st.session_state.updated_admin:
            st.session_state.updated_admin = False
            st.success("âœ¨ ê¶Œí•œ ì„¤ì •ì´ ì„±ê³µì ìœ¼ë¡œ ì ìš©ë˜ì—ˆìŠµë‹ˆë‹¤!")

elif st.session_state.page == "process_auth":
    # ê´€ë¦¬ìž ë“±ë¡ ë° ê´€ë¦¬ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>âš™ï¸ ê´€ë¦¬ìž ë“±ë¡ ë° ê´€ë¦¬</h1></div>", unsafe_allow_html=True)
    
    # ê´€ë¦¬ìž ê¶Œí•œ í™•ì¸
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ì´ íŽ˜ì´ì§€ëŠ” ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆìŠµë‹ˆë‹¤.")
        st.stop()
    
    # íƒ­ êµ¬ì„±
    tab1, tab2 = st.tabs(["ðŸ“‹ ê´€ë¦¬ìž ëª©ë¡", "âž• ê´€ë¦¬ìž ë“±ë¡"])
    
    with tab1:
        # ê´€ë¦¬ìž ëª©ë¡ ì„¹ì…˜
        st.subheader("ë“±ë¡ëœ ê´€ë¦¬ìž ëª©ë¡")
        
        # ì„¸ì…˜ ìƒíƒœì— ê´€ë¦¬ìž ëª©ë¡ ì´ˆê¸°í™” (ì²˜ìŒ ì ‘ì† ì‹œì—ë§Œ)
        if 'admin_users' not in st.session_state:
            # JSON íŒŒì¼ì—ì„œ ê´€ë¦¬ìž ë°ì´í„° ë¡œë“œ
            st.session_state.admin_users = load_admin_data()
        
        # ì‚¬ìš©ìž ë°ì´í„°í”„ë ˆìž„ ìƒì„± (manager_auth íŽ˜ì´ì§€ì™€ ë™ì¼í•œ ë°ì´í„° ì‚¬ìš©)
        admin_df = pd.DataFrame(st.session_state.admin_users)
        
        # ê´€ë¦¬ìž ëª©ë¡ í•„í„°ë§
        col1, col2 = st.columns(2)
        with col1:
            dept_filter = st.selectbox("ë¶€ì„œ í•„í„°", options=["ì „ì²´", "ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"])
        with col2:
            status_filter = st.selectbox("ìƒíƒœ í•„í„°", options=["ì „ì²´", "í™œì„±", "ë¹„í™œì„±"])
        
        # í•„í„° ì ìš©
        filtered_df = admin_df.copy()
        if dept_filter != "ì „ì²´" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["ë¶€ì„œ"] == dept_filter]
        if status_filter != "ì „ì²´" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["ìƒíƒœ"] == status_filter]
        
        # í•„í„°ë§ëœ ê´€ë¦¬ìž ëª©ë¡ í‘œì‹œ
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
        
        # ì„ íƒí•œ ê´€ë¦¬ìž ìƒì„¸ ì •ë³´ ë° ê¶Œí•œ ê´€ë¦¬
        selected_admin = st.selectbox(
            "ìƒì„¸ ì •ë³´ë¥¼ ë³¼ ê´€ë¦¬ìž ì„ íƒ",
            options=filtered_df["ì•„ì´ë””"].tolist(),
            format_func=lambda x: f"{x} ({filtered_df[filtered_df['ì•„ì´ë””'] == x]['ì´ë¦„'].values[0]})"
        )
        
        if selected_admin:
            st.subheader(f"ê´€ë¦¬ìž ìƒì„¸ ì •ë³´: {selected_admin}")
            
            # ì„ íƒëœ ê´€ë¦¬ìž ì •ë³´
            admin_info = filtered_df[filtered_df["ì•„ì´ë””"] == selected_admin].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ì´ë¦„", admin_info["ì´ë¦„"])
                st.metric("ê¶Œí•œ", admin_info["ê¶Œí•œ"])
            with col2:
                st.metric("ë¶€ì„œ", admin_info["ë¶€ì„œ"])
                st.metric("ìƒíƒœ", admin_info["ìƒíƒœ"])
            with col3:
                st.metric("ìµœê·¼ì ‘ì†ì¼", admin_info["ìµœê·¼ì ‘ì†ì¼"])
            
            # ê³„ì • í™œì„±í™”/ë¹„í™œì„±í™” ë²„íŠ¼
            col1, col2 = st.columns(2)
            with col1:
                if admin_info["ìƒíƒœ"] == "í™œì„±":
                    if st.button(f"'{admin_info['ì´ë¦„']}' ê³„ì • ë¹„í™œì„±í™”", key="deactivate_admin"):
                        # ì„¸ì…˜ ìƒíƒœì—ì„œ í•´ë‹¹ ê´€ë¦¬ìžì˜ ìƒíƒœ ì—…ë°ì´íŠ¸
                        idx = st.session_state.admin_users["ì•„ì´ë””"].index(selected_admin)
                        st.session_state.admin_users["ìƒíƒœ"][idx] = "ë¹„í™œì„±"
                        
                        # íŒŒì¼ì— ì €ìž¥
                        save_admin_data(st.session_state.admin_users)
                        
                        st.warning(f"'{admin_info['ì´ë¦„']}' ê³„ì •ì´ ë¹„í™œì„±í™”ë˜ì—ˆìŠµë‹ˆë‹¤.")
                        time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                        st.experimental_rerun()
                else:
                    if st.button(f"'{admin_info['ì´ë¦„']}' ê³„ì • í™œì„±í™”", key="activate_admin"):
                        # ì„¸ì…˜ ìƒíƒœì—ì„œ í•´ë‹¹ ê´€ë¦¬ìžì˜ ìƒíƒœ ì—…ë°ì´íŠ¸
                        idx = st.session_state.admin_users["ì•„ì´ë””"].index(selected_admin)
                        st.session_state.admin_users["ìƒíƒœ"][idx] = "í™œì„±"
                        
                        # íŒŒì¼ì— ì €ìž¥
                        save_admin_data(st.session_state.admin_users)
                        
                        st.success(f"'{admin_info['ì´ë¦„']}' ê³„ì •ì´ í™œì„±í™”ë˜ì—ˆìŠµë‹ˆë‹¤.")
                        time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                        st.experimental_rerun()
            
            with col2:
                if st.button(f"'{admin_info['ì´ë¦„']}' ë¹„ë°€ë²ˆí˜¸ ì´ˆê¸°í™”", key="reset_admin_pwd"):
                    st.success(f"'{admin_info['ì´ë¦„']}' ê³„ì •ì˜ ë¹„ë°€ë²ˆí˜¸ê°€ ì´ˆê¸°í™”ë˜ì—ˆìŠµë‹ˆë‹¤.")
                    st.code("ìž„ì‹œ ë¹„ë°€ë²ˆí˜¸: Admin@1234")
            
            # ê¶Œí•œ ë³€ê²½
            st.subheader("ê¶Œí•œ ë³€ê²½")
            new_role = st.radio(
                "ê¶Œí•œ ì„ íƒ",
                options=["ì¼ë°˜", "ê´€ë¦¬ìž"],
                index=0 if admin_info["ê¶Œí•œ"] == "ì¼ë°˜" else 1
            )
            
            if st.button("ê¶Œí•œ ë³€ê²½ ì €ìž¥"):
                # ì„¸ì…˜ ìƒíƒœì—ì„œ í•´ë‹¹ ê´€ë¦¬ìžì˜ ê¶Œí•œ ì—…ë°ì´íŠ¸
                idx = st.session_state.admin_users["ì•„ì´ë””"].index(selected_admin)
                user_name = st.session_state.admin_users["ì´ë¦„"][idx]
                old_role = st.session_state.admin_users["ê¶Œí•œ"][idx]  # ì´ì „ ê¶Œí•œ ì €ìž¥
                
                # ê¶Œí•œ ì—…ë°ì´íŠ¸
                st.session_state.admin_users["ê¶Œí•œ"][idx] = new_role
                
                # íŒŒì¼ì— ì €ìž¥
                save_admin_data(st.session_state.admin_users)
                
                # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼
                st.success(f"ê´€ë¦¬ìž '{selected_admin}'ì˜ ê¶Œí•œì´ ì„±ê³µì ìœ¼ë¡œ ë³€ê²½ë˜ì—ˆìŠµë‹ˆë‹¤.")
                time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                
                # ì—…ë°ì´íŠ¸ì— ë”°ë¥¸ ë©”ì‹œì§€ ì»¤ìŠ¤í„°ë§ˆì´ì§•
                if old_role != new_role:
                    message = f"âœ… {user_name}ë‹˜ì˜ ê¶Œí•œì´ {old_role}ì—ì„œ {new_role}ë¡œ ë³€ê²½ë˜ì—ˆìŠµë‹ˆë‹¤"
                    st.toast(message, icon="ðŸ”µ")
                
                # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                st.experimental_rerun()
    
    with tab2:
        # ê´€ë¦¬ìž ë“±ë¡ ì„¹ì…˜
        st.subheader("ìƒˆ ê´€ë¦¬ìž ë“±ë¡")
        
        # í¼ ìž…ë ¥ê°’ ì´ˆê¸°í™”ë¥¼ ìœ„í•œ ì„¸ì…˜ ìƒíƒœ ì´ˆê¸°í™”
        if 'new_admin_id' not in st.session_state:
            st.session_state.new_admin_id = ""
        if 'new_admin_name' not in st.session_state:
            st.session_state.new_admin_name = ""
        if 'new_admin_password' not in st.session_state:
            st.session_state.new_admin_password = ""
        if 'new_admin_password_confirm' not in st.session_state:
            st.session_state.new_admin_password_confirm = ""
        if 'new_admin_dept' not in st.session_state:
            st.session_state.new_admin_dept = "ê´€ë¦¬ë¶€"
        
        with st.form("new_admin_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_admin_id = st.text_input("ì•„ì´ë””", value=st.session_state.new_admin_id)
                new_admin_name = st.text_input("ì´ë¦„", value=st.session_state.new_admin_name)
                new_admin_dept = st.selectbox("ë¶€ì„œ", options=["ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"], index=["ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"].index(st.session_state.new_admin_dept) if st.session_state.new_admin_dept in ["ê´€ë¦¬ë¶€", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€"] else 0)
            with col2:
                new_admin_pwd = st.text_input("ë¹„ë°€ë²ˆí˜¸", type="password", value=st.session_state.new_admin_password)
                new_admin_pwd_confirm = st.text_input("ë¹„ë°€ë²ˆí˜¸ í™•ì¸", type="password", value=st.session_state.new_admin_password_confirm)
                new_admin_role = st.selectbox("ê¶Œí•œ", options=["ì¼ë°˜", "ê´€ë¦¬ìž"], index=0)
            
            submit_admin = st.form_submit_button("ê´€ë¦¬ìž ë“±ë¡")
        
        if submit_admin:
            if not new_admin_id or not new_admin_name or not new_admin_pwd:
                st.error("í•„ìˆ˜ í•­ëª©ì„ ëª¨ë‘ ìž…ë ¥í•˜ì„¸ìš”.")
            elif new_admin_pwd != new_admin_pwd_confirm:
                st.error("ë¹„ë°€ë²ˆí˜¸ê°€ ì¼ì¹˜í•˜ì§€ ì•ŠìŠµë‹ˆë‹¤.")
            elif new_admin_id in st.session_state.admin_users["ì•„ì´ë””"]:
                st.error("ì´ë¯¸ ì¡´ìž¬í•˜ëŠ” ì•„ì´ë””ìž…ë‹ˆë‹¤.")
            else:
                # ì„¸ì…˜ ìƒíƒœì— ìƒˆ ê´€ë¦¬ìž ì¶”ê°€
                st.session_state.admin_users["ì•„ì´ë””"].append(new_admin_id)
                st.session_state.admin_users["ì´ë¦„"].append(new_admin_name)
                st.session_state.admin_users["ê¶Œí•œ"].append(new_admin_role)
                st.session_state.admin_users["ë¶€ì„œ"].append(new_admin_dept)
                st.session_state.admin_users["ìµœê·¼ì ‘ì†ì¼"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.admin_users["ìƒíƒœ"].append("í™œì„±")
                
                # íŒŒì¼ì— ì €ìž¥
                save_admin_data(st.session_state.admin_users)
                
                # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼
                st.success(f"ê´€ë¦¬ìž '{new_admin_name}'ì´(ê°€) ì„±ê³µì ìœ¼ë¡œ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤.")
                time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                
                # ì¶”ê°€ íš¨ê³¼ë¥¼ ìœ„í•œ í”Œëž˜ê·¸ ì„¤ì •
                if 'added_admin' not in st.session_state:
                    st.session_state.added_admin = True
                
                # í¼ ìž…ë ¥ê°’ ë¦¬ì…‹ì„ ìœ„í•œ ì„¸ì…˜ ìƒíƒœ ì„¤ì •
                st.session_state.new_admin_id = ""
                st.session_state.new_admin_name = ""
                st.session_state.new_admin_password = ""
                st.session_state.new_admin_password_confirm = ""
                
                # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                st.experimental_rerun()
        
        # ì¶”ê°€ íš¨ê³¼ í‘œì‹œ
        if 'added_admin' in st.session_state and st.session_state.added_admin:
            st.session_state.added_admin = False
            st.balloons()  # í’ì„  íš¨ê³¼ ì¶”ê°€

elif st.session_state.page == "user_auth":
    # ê²€ì‚¬ìž ë“±ë¡ ë° ê´€ë¦¬ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ”‘ ê²€ì‚¬ìž ë“±ë¡ ë° ê´€ë¦¬</h1></div>", unsafe_allow_html=True)
    
    # ê´€ë¦¬ìž ê¶Œí•œ í™•ì¸
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ì´ íŽ˜ì´ì§€ëŠ” ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆìŠµë‹ˆë‹¤.")
        st.stop()
    
    # íƒ­ êµ¬ì„±
    tab1, tab2, tab3 = st.tabs(["ðŸ‘¥ ê²€ì‚¬ìž ëª©ë¡", "âž• ì‹ ê·œ ê²€ì‚¬ìž ë“±ë¡", "ðŸ“Š ê²€ì‚¬ìž í†µê³„"])
    
    with tab1:
        # ì‚¬ìš©ìž ëª©ë¡ ì„¹ì…˜
        st.subheader("ë“±ë¡ëœ ê²€ì‚¬ìž ëª©ë¡")
        
        try:
            # ì„¸ì…˜ ìƒíƒœì— ì‚¬ìš©ìž ëª©ë¡ ì´ˆê¸°í™” (ì²˜ìŒ ì ‘ì† ì‹œì—ë§Œ)
            if 'user_data' not in st.session_state:
                # JSON íŒŒì¼ì—ì„œ ì‚¬ìš©ìž ë°ì´í„° ë¡œë“œ
                st.session_state.user_data = load_user_data()
            
            # ì‚¬ìš©ìž ë°ì´í„°ê°€ ì˜¬ë°”ë¥¸ í˜•ì‹ì¸ì§€ í™•ì¸
            if not isinstance(st.session_state.user_data, dict) or "ì•„ì´ë””" not in st.session_state.user_data:
                # ìž˜ëª»ëœ í˜•ì‹ì˜ ë°ì´í„°ì¸ ê²½ìš° ì´ˆê¸°í™”
                st.session_state.user_data = load_user_data()
                st.warning("ì‚¬ìš©ìž ë°ì´í„°ê°€ ì˜¬ë°”ë¥¸ í˜•ì‹ì´ ì•„ë‹™ë‹ˆë‹¤. ë°ì´í„°ë¥¼ ìž¬ì„¤ì •í–ˆìŠµë‹ˆë‹¤.")
            
            # ì‚¬ìš©ìž ë°ì´í„°í”„ë ˆìž„ ìƒì„±
            user_df = pd.DataFrame(st.session_state.user_data)
            
            # DataFrameì´ ë¹„ì–´ìžˆëŠ” ê²½ìš° ë¹ˆ DataFrameì„ ë§Œë“¤ì–´ì£¼ê¸°
            if user_df.empty:
                user_df = pd.DataFrame({
                    "ì•„ì´ë””": [],
                    "ì´ë¦„": [],
                    "ë¶€ì„œ": [],
                    "ì§ê¸‰": [],
                    "ê³µì •": [],
                    "ê³„ì •ìƒì„±ì¼": [],
                    "ìµœê·¼ì ‘ì†ì¼": [],
                    "ìƒíƒœ": []
                })
        
        except Exception as e:
            st.error(f"ì‚¬ìš©ìž ë°ì´í„°ë¥¼ ë¶ˆëŸ¬ì˜¤ëŠ”ë° ì‹¤íŒ¨í–ˆìŠµë‹ˆë‹¤: {str(e)}")
        
        # í•„í„°ë§ ì˜µì…˜
        col1, col2, col3 = st.columns(3)
        with col1:
            dept_filter = st.selectbox("ë¶€ì„œ í•„í„°", options=["ì „ì²´", "ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€", "ê´€ë¦¬ë¶€"], key="user_dept_filter")
        with col2:
            process_filter = st.selectbox("ê³µì • í•„í„°", options=["ì „ì²´", "ì„ ì‚­", "ë°€ë§", "ê²€ì‚¬", "ì„¤ê³„", "ê´€ë¦¬"], key="user_process_filter")
        with col3:
            status_filter = st.selectbox("ìƒíƒœ í•„í„°", options=["ì „ì²´", "í™œì„±", "ë¹„í™œì„±", "íœ´ë©´"], key="user_status_filter")
        
        # í•„í„° ì ìš©
        filtered_user_df = user_df.copy()
        if dept_filter != "ì „ì²´" and not filtered_user_df.empty and "ë¶€ì„œ" in filtered_user_df.columns:
            filtered_user_df = filtered_user_df[filtered_user_df["ë¶€ì„œ"] == dept_filter]
        if process_filter != "ì „ì²´" and not filtered_user_df.empty and "ê³µì •" in filtered_user_df.columns:
            filtered_user_df = filtered_user_df[filtered_user_df["ê³µì •"] == process_filter]
        if status_filter != "ì „ì²´" and not filtered_user_df.empty and "ìƒíƒœ" in filtered_user_df.columns:
            filtered_user_df = filtered_user_df[filtered_user_df["ìƒíƒœ"] == status_filter]
        
        # í•„í„°ë§ëœ ì‚¬ìš©ìž ëª©ë¡ í‘œì‹œ
        if filtered_user_df.empty:
            st.info("ë“±ë¡ëœ ê²€ì‚¬ìžê°€ ì—†ìŠµë‹ˆë‹¤. ë¨¼ì € ê²€ì‚¬ìžë¥¼ ë“±ë¡í•´ì£¼ì„¸ìš”.")
        else:
            st.dataframe(filtered_user_df, use_container_width=True, hide_index=True)
        
        # ì‚¬ìš©ìž ê²€ìƒ‰
        search_query = st.text_input("ê²€ì‚¬ìž ê²€ìƒ‰ (ì´ë¦„ ë˜ëŠ” ì•„ì´ë””)", key="user_search")
        if search_query and not user_df.empty:
            try:
                if "ì´ë¦„" in user_df.columns and "ì•„ì´ë””" in user_df.columns:
                    search_results = user_df[
                        user_df["ì´ë¦„"].str.contains(search_query) | 
                        user_df["ì•„ì´ë””"].str.contains(search_query)
                    ]
                    if not search_results.empty:
                        st.subheader("ê²€ìƒ‰ ê²°ê³¼")
                        st.dataframe(search_results, use_container_width=True, hide_index=True)
                    else:
                        st.info("ê²€ìƒ‰ ê²°ê³¼ê°€ ì—†ìŠµë‹ˆë‹¤.")
                else:
                    st.warning("ì‚¬ìš©ìž ë°ì´í„°ì— í•„ìš”í•œ ì—´ì´ ì—†ìŠµë‹ˆë‹¤.")
            except Exception as e:
                st.error(f"ê²€ìƒ‰ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
        
        # ì„ íƒí•œ ì‚¬ìš©ìž ìƒì„¸ ì •ë³´ ë° ê´€ë¦¬
        if not user_df.empty:
            try:
                if "ì•„ì´ë””" in user_df.columns:
                    selected_user_id = st.selectbox(
                        "ìƒì„¸ ì •ë³´ë¥¼ ë³¼ ê²€ì‚¬ìž ì„ íƒ",
                        options=user_df["ì•„ì´ë””"].tolist(),
                        format_func=lambda x: f"{x} ({user_df[user_df['ì•„ì´ë””'] == x]['ì´ë¦„'].values[0] if not user_df[user_df['ì•„ì´ë””'] == x].empty and 'ì´ë¦„' in user_df.columns else 'ì•Œ ìˆ˜ ì—†ìŒ'})"
                    )
                    
                    if selected_user_id:
                        st.subheader(f"ê²€ì‚¬ìž ìƒì„¸ ì •ë³´: {selected_user_id}")
                        
                        # ì„ íƒëœ ì‚¬ìš©ìž ì •ë³´
                        user_info_df = user_df[user_df["ì•„ì´ë””"] == selected_user_id]
                        if not user_info_df.empty:
                            user_info = user_info_df.iloc[0]
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("ì´ë¦„", user_info["ì´ë¦„"] if "ì´ë¦„" in user_info and pd.notna(user_info["ì´ë¦„"]) else "ì •ë³´ ì—†ìŒ")
                                st.metric("ë¶€ì„œ", user_info["ë¶€ì„œ"] if "ë¶€ì„œ" in user_info and pd.notna(user_info["ë¶€ì„œ"]) else "ì •ë³´ ì—†ìŒ")
                            with col2:
                                st.metric("ì§ê¸‰", user_info["ì§ê¸‰"] if "ì§ê¸‰" in user_info and pd.notna(user_info["ì§ê¸‰"]) else "ì •ë³´ ì—†ìŒ")
                                st.metric("ê³µì •", user_info["ê³µì •"] if "ê³µì •" in user_info and pd.notna(user_info["ê³µì •"]) else "ì •ë³´ ì—†ìŒ")
                            with col3:
                                st.metric("ê³„ì •ìƒì„±ì¼", user_info["ê³„ì •ìƒì„±ì¼"] if "ê³„ì •ìƒì„±ì¼" in user_info and pd.notna(user_info["ê³„ì •ìƒì„±ì¼"]) else "ì •ë³´ ì—†ìŒ")
                                st.metric("ìµœê·¼ì ‘ì†ì¼", user_info["ìµœê·¼ì ‘ì†ì¼"] if "ìµœê·¼ì ‘ì†ì¼" in user_info and pd.notna(user_info["ìµœê·¼ì ‘ì†ì¼"]) else "ì •ë³´ ì—†ìŒ")
                            
                            # ê³„ì • ìƒíƒœ ê´€ë¦¬
                            st.subheader("ê³„ì • ìƒíƒœ ê´€ë¦¬")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                current_status = user_info["ìƒíƒœ"] if "ìƒíƒœ" in user_info and pd.notna(user_info["ìƒíƒœ"]) else "í™œì„±"
                                new_status = st.radio(
                                    "ê³„ì • ìƒíƒœ",
                                    options=["í™œì„±", "ë¹„í™œì„±", "íœ´ë©´"],
                                    index=0 if current_status == "í™œì„±" else 
                                        1 if current_status == "ë¹„í™œì„±" else 2,
                                    key="user_status_change"
                                )
                            
                            with col2:
                                if st.button("ë¹„ë°€ë²ˆí˜¸ ì´ˆê¸°í™”", key="user_reset_pwd"):
                                    user_name = user_info["ì´ë¦„"] if "ì´ë¦„" in user_info and pd.notna(user_info["ì´ë¦„"]) else selected_user_id
                                    st.success(f"'{user_name}' ê³„ì •ì˜ ë¹„ë°€ë²ˆí˜¸ê°€ ì´ˆê¸°í™”ë˜ì—ˆìŠµë‹ˆë‹¤.")
                                    st.code("ìž„ì‹œ ë¹„ë°€ë²ˆí˜¸: User@1234")
                                
                                if st.button("ìƒíƒœ ë³€ê²½ ì €ìž¥", key="save_user_status"):
                                    try:
                                        # ì„¸ì…˜ ìƒíƒœì—ì„œ í•´ë‹¹ ì‚¬ìš©ìžì˜ ìƒíƒœ ì—…ë°ì´íŠ¸
                                        if "ì•„ì´ë””" in st.session_state.user_data and selected_user_id in st.session_state.user_data["ì•„ì´ë””"]:
                                            idx = st.session_state.user_data["ì•„ì´ë””"].index(selected_user_id)
                                            user_name = st.session_state.user_data["ì´ë¦„"][idx] if "ì´ë¦„" in st.session_state.user_data and idx < len(st.session_state.user_data["ì´ë¦„"]) else selected_user_id
                                            old_status = st.session_state.user_data["ìƒíƒœ"][idx] if "ìƒíƒœ" in st.session_state.user_data and idx < len(st.session_state.user_data["ìƒíƒœ"]) else "ì•Œ ìˆ˜ ì—†ìŒ"
                                            
                                            # ìƒíƒœ ì—…ë°ì´íŠ¸
                                            if "ìƒíƒœ" in st.session_state.user_data:
                                                if idx < len(st.session_state.user_data["ìƒíƒœ"]):
                                                    st.session_state.user_data["ìƒíƒœ"][idx] = new_status
                                                else:
                                                    # ì¸ë±ìŠ¤ê°€ ë²”ìœ„ë¥¼ ë²—ì–´ë‚˜ë©´ í•„ìš”í•œ ë§Œí¼ í™•ìž¥
                                                    st.session_state.user_data["ìƒíƒœ"].extend([None] * (idx - len(st.session_state.user_data["ìƒíƒœ"]) + 1))
                                                    st.session_state.user_data["ìƒíƒœ"][idx] = new_status
                                            else:
                                                # "ìƒíƒœ" í‚¤ê°€ ì—†ìœ¼ë©´ ìƒì„±
                                                st.session_state.user_data["ìƒíƒœ"] = ["í™œì„±"] * len(st.session_state.user_data["ì•„ì´ë””"])
                                                st.session_state.user_data["ìƒíƒœ"][idx] = new_status
                                            
                                            # íŒŒì¼ì— ì €ìž¥
                                            save_user_data(st.session_state.user_data)
                                            
                                            # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼
                                            st.success(f"ì‚¬ìš©ìž '{user_name}'ì˜ ìƒíƒœê°€ '{new_status}'ë¡œ ì„±ê³µì ìœ¼ë¡œ ë³€ê²½ë˜ì—ˆìŠµë‹ˆë‹¤.")
                                            time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                                            
                                            # ì—…ë°ì´íŠ¸ì— ë”°ë¥¸ ë©”ì‹œì§€ ì»¤ìŠ¤í„°ë§ˆì´ì§•
                                            if old_status != new_status:
                                                message = f"âœ… {user_name}ë‹˜ì˜ ìƒíƒœê°€ {old_status}ì—ì„œ {new_status}ë¡œ ë³€ê²½ë˜ì—ˆìŠµë‹ˆë‹¤"
                                                st.toast(message, icon="ðŸ”µ")
                                            
                                            # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                                            st.experimental_rerun()
                                        else:
                                            st.error("ì‚¬ìš©ìž ë°ì´í„°ì—ì„œ ì„ íƒí•œ ì‚¬ìš©ìžë¥¼ ì°¾ì„ ìˆ˜ ì—†ìŠµë‹ˆë‹¤.")
                                    except Exception as e:
                                        st.error(f"ìƒíƒœ ë³€ê²½ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
                        
                        # ì‚¬ìš©ìž ì‚­ì œ ì„¹ì…˜
                        st.subheader("ê²€ì‚¬ìž ì‚­ì œ")
                        delete_confirm = st.checkbox("ì‚­ì œë¥¼ í™•ì¸í•©ë‹ˆë‹¤", key="delete_user_confirm")
                        
                        if st.button("ê²€ì‚¬ìž ì‚­ì œ", type="primary", disabled=not delete_confirm):
                            if delete_confirm:
                                try:
                                    # ì„¸ì…˜ ìƒíƒœì—ì„œ ì‚¬ìš©ìž ì‚­ì œ
                                    idx = st.session_state.user_data["ì•„ì´ë””"].index(selected_user_id)
                                    deleted_name = st.session_state.user_data["ì´ë¦„"][idx] if "ì´ë¦„" in st.session_state.user_data and idx < len(st.session_state.user_data["ì´ë¦„"]) else selected_user_id
                                    
                                    # ì‚¬ìš©ìž ì‚­ì œ
                                    for key in st.session_state.user_data:
                                        if idx < len(st.session_state.user_data[key]):
                                            st.session_state.user_data[key].pop(idx)
                                    
                                    # íŒŒì¼ì— ì €ìž¥
                                    save_user_data(st.session_state.user_data)
                                    
                                    # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼ - íŽ˜ì´ì§€ ë¦¬ë¡œë“œ ì „ì— í‘œì‹œ
                                    st.warning(f"ê²€ì‚¬ìž '{selected_user_id}'ê°€ ì‹œìŠ¤í…œì—ì„œ ì‚­ì œë˜ì—ˆìŠµë‹ˆë‹¤.")
                                    time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                                    st.toast(f"ðŸ—‘ï¸ {deleted_name} ê²€ì‚¬ìžê°€ ì‚­ì œë˜ì—ˆìŠµë‹ˆë‹¤", icon="ðŸ”´")
                                    
                                    # ì‚­ì œ íš¨ê³¼ë¥¼ ìœ„í•œ í”Œëž˜ê·¸ ì„¤ì •
                                    if 'deleted_user' not in st.session_state:
                                        st.session_state.deleted_user = True
                                    
                                    # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                                    st.experimental_rerun()
                                except Exception as e:
                                    st.error(f"ê²€ì‚¬ìž ì‚­ì œ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
                            else:
                                st.error("ì‚­ì œë¥¼ í™•ì¸í•´ì£¼ì„¸ìš”.")
                else:
                    st.warning("ì„ íƒí•œ ê²€ì‚¬ìžì˜ ì •ë³´ë¥¼ ì°¾ì„ ìˆ˜ ì—†ìŠµë‹ˆë‹¤.")
            except Exception as e:
                st.error(f"ê²€ì‚¬ìž ì •ë³´ í‘œì‹œ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
                st.info("ê²€ì‚¬ìž ë°ì´í„°ì— ë¬¸ì œê°€ ìžˆì„ ìˆ˜ ìžˆìŠµë‹ˆë‹¤. ë°ì´í„°ë¥¼ í™•ì¸í•´ì£¼ì„¸ìš”.")
            
            # ì‚­ì œ íš¨ê³¼ í‘œì‹œ
            if 'deleted_user' in st.session_state and st.session_state.deleted_user:
                st.session_state.deleted_user = False
                st.snow()  # ì‚­ì œ ìž„íŒ©íŠ¸ íš¨ê³¼

    with tab2:
        # ì‚¬ìš©ìž ë“±ë¡ ì„¹ì…˜
        st.subheader("ì‹ ê·œ ê²€ì‚¬ìž ë“±ë¡")
        
        # í¼ ìž…ë ¥ê°’ ì´ˆê¸°í™”ë¥¼ ìœ„í•œ ì„¸ì…˜ ìƒíƒœ ì´ˆê¸°í™”
        if 'new_user_id' not in st.session_state:
            st.session_state.new_user_id = ""
        if 'new_user_name' not in st.session_state:
            st.session_state.new_user_name = ""
        if 'new_user_pwd' not in st.session_state:
            st.session_state.new_user_pwd = ""
        if 'new_user_pwd_confirm' not in st.session_state:
            st.session_state.new_user_pwd_confirm = ""
        if 'new_user_dept' not in st.session_state:
            st.session_state.new_user_dept = "ìƒì‚°ë¶€"
        if 'new_user_position' not in st.session_state:
            st.session_state.new_user_position = "ì‚¬ì›"
        if 'new_user_process' not in st.session_state:
            st.session_state.new_user_process = "ì„ ì‚­"
        
        with st.form("new_user_form_2"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("ì•„ì´ë””", value=st.session_state.new_user_id, key="new_user_id_2")
                new_user_name = st.text_input("ì´ë¦„", value=st.session_state.new_user_name, key="new_user_name_2")
                new_user_dept = st.selectbox("ë¶€ì„œ", options=["ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€", "ê´€ë¦¬ë¶€"], index=["ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€", "ê´€ë¦¬ë¶€"].index(st.session_state.new_user_dept) if st.session_state.new_user_dept in ["ìƒì‚°ë¶€", "í’ˆì§ˆë¶€", "ê¸°ìˆ ë¶€", "ê´€ë¦¬ë¶€"] else 0, key="new_user_dept_2")
            with col2:
                new_user_pwd = st.text_input("ë¹„ë°€ë²ˆí˜¸", type="password", value=st.session_state.new_user_pwd, key="new_user_pwd_2")
                new_user_pwd_confirm = st.text_input("ë¹„ë°€ë²ˆí˜¸ í™•ì¸", type="password", value=st.session_state.new_user_pwd_confirm, key="new_user_pwd_confirm_2")
                new_user_position = st.selectbox("ì§ê¸‰", options=["ì‚¬ì›", "ì£¼ìž„", "ëŒ€ë¦¬", "ê³¼ìž¥", "ë¶€ìž¥"], index=["ì‚¬ì›", "ì£¼ìž„", "ëŒ€ë¦¬", "ê³¼ìž¥", "ë¶€ìž¥"].index(st.session_state.new_user_position) if st.session_state.new_user_position in ["ì‚¬ì›", "ì£¼ìž„", "ëŒ€ë¦¬", "ê³¼ìž¥", "ë¶€ìž¥"] else 0, key="new_user_position_2")
            
            new_user_process = st.selectbox("ë‹´ë‹¹ ê³µì •", options=["ì„ ì‚­", "ë°€ë§", "ê²€ì‚¬", "ì„¤ê³„", "ê´€ë¦¬"], index=["ì„ ì‚­", "ë°€ë§", "ê²€ì‚¬", "ì„¤ê³„", "ê´€ë¦¬"].index(st.session_state.new_user_process) if st.session_state.new_user_process in ["ì„ ì‚­", "ë°€ë§", "ê²€ì‚¬", "ì„¤ê³„", "ê´€ë¦¬"] else 0, key="new_user_process_2")
            new_user_memo = st.text_area("ë©”ëª¨ (ì„ íƒì‚¬í•­)", max_chars=200, key="new_user_memo_2")
            
            submit_user = st.form_submit_button("ê²€ì‚¬ìž ë“±ë¡")
        
        if submit_user:
            if not new_user_id or not new_user_name or not new_user_pwd:
                st.error("í•„ìˆ˜ í•­ëª©ì„ ëª¨ë‘ ìž…ë ¥í•˜ì„¸ìš”.")
            elif new_user_pwd != new_user_pwd_confirm:
                st.error("ë¹„ë°€ë²ˆí˜¸ê°€ ì¼ì¹˜í•˜ì§€ ì•ŠìŠµë‹ˆë‹¤.")
            elif 'user_data' in st.session_state and "ì•„ì´ë””" in st.session_state.user_data and new_user_id in st.session_state.user_data["ì•„ì´ë””"]:
                st.error("ì´ë¯¸ ì¡´ìž¬í•˜ëŠ” ì•„ì´ë””ìž…ë‹ˆë‹¤.")
            else:
                # ì„¸ì…˜ ìƒíƒœì— ìƒˆ ì‚¬ìš©ìž ì¶”ê°€
                if 'user_data' not in st.session_state:
                    st.session_state.user_data = load_user_data()
                
                # í•„ìˆ˜ í‚¤ í™•ì¸
                required_keys = ["ì•„ì´ë””", "ì´ë¦„", "ë¶€ì„œ", "ì§ê¸‰", "ê³µì •", "ê³„ì •ìƒì„±ì¼", "ìµœê·¼ì ‘ì†ì¼", "ìƒíƒœ"]
                for key in required_keys:
                    if key not in st.session_state.user_data:
                        st.session_state.user_data[key] = []
                
                st.session_state.user_data["ì•„ì´ë””"].append(new_user_id)
                st.session_state.user_data["ì´ë¦„"].append(new_user_name)
                st.session_state.user_data["ë¶€ì„œ"].append(new_user_dept)
                st.session_state.user_data["ì§ê¸‰"].append(new_user_position)
                st.session_state.user_data["ê³µì •"].append(new_user_process)
                st.session_state.user_data["ê³„ì •ìƒì„±ì¼"].append(datetime.now().strftime("%Y-%m-%d"))
                st.session_state.user_data["ìµœê·¼ì ‘ì†ì¼"].append(datetime.now().strftime("%Y-%m-%d %H:%M"))
                st.session_state.user_data["ìƒíƒœ"].append("í™œì„±")
                
                # íŒŒì¼ì— ì €ìž¥
                save_user_data(st.session_state.user_data)
                
                # ì„±ê³µ ë©”ì‹œì§€ ë° ì‹œê°ì  íš¨ê³¼
                st.success(f"ì‚¬ìš©ìž '{new_user_name}'ì´(ê°€) ì„±ê³µì ìœ¼ë¡œ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤.")
                time.sleep(0.5)  # íš¨ê³¼ë¥¼ ë³¼ ìˆ˜ ìžˆë„ë¡ ì§§ì€ ëŒ€ê¸°ì‹œê°„ ì¶”ê°€
                
                # ì¶”ê°€ íš¨ê³¼ë¥¼ ìœ„í•œ í”Œëž˜ê·¸ ì„¤ì •
                if 'added_user' not in st.session_state:
                    st.session_state.added_user = True
                
                # í¼ ìž…ë ¥ê°’ ë¦¬ì…‹ì„ ìœ„í•œ ì„¸ì…˜ ìƒíƒœ ì„¤ì •
                st.session_state.new_user_id = ""
                st.session_state.new_user_name = ""
                st.session_state.new_user_pwd = ""
                st.session_state.new_user_pwd_confirm = ""
                
                # íŽ˜ì´ì§€ ë¦¬ë¡œë“œ
                st.experimental_rerun()
        
        # ì¶”ê°€ íš¨ê³¼ í‘œì‹œ
        if 'added_user' in st.session_state and st.session_state.added_user:
            st.session_state.added_user = False
            st.balloons()  # í’ì„  íš¨ê³¼ ì¶”ê°€
    
    with tab3:
        # ì‚¬ìš© í†µê³„ ì„¹ì…˜
        st.subheader("ê²€ì‚¬ìž í†µê³„")
        
        if 'user_data' not in st.session_state or not isinstance(st.session_state.user_data, dict) or "ì•„ì´ë””" not in st.session_state.user_data or len(st.session_state.user_data["ì•„ì´ë””"]) == 0:
            st.info("ë“±ë¡ëœ ì‚¬ìš©ìžê°€ ì—†ìŠµë‹ˆë‹¤. í†µê³„ë¥¼ í‘œì‹œí•˜ë ¤ë©´ ì‚¬ìš©ìžë¥¼ ë“±ë¡í•´ì£¼ì„¸ìš”.")
        else:
            user_df = pd.DataFrame(st.session_state.user_data)
            
            try:
                # ë¶€ì„œë³„ ì‚¬ìš©ìž ë¶„í¬
                if "ë¶€ì„œ" in user_df.columns and not user_df["ë¶€ì„œ"].empty:
                    dept_counts = user_df["ë¶€ì„œ"].value_counts().reset_index()
                    dept_counts.columns = ["ë¶€ì„œ", "ê²€ì‚¬ìž ìˆ˜"]
                    
                    # ê³µì •ë³„ ì‚¬ìš©ìž ë¶„í¬
                    process_counts = None
                    if "ê³µì •" in user_df.columns and not user_df["ê³µì •"].empty:
                        process_counts = user_df["ê³µì •"].value_counts().reset_index()
                        process_counts.columns = ["ê³µì •", "ê²€ì‚¬ìž ìˆ˜"]
                    
                    # ìƒíƒœë³„ ì‚¬ìš©ìž ë¶„í¬
                    status_counts = None
                    if "ìƒíƒœ" in user_df.columns and not user_df["ìƒíƒœ"].empty:
                        status_counts = user_df["ìƒíƒœ"].value_counts().reset_index()
                        status_counts.columns = ["ìƒíƒœ", "ê²€ì‚¬ìž ìˆ˜"]
                    
                    # ì°¨íŠ¸ í‘œì‹œ
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='emoji-title'>ðŸ‘¥ ë¶€ì„œë³„ ê²€ì‚¬ìž ë¶„í¬</div>", unsafe_allow_html=True)
                        
                        fig = px.bar(
                            dept_counts, 
                            x="ë¶€ì„œ", 
                            y="ê²€ì‚¬ìž ìˆ˜",
                            color="ë¶€ì„œ",
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
                            st.markdown("<div class='emoji-title'>ðŸ”§ ê³µì •ë³„ ê²€ì‚¬ìž ë¶„í¬</div>", unsafe_allow_html=True)
                            
                            fig = px.bar(
                                process_counts, 
                                x="ê³µì •", 
                                y="ê²€ì‚¬ìž ìˆ˜",
                                color="ê³µì •",
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
                    
                    # ìƒíƒœë³„ ì‚¬ìš©ìž ë¶„í¬ (íŒŒì´ ì°¨íŠ¸)
                    if status_counts is not None:
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='emoji-title'>ðŸ”„ ìƒíƒœë³„ ê²€ì‚¬ìž ë¶„í¬</div>", unsafe_allow_html=True)
                        
                        fig = px.pie(
                            status_counts, 
                            values="ê²€ì‚¬ìž ìˆ˜", 
                            names="ìƒíƒœ",
                            hole=0.4,
                            color="ìƒíƒœ",
                            color_discrete_map={
                                "í™œì„±": "#4CAF50",
                                "ë¹„í™œì„±": "#F44336",
                                "íœ´ë©´": "#FFC107"
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
                        
                        # ê°„ë‹¨í•œ í˜„í™© ìš”ì•½
                        st.markdown("<div class='card'>", unsafe_allow_html=True)
                        st.markdown("<div class='emoji-title'>ðŸ“Š ê²€ì‚¬ìž í˜„í™© ìš”ì•½</div>", unsafe_allow_html=True)
                        
                        active_users = len(user_df[user_df["ìƒíƒœ"] == "í™œì„±"]) if "ìƒíƒœ" in user_df.columns else 0
                        inactive_users = len(user_df[user_df["ìƒíƒœ"] != "í™œì„±"]) if "ìƒíƒœ" in user_df.columns else 0
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("í™œì„± ê²€ì‚¬ìž", active_users)
                        with col2:
                            st.metric("ë¹„í™œì„±/íœ´ë©´ ê²€ì‚¬ìž", inactive_users)
                        
                        # ìµœê·¼ ë“±ë¡ëœ ì‚¬ìš©ìž
                        if "ê³„ì •ìƒì„±ì¼" in user_df.columns and len(user_df) > 0:
                            try:
                                user_df["ê³„ì •ìƒì„±ì¼"] = pd.to_datetime(user_df["ê³„ì •ìƒì„±ì¼"], errors='coerce')
                                recent_users = user_df.sort_values("ê³„ì •ìƒì„±ì¼", ascending=False).head(3)
                                
                                st.subheader("ìµœê·¼ ë“±ë¡ëœ ê²€ì‚¬ìž")
                                for _, user in recent_users.iterrows():
                                    user_name = user["ì´ë¦„"] if "ì´ë¦„" in user and pd.notna(user["ì´ë¦„"]) else "ì´ë¦„ ì—†ìŒ"
                                    user_dept = user["ë¶€ì„œ"] if "ë¶€ì„œ" in user and pd.notna(user["ë¶€ì„œ"]) else "ë¶€ì„œ ì—†ìŒ"
                                    user_date = user["ê³„ì •ìƒì„±ì¼"].strftime("%Y-%m-%d") if pd.notna(user["ê³„ì •ìƒì„±ì¼"]) else "ë‚ ì§œ ì—†ìŒ"
                                    
                                    st.markdown(f"**{user_name}** ({user_dept}) - {user_date}")
                            except Exception as e:
                                st.warning(f"ìµœê·¼ ì‚¬ìš©ìž ì •ë³´ í‘œì‹œ ì¤‘ ì˜¤ë¥˜ ë°œìƒ: {str(e)}")
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("ì‚¬ìš©ìž ë°ì´í„°ì— 'ë¶€ì„œ' í•„ë“œê°€ ì—†ê±°ë‚˜ ë¹„ì–´ìžˆì–´ í†µê³„ë¥¼ ìƒì„±í•  ìˆ˜ ì—†ìŠµë‹ˆë‹¤.")
            except Exception as e:
                st.error(f"í†µê³„ ìƒì„± ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤: {str(e)}")
                st.info("ì‚¬ìš©ìž ë°ì´í„° êµ¬ì¡°ë¥¼ í™•ì¸í•´ì£¼ì„¸ìš”.")

elif st.session_state.page == "inspection_data":
    # ìƒì‚° ì‹¤ì  ê´€ë¦¬ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ“Š ê²€ì‚¬ì‹¤ì  ê´€ë¦¬</h1></div>", unsafe_allow_html=True)
    
    # ê´€ë¦¬ìž ê¶Œí•œ í™•ì¸
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ì´ íŽ˜ì´ì§€ëŠ” ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆìŠµë‹ˆë‹¤.")
        st.stop()
    
    # íƒ­ êµ¬ì„±
    tab1, tab2, tab3 = st.tabs(["ðŸ“‘ ì‹¤ì  ë°ì´í„° ì¡°íšŒ", "ðŸ“ ì‹¤ì  ë°ì´í„° ìž…ë ¥", "ðŸ” ë°ì´í„° ê²€ì¦"])
    
    with tab1:
        # ì‹¤ì  ë°ì´í„° ì¡°íšŒ ì„¹ì…˜
        st.subheader("ê²€ì‚¬ ì‹¤ì  ë°ì´í„° ì¡°íšŒ")
        
        # ê²€ìƒ‰ ë° í•„í„° ì¡°ê±´
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("ì‹œìž‘ì¼", datetime.now() - timedelta(days=30), key="prod_start_date")
        with col2:
            end_date = st.date_input("ì¢…ë£Œì¼", datetime.now(), key="prod_end_date")
        with col3:
            # ì‹¤ì œ ë°ì´í„°ì—ì„œ ê³µì • ëª©ë¡ ì¶”ì¶œ
            inspection_data = load_inspection_data()
            process_options = ["ì „ì²´"]
            if not inspection_data.empty and "ê³µì •" in inspection_data.columns:
                process_options += sorted(inspection_data["ê³µì •"].unique().tolist())
            process_filter = st.selectbox("ê³µì • í•„í„°", options=process_options, key="prod_process")
        
        # ë°ì´í„° ë¡œë“œ í›„ í‘œì‹œ
        if inspection_data.empty:
            st.info("ì €ìž¥ëœ ê²€ì‚¬ ì‹¤ì  ë°ì´í„°ê°€ ì—†ìŠµë‹ˆë‹¤. 'ì‹¤ì  ë°ì´í„° ìž…ë ¥' íƒ­ì—ì„œ ë°ì´í„°ë¥¼ ìž…ë ¥í•´ì£¼ì„¸ìš”.")
        else:
            # í•„ìš”í•œ ê²½ìš° ë‚ ì§œ ì—´ ë³€í™˜
            if "ê²€ì‚¬ì¼ìž" in inspection_data.columns and inspection_data["ê²€ì‚¬ì¼ìž"].dtype == 'object':
                try:
                    inspection_data["ê²€ì‚¬ì¼ìž"] = pd.to_datetime(inspection_data["ê²€ì‚¬ì¼ìž"])
                except:
                    pass
            
            # í•„í„° ì ìš©
            filtered_df = inspection_data.copy()
            
            # ë‚ ì§œ í•„í„° ì ìš©
            if "ê²€ì‚¬ì¼ìž" in filtered_df.columns:
                # ë‚ ì§œ í˜•ì‹ í™•ì¸
                if filtered_df["ê²€ì‚¬ì¼ìž"].dtype == 'datetime64[ns]':
                    filtered_df = filtered_df[
                        (filtered_df["ê²€ì‚¬ì¼ìž"].dt.date >= pd.Timestamp(start_date).date()) & 
                        (filtered_df["ê²€ì‚¬ì¼ìž"].dt.date <= pd.Timestamp(end_date).date())
                    ]
                else:
                    # ë¬¸ìžì—´ì¸ ê²½ìš° ì²˜ë¦¬
                    filtered_df = filtered_df[
                        (pd.to_datetime(filtered_df["ê²€ì‚¬ì¼ìž"]).dt.date >= pd.Timestamp(start_date).date()) & 
                        (pd.to_datetime(filtered_df["ê²€ì‚¬ì¼ìž"]).dt.date <= pd.Timestamp(end_date).date())
                    ]
            
            # ê³µì • í•„í„° ì ìš©
            if process_filter != "ì „ì²´" and "ê³µì •" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["ê³µì •"] == process_filter]
            
            # ê²€ìƒ‰ ê¸°ëŠ¥
            search_query = st.text_input("ëª¨ë¸ëª… ë˜ëŠ” LOTë²ˆí˜¸ ê²€ìƒ‰", key="prod_search")
            if search_query:
                search_condition = False
                if "ëª¨ë¸ëª…" in filtered_df.columns:
                    search_condition |= filtered_df["ëª¨ë¸ëª…"].astype(str).str.contains(search_query, case=False, na=False)
                if "LOTë²ˆí˜¸" in filtered_df.columns:
                    search_condition |= filtered_df["LOTë²ˆí˜¸"].astype(str).str.contains(search_query, case=False, na=False)
                
                filtered_df = filtered_df[search_condition]
            
            # ë°ì´í„° ì •ë ¬ ì˜µì…˜
            sort_columns = ["ê²€ì‚¬ì¼ìž"]
            if "ë¶ˆëŸ‰ë¥ (%)" in filtered_df.columns:
                sort_columns.append("ë¶ˆëŸ‰ë¥ (%)")
            
            sort_options = []
            if "ê²€ì‚¬ì¼ìž" in filtered_df.columns:
                sort_options += ["ë‚ ì§œ(ìµœì‹ ìˆœ)", "ë‚ ì§œ(ì˜¤ëž˜ëœìˆœ)"]
            if "ë¶ˆëŸ‰ë¥ (%)" in filtered_df.columns:
                sort_options += ["ë¶ˆëŸ‰ë¥ (ë†’ì€ìˆœ)", "ë¶ˆëŸ‰ë¥ (ë‚®ì€ìˆœ)"]
            
            sort_option = st.selectbox(
                "ì •ë ¬ ê¸°ì¤€",
                options=sort_options,
                index=0 if sort_options else 0
            )
            
            # ì •ë ¬ ì ìš©
            if sort_option == "ë‚ ì§œ(ìµœì‹ ìˆœ)" and "ê²€ì‚¬ì¼ìž" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="ê²€ì‚¬ì¼ìž", ascending=False)
            elif sort_option == "ë‚ ì§œ(ì˜¤ëž˜ëœìˆœ)" and "ê²€ì‚¬ì¼ìž" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="ê²€ì‚¬ì¼ìž", ascending=True)
            elif sort_option == "ë¶ˆëŸ‰ë¥ (ë†’ì€ìˆœ)" and "ë¶ˆëŸ‰ë¥ (%)" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="ë¶ˆëŸ‰ë¥ (%)", ascending=False)
            elif sort_option == "ë¶ˆëŸ‰ë¥ (ë‚®ì€ìˆœ)" and "ë¶ˆëŸ‰ë¥ (%)" in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by="ë¶ˆëŸ‰ë¥ (%)", ascending=True)
            
            # í•„í„°ë§ëœ ìƒì‚° ì‹¤ì  í‘œì‹œ
            if filtered_df.empty:
                st.warning("ê²€ìƒ‰ ì¡°ê±´ì— ë§žëŠ” ë°ì´í„°ê°€ ì—†ìŠµë‹ˆë‹¤.")
            else:
                # ë‚ ì§œ í˜•ì‹ ë³€í™˜ (í‘œì‹œìš©)
                if "ê²€ì‚¬ì¼ìž" in filtered_df.columns and filtered_df["ê²€ì‚¬ì¼ìž"].dtype == 'datetime64[ns]':
                    filtered_df["ê²€ì‚¬ì¼ìž"] = filtered_df["ê²€ì‚¬ì¼ìž"].dt.strftime("%Y-%m-%d")
                
                # ì»¬ëŸ¼ êµ¬ì„± ì„¤ì •
                column_config = {}
                
                # ë¶ˆëŸ‰ë¥  í”„ë¡œê·¸ë ˆìŠ¤ ë°” ì„¤ì •
                if "ë¶ˆëŸ‰ë¥ (%)" in filtered_df.columns:
                    column_config["ë¶ˆëŸ‰ë¥ (%)"] = st.column_config.ProgressColumn(
                        "ë¶ˆëŸ‰ë¥ (%)",
                        help="ê²€ì‚¬ ìˆ˜ëŸ‰ ì¤‘ ë¶ˆëŸ‰ ë¹„ìœ¨",
                        format="%.2f%%",
                        min_value=0,
                        max_value=10,
                    )
                
                # ë‹¬ì„±ë¥  í”„ë¡œê·¸ë ˆìŠ¤ ë°” ì„¤ì • (ê³„íšìˆ˜ëŸ‰ ëŒ€ë¹„ ê²€ì‚¬ìˆ˜ëŸ‰)
                if "ê³„íšìˆ˜ëŸ‰" in filtered_df.columns and "ê²€ì‚¬ìˆ˜ëŸ‰" in filtered_df.columns:
                    # ë‹¬ì„±ë¥  ê³„ì‚°ì´ ì•ˆ ë˜ì–´ìžˆìœ¼ë©´ ê³„ì‚°
                    if "ë‹¬ì„±ë¥ (%)" not in filtered_df.columns:
                        filtered_df["ë‹¬ì„±ë¥ (%)"] = (filtered_df["ê²€ì‚¬ìˆ˜ëŸ‰"] / filtered_df["ê³„íšìˆ˜ëŸ‰"] * 100).round(2)
                    
                    column_config["ë‹¬ì„±ë¥ (%)"] = st.column_config.ProgressColumn(
                        "ë‹¬ì„±ë¥ (%)",
                        help="ê³„íš ëŒ€ë¹„ ê²€ì‚¬ ë‹¬ì„±ë¥ ",
                        format="%.2f%%",
                        min_value=0,
                        max_value=120,
                        width="medium"
                    )
                
                # ë°ì´í„° í‘œì‹œ
                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=column_config
                )
    
    # ë‚˜ë¨¸ì§€ íƒ­ì€ êµ¬í˜„ì´ ë³µìž¡í•˜ë¯€ë¡œ ê°„ë‹¨í•œ ì•ˆë‚´ ë©”ì‹œì§€ë¡œ ëŒ€ì²´
    with tab2:
        # ì‹¤ì  ë°ì´í„° ìž…ë ¥ í¼ êµ¬í˜„
        st.subheader("ê²€ì‚¬ì‹¤ì  ë°ì´í„° ìž…ë ¥")
        
        # ê¸°ë³¸ ì •ë³´ ìž…ë ¥ í¼
        col1, col2 = st.columns(2)
        with col1:
            # ì„¸ì…˜ì— ì €ìž¥ëœ ê²€ì‚¬ì› ëª©ë¡ ì‚¬ìš© ë˜ëŠ” ê°€ì ¸ì˜¤ê¸°
            if 'inspectors' not in st.session_state or len(st.session_state.inspectors) == 0:
                try:
                    st.session_state.inspectors = load_inspectors()
                except Exception as e:
                    st.error(f"ê²€ì‚¬ì› ëª©ë¡ì„ ë¶ˆëŸ¬ì˜¤ëŠ”ë° ì‹¤íŒ¨í–ˆìŠµë‹ˆë‹¤: {str(e)}")
                    # ë°±ì—… ê²€ì‚¬ì› ëª©ë¡ ì„¤ì •
                    default_inspectors = [
                        {"id": "INS001", "name": "í™ê¸¸ë™", "department": "CNC_1"},
                        {"id": "INS002", "name": "ê¹€ì² ìˆ˜", "department": "CNC_2"},
                        {"id": "INS003", "name": "ì´ì˜í¬", "department": "PQC_LINE"},
                        {"id": "INS004", "name": "ë°•ë¯¼ìˆ˜", "department": "CNC_1"},
                        {"id": "INS005", "name": "ìµœì§€í›ˆ", "department": "CNC_2"}
                    ]
                    st.session_state.inspectors = pd.DataFrame(default_inspectors)
            
            # ê²€ì‚¬ì› ì´ë¦„ ëª©ë¡ ì¶”ì¶œ
            inspector_names = ["ê²€ì‚¬ì›ì„ ì„ íƒí•˜ì„¸ìš”"] + st.session_state.inspectors["name"].tolist()
            
            inspector_name = st.selectbox(
                "ê²€ì‚¬ì› ì´ë¦„",
                options=inspector_names,
                index=0,
                key="input_inspector_name"
            )
            
            # ê²€ì‚¬ì› ID ìžë™ ìž…ë ¥
            inspector_id = ""
            if inspector_name != "ê²€ì‚¬ì›ì„ ì„ íƒí•˜ì„¸ìš”":
                inspector_row = st.session_state.inspectors[st.session_state.inspectors["name"] == inspector_name]
                if not inspector_row.empty:
                    inspector_id = inspector_row.iloc[0]["id"]
            
            st.text_input("ê²€ì‚¬ì› ID", value=inspector_id, key="input_inspector_id", disabled=True)
            
            process = st.selectbox(
                "ê³µì •",
                options=["ê³µì •ì„ ì„ íƒí•˜ì„¸ìš”", "IQC", "CNC1_PQC", "CNC2_PQC", "OQC", "CNC OQC"],
                index=0,
                key="input_process"
            )
            
            # ëª¨ë¸ëª… ì„ íƒ - ìƒì‚°ëª¨ë¸ ë°ì´í„°ì—ì„œ ê°€ì ¸ì˜¤ê¸°
            models_df = load_product_models()
            model_options = ["ëª¨ë¸ì„ ì„ íƒí•˜ì„¸ìš”"]
            
            if not models_df.empty and "ëª¨ë¸ëª…" in models_df.columns:
                model_options += sorted(models_df["ëª¨ë¸ëª…"].unique().tolist())
            else:
                # ê¸°ë³¸ ëª¨ë¸ ì´ë¦„ ëª©ë¡
                model_options += ["BY2", "PA1", "PS SUB6", "E1", "PA3", "B7DUALSIM", "Y2", 
                         "B7R SUB6", "B6S6", "B5S6", "B7SUB", "B6", "B7MMW", "B7R MMW", "PA2", 
                         "B5M", "B7RR", "B7R SUB", "B7R", "B6M", "B7SUB6"]
            
            model_name = st.selectbox(
                "ëª¨ë¸ëª…",
                options=model_options,
                index=0,
                key="input_model"
            )
            
        with col2:
            inspection_date = st.date_input("ê²€ì‚¬ì¼ìž", datetime.now(), key="input_date")
            
            lot_number = st.text_input("LOT ë²ˆí˜¸", placeholder="LOT ë²ˆí˜¸ë¥¼ ìž…ë ¥í•˜ì„¸ìš”", key="input_lot")
            
            work_time = st.number_input("ìž‘ì—… ì‹œê°„(ë¶„)", min_value=0, value=60, placeholder="ìž‘ì—… ì‹œê°„ì„ ë¶„ ë‹¨ìœ„ë¡œ ìž…ë ¥í•˜ì„¸ìš”", key="input_work_time")
        
        # ìˆ˜ëŸ‰ ì •ë³´ ìž…ë ¥
        col1, col2, col3 = st.columns(3)
        with col1:
            plan_quantity = st.number_input("ê³„íš ìˆ˜ëŸ‰", min_value=0, value=100, placeholder="ê³„íš ìˆ˜ëŸ‰ì„ ìž…ë ¥í•˜ì„¸ìš”", key="input_plan_qty")
        with col2:
            total_quantity = st.number_input("ì´ ê²€ì‚¬ ìˆ˜ëŸ‰", min_value=0, value=0, placeholder="ì´ ê²€ì‚¬ ìˆ˜ëŸ‰ì„ ìž…ë ¥í•˜ì„¸ìš”", key="input_total_qty")
        with col3:
            defect_quantity = st.number_input("ë¶ˆëŸ‰ ìˆ˜ëŸ‰", min_value=0, value=0, placeholder="ë¶ˆëŸ‰ ìˆ˜ëŸ‰ì„ ìž…ë ¥í•˜ì„¸ìš”", key="input_defect_qty")
        
        # ë¶ˆëŸ‰ ì •ë³´ ìž…ë ¥ ì„¹ì…˜
        if defect_quantity > 0:
            st.subheader("ë¶ˆëŸ‰ ì •ë³´")
            
            # ë¶ˆëŸ‰ ìœ í˜• ì„ íƒ
            defect_types = st.multiselect(
                "ë¶ˆëŸ‰ ìœ í˜• ì„ íƒ",
                options=["Ä‚N MÃ’N", "ATN CRACK", "Cáº®T SÃ‚U, Gá»œ Báº¬C", "CHÆ¯A GIA CÃ”NG Háº¾T", "CHÆ¯A GIA CÃ”NG USB", 
                         "CRACK", "Äá»˜ Dáº¦Y MAX", "Äá»˜ Dáº¦Y MIN", "GÃƒY TOOL", "Gá»œ Báº¬C KHE SÃ“NG", 
                         "HOLE KÃCH THÆ¯á»šC", "KÃCH THÆ¯á»šC KHE SÃ“NG", "Lá»†CH USB", "Lá»—i KhÃ¡c", "MÃ’N TOOL, háº¿t CNC", 
                         "NG 3D (MÃY)", "NG CHIá»€U DÃ€I PHÃ”I", "NG CHIá»€U Rá»˜NG PHÃ”I", "NG Äá»˜ Dáº¦Y PHÃ”I", "NG KÃCH THÆ¯á»šC", 
                         "NG PHÃ”I", "NG T CUT", "Ã¸1 CRACK", "Ã¸1 CRACK PIN JIG", "SETTING", 
                         "Táº®C NÆ¯á»šC", "TÃŠN Lá»–I", "THAO TÃC1", "THAO TÃC2", "THAO TÃC3", 
                         "TOOL RUNG Láº®C", "TRÃ€N NHá»°A", "TRá»¤C A", "Váº¾T ÄÃ‚M"],
                placeholder="ë¶ˆëŸ‰ ìœ í˜•ì„ ì„ íƒí•˜ì„¸ìš”",
                key="defect_types"
            )
            
            if defect_types:
                # ë¶ˆëŸ‰ ìœ í˜•ë³„ ìˆ˜ëŸ‰ ìž…ë ¥
                cols = st.columns(min(len(defect_types), 3))
                defect_details = []
                total_defects = 0
                
                for i, defect_type in enumerate(defect_types):
                    with cols[i % 3]:
                        qty = st.number_input(
                            f"{defect_type} ìˆ˜ëŸ‰",
                            min_value=0,
                            max_value=defect_quantity,
                            key=f"defect_{i}"
                        )
                        if qty > 0:
                            defect_details.append({"type": defect_type, "quantity": qty})
                            total_defects += qty
                
                if total_defects != defect_quantity:
                    st.warning(f"ìž…ë ¥í•œ ë¶ˆëŸ‰ ìˆ˜ëŸ‰ í•©ê³„ ({total_defects})ê°€ ì´ ë¶ˆëŸ‰ ìˆ˜ëŸ‰ ({defect_quantity})ê³¼ ì¼ì¹˜í•˜ì§€ ì•ŠìŠµë‹ˆë‹¤.")
            
            # ë¶ˆëŸ‰ ì„¸ë¶€ì •ë³´ë¥¼ ì„¸ì…˜ì— ì €ìž¥
            st.session_state.defect_details = defect_details if defect_types else []
        else:
            # ë¶ˆëŸ‰ì´ ì—†ëŠ” ê²½ìš° ì„¸ì…˜ì—ì„œ ë¶ˆëŸ‰ ì„¸ë¶€ì •ë³´ ì´ˆê¸°í™”
            st.session_state.defect_details = []
        
        # ì§€í‘œ ê³„ì‚° ë° í‘œì‹œ
        if total_quantity > 0:
            st.subheader("ê²€ì‚¬ ì§€í‘œ")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                # ë¶ˆëŸ‰ë¥  ê³„ì‚°
                defect_rate = round((defect_quantity / total_quantity * 100), 2) if total_quantity > 0 else 0
                st.metric("ë¶ˆëŸ‰ë¥ ", f"{defect_rate}%")
            
            with col2:
                # ëª©í‘œ ëŒ€ë¹„ ê²€ì‚¬ìœ¨ ê³„ì‚°
                inspection_rate = round((total_quantity / plan_quantity * 100), 2) if plan_quantity > 0 else 0
                inspection_status = "âœ… ëª©í‘œ ë‹¬ì„±" if inspection_rate >= 100 else "â³ ì§„í–‰ ì¤‘"
                st.metric("ëª©í‘œëŒ€ë¹„ ê²€ì‚¬ìœ¨", f"{inspection_rate}%", delta=f"{inspection_status}")
            
            with col3:
                # ì‹œê°„ë‹¹ ê²€ì‚¬ëŸ‰ ë° ëª©í‘œ ë‹¬ì„± ì˜ˆìƒ ì‹œê°„
                if work_time > 0:
                    hourly_rate = round((total_quantity / work_time * 60), 1)
                    time_to_complete = round((plan_quantity - total_quantity) / hourly_rate * 60) if hourly_rate > 0 else 0
                    
                    if total_quantity < plan_quantity:
                        st.metric("ì‹œê°„ë‹¹ ê²€ì‚¬ëŸ‰", f"{hourly_rate}ê°œ/ì‹œê°„", 
                                 delta=f"ëª©í‘œ ë‹¬ì„±ê¹Œì§€ ì•½ {time_to_complete}ë¶„ ì†Œìš” ì˜ˆìƒ")
                    else:
                        st.metric("ì‹œê°„ë‹¹ ê²€ì‚¬ëŸ‰", f"{hourly_rate}ê°œ/ì‹œê°„", delta="ëª©í‘œ ë‹¬ì„± ì™„ë£Œ")
        
        # ë¹„ê³  ìž…ë ¥
        memo = st.text_area("ë¹„ê³ ", placeholder="íŠ¹ì´ì‚¬í•­ì´ ìžˆìœ¼ë©´ ìž…ë ¥í•˜ì„¸ìš”", key="input_memo", help="ì¶”ê°€ íŠ¹ì´ì‚¬í•­ì´ ìžˆìœ¼ë©´ ìž…ë ¥í•˜ì„¸ìš”.")
        
        # ì €ìž¥ ë²„íŠ¼
        if st.button("ë°ì´í„° ì €ìž¥", use_container_width=True):
            # ìž…ë ¥ ê²€ì¦
            if inspector_name == "ê²€ì‚¬ì›ì„ ì„ íƒí•˜ì„¸ìš”":
                st.error("ê²€ì‚¬ì›ì„ ì„ íƒí•´ì£¼ì„¸ìš”.")
            elif process == "ê³µì •ì„ ì„ íƒí•˜ì„¸ìš”":
                st.error("ê³µì •ì„ ì„ íƒí•´ì£¼ì„¸ìš”.")    
            elif model_name == "ëª¨ë¸ì„ ì„ íƒí•˜ì„¸ìš”":
                st.error("ëª¨ë¸ì„ ì„ íƒí•´ì£¼ì„¸ìš”.")
            elif total_quantity <= 0:
                st.error("ê²€ì‚¬ ìˆ˜ëŸ‰ì„ ìž…ë ¥í•´ì£¼ì„¸ìš”.")
            elif defect_quantity > total_quantity:
                st.error("ë¶ˆëŸ‰ ìˆ˜ëŸ‰ì€ ì´ ê²€ì‚¬ ìˆ˜ëŸ‰ë³´ë‹¤ í´ ìˆ˜ ì—†ìŠµë‹ˆë‹¤.")
            else:
                # ë°ì´í„° ì¤€ë¹„
                inspection_data = {
                    "ê²€ì‚¬ì›": inspector_name,
                    "ê³µì •": process,
                    "ëª¨ë¸ëª…": model_name,
                    "ê²€ì‚¬ì¼ìž": inspection_date.strftime("%Y-%m-%d"),
                    "ê²€ì‚¬ì‹œê°„": time.strftime("%H:%M"),
                    "LOTë²ˆí˜¸": lot_number,
                    "ìž‘ì—…ì‹œê°„(ë¶„)": work_time,
                    "ê³„íšìˆ˜ëŸ‰": plan_quantity,
                    "ê²€ì‚¬ìˆ˜ëŸ‰": total_quantity,
                    "ë¶ˆëŸ‰ìˆ˜ëŸ‰": defect_quantity,
                    "ë¶ˆëŸ‰ë¥ (%)": defect_rate if total_quantity > 0 else 0,
                    "ë‹¬ì„±ë¥ (%)": inspection_rate if plan_quantity > 0 else 0,
                    "ë¹„ê³ ": memo
                }
                
                # ë¶ˆëŸ‰ ì„¸ë¶€ì •ë³´ê°€ ìžˆëŠ” ê²½ìš° í•¨ê»˜ ì €ìž¥
                if defect_quantity > 0 and hasattr(st.session_state, 'defect_details') and st.session_state.defect_details:
                    inspection_data["ë¶ˆëŸ‰ì„¸ë¶€"] = st.session_state.defect_details
                
                try:
                    # ë°ì´í„°ë² ì´ìŠ¤ì— ì €ìž¥ ì‹œë„
                    response = save_inspection_data(inspection_data)
                    
                    # ë¶ˆëŸ‰ ìƒì„¸ ì €ìž¥ (ê° ë¶ˆëŸ‰ ìœ í˜•ë³„ë¡œ)
                    if defect_quantity > 0 and hasattr(st.session_state, 'defect_details'):
                        for defect_item in st.session_state.defect_details:
                            defect_data = {
                                "ë¶ˆëŸ‰ìœ í˜•": defect_item["type"],
                                "ìˆ˜ëŸ‰": defect_item["quantity"],
                                "ê²€ì‚¬ID": inspection_data.get("id", ""),  # ê²€ì‚¬ IDê°€ ìžˆëŠ” ê²½ìš°
                                "ë“±ë¡ì¼ìž": datetime.now().strftime("%Y-%m-%d"),
                                "ë“±ë¡ìž": inspector_name,
                                "ë¹„ê³ ": memo
                            }
                            try:
                                save_defect_data(defect_data)
                            except Exception as e:
                                st.warning(f"ë¶ˆëŸ‰ ì„¸ë¶€ ë°ì´í„° ì €ìž¥ ì¤‘ ì˜¤ë¥˜: {str(e)}")
                    
                    st.success("ê²€ì‚¬ì‹¤ì  ë°ì´í„°ê°€ ì„±ê³µì ìœ¼ë¡œ ì €ìž¥ë˜ì—ˆìŠµë‹ˆë‹¤!")
                    
                    # ì €ìž¥ ì„±ê³µ ì‹œ ìž…ë ¥ í•„ë“œ ì´ˆê¸°í™” ë˜ëŠ” ë‹¤ë¥¸ ì•¡ì…˜
                    st.balloons()
                    time.sleep(1)
                    st.experimental_rerun()  # íŽ˜ì´ì§€ ìƒˆë¡œê³ ì¹¨
                except Exception as e:
                    # ë¡œì»¬ ì„¸ì…˜ì— ì €ìž¥ (ë°ì´í„°ë² ì´ìŠ¤ ì—°ê²° ì‹¤íŒ¨ ì‹œ)
                    if 'saved_inspections' not in st.session_state:
                        st.session_state.saved_inspections = []
                    
                    st.session_state.saved_inspections.append(inspection_data)
                    st.success("ê²€ì‚¬ì‹¤ì  ë°ì´í„°ê°€ ì„¸ì…˜ì— ì €ìž¥ë˜ì—ˆìŠµë‹ˆë‹¤. (ë°ì´í„°ë² ì´ìŠ¤ ì—°ê²°ì´ ë˜ë©´ ìžë™ìœ¼ë¡œ ë™ê¸°í™”ë©ë‹ˆë‹¤)")
                    st.info(f"ì°¸ê³ : {str(e)}")
                    time.sleep(1)
                    st.experimental_rerun()  # íŽ˜ì´ì§€ ìƒˆë¡œê³ ì¹¨
    
    with tab3:
        # ê°„ë‹¨í•œ ë°ì´í„° ê²€ì¦ ê¸°ëŠ¥ êµ¬í˜„
        st.subheader("ë°ì´í„° ê²€ì¦")
        
        # ë‚ ì§œ ë²”ìœ„ ì„ íƒ
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("ì‹œìž‘ì¼", datetime.now() - timedelta(days=30), key="verify_start_date")
        with col2:
            end_date = st.date_input("ì¢…ë£Œì¼", datetime.now(), key="verify_end_date")
        
        # ê²€ì¦ ìœ í˜• ì„ íƒ
        verification_type = st.selectbox(
            "ê²€ì¦ ìœ í˜•",
            options=["ê²€ì¦ ìœ í˜•ì„ ì„ íƒí•˜ì„¸ìš”", "ëˆ„ë½ ë°ì´í„° ê²€ì‚¬", "ë¶ˆëŸ‰ë¥  ì´ìƒì¹˜ ê²€ì‚¬", "LOT ì¤‘ë³µ ê²€ì‚¬", "ì „ì²´ ê²€ì‚¬"],
            index=0,
            key="verification_type"
        )
        
        # ë°ì´í„° ë¡œë“œ ë° ê²€ì¦ ë²„íŠ¼
        if st.button("ë°ì´í„° ê²€ì¦ ì‹¤í–‰", key="run_verification"):
            # ë¡œë”© í‘œì‹œ
            with st.spinner("ë°ì´í„° ê²€ì¦ ì¤‘..."):
                time.sleep(1)  # ê²€ì¦ ìž‘ì—… ì‹œë®¬ë ˆì´ì…˜
                
                # ì‹¤ì œ ê²€ì‚¬ ë°ì´í„° ë¡œë“œ
                inspection_data = load_inspection_data()
                
                if not inspection_data.empty:
                    df = inspection_data.copy()
                    
                    # ë‚ ì§œ í•„í„° ì ìš©
                    if "ê²€ì‚¬ì¼ìž" in df.columns:
                        try:
                            # ë‚ ì§œ í˜•ì‹ í™•ì¸ ë° ë³€í™˜
                            if df["ê²€ì‚¬ì¼ìž"].dtype != 'datetime64[ns]':
                                df["ê²€ì‚¬ì¼ìž"] = pd.to_datetime(df["ê²€ì‚¬ì¼ìž"])
                            
                            # í•„í„°ë§
                            df = df[
                                (df["ê²€ì‚¬ì¼ìž"].dt.date >= pd.Timestamp(start_date).date()) & 
                                (df["ê²€ì‚¬ì¼ìž"].dt.date <= pd.Timestamp(end_date).date())
                            ]
                        except Exception as e:
                            st.warning(f"ë‚ ì§œ í•„í„°ë§ ì¤‘ ì˜¤ë¥˜ ë°œìƒ: {str(e)}")
                    
                    st.success(f"ì´ {len(df)}ê°œì˜ ê²€ì‚¬ ë°ì´í„°ë¥¼ ê²€ì¦í–ˆìŠµë‹ˆë‹¤.")
                    
                    # ì„ íƒí•œ ê²€ì¦ ìœ í˜•ì— ë”°ë¥¸ ê²°ê³¼ í‘œì‹œ
                    if verification_type == "ëˆ„ë½ ë°ì´í„° ê²€ì‚¬" or verification_type == "ì „ì²´ ê²€ì‚¬":
                        # í•„ìˆ˜ í•„ë“œ ì •ì˜
                        required_fields = ["ê²€ì‚¬ì›", "ê³µì •", "ëª¨ë¸ëª…", "ê²€ì‚¬ì¼ìž", "ê²€ì‚¬ìˆ˜ëŸ‰"]
                        
                        # í•„ìˆ˜ í•„ë“œ ëˆ„ë½ ê²€ì‚¬
                        missing_mask = df[required_fields].isnull().any(axis=1)
                        missing_data = df[missing_mask]
                        
                        if len(missing_data) > 0:
                            st.warning(f"{len(missing_data)}ê°œì˜ ê²€ì‚¬ ë°ì´í„°ì— í•„ìˆ˜ ê°’ì´ ëˆ„ë½ë˜ì—ˆìŠµë‹ˆë‹¤.")
                            st.dataframe(missing_data)
                        else:
                            st.info("ëˆ„ë½ëœ í•„ìˆ˜ ë°ì´í„°ê°€ ì—†ìŠµë‹ˆë‹¤.")
                    
                    if verification_type == "ë¶ˆëŸ‰ë¥  ì´ìƒì¹˜ ê²€ì‚¬" or verification_type == "ì „ì²´ ê²€ì‚¬":
                        if "ë¶ˆëŸ‰ë¥ (%)" in df.columns:
                            # ì´ìƒì¹˜ ê¸°ì¤€: ë¶ˆëŸ‰ë¥  5% ì´ˆê³¼
                            outlier_threshold = 5.0
                            outliers = df[df["ë¶ˆëŸ‰ë¥ (%)"] > outlier_threshold]
                            
                            if len(outliers) > 0:
                                st.warning(f"{len(outliers)}ê°œì˜ ê²€ì‚¬ ë°ì´í„°ì— ë¶ˆëŸ‰ë¥  ì´ìƒì¹˜ê°€ ìžˆìŠµë‹ˆë‹¤. (ê¸°ì¤€: {outlier_threshold}% ì´ˆê³¼)")
                                display_cols = ["ê²€ì‚¬ì¼ìž", "ëª¨ë¸ëª…", "ê³µì •", "ê²€ì‚¬ìˆ˜ëŸ‰", "ë¶ˆëŸ‰ìˆ˜ëŸ‰", "ë¶ˆëŸ‰ë¥ (%)"]
                                display_cols = [col for col in display_cols if col in outliers.columns]
                                st.dataframe(outliers[display_cols])
                            else:
                                st.info("ë¶ˆëŸ‰ë¥  ì´ìƒì¹˜ê°€ ì—†ìŠµë‹ˆë‹¤.")
                    
                    if verification_type == "LOT ì¤‘ë³µ ê²€ì‚¬" or verification_type == "ì „ì²´ ê²€ì‚¬":
                        if "LOTë²ˆí˜¸" in df.columns:
                            # LOTë²ˆí˜¸ê°€ ë¹„ì–´ìžˆì§€ ì•Šì€ ë°ì´í„°ë§Œ ê³ ë ¤
                            df_with_lot = df[df["LOTë²ˆí˜¸"].notna() & (df["LOTë²ˆí˜¸"] != "")]
                            duplicates = df_with_lot[df_with_lot.duplicated("LOTë²ˆí˜¸", keep=False)]
                            
                            if len(duplicates) > 0:
                                st.warning(f"{len(duplicates)}ê°œì˜ ê²€ì‚¬ ë°ì´í„°ì— LOT ë²ˆí˜¸ ì¤‘ë³µì´ ìžˆìŠµë‹ˆë‹¤.")
                                display_cols = ["ê²€ì‚¬ì¼ìž", "LOTë²ˆí˜¸", "ëª¨ë¸ëª…", "ê³µì •", "ê²€ì‚¬ìˆ˜ëŸ‰"]
                                display_cols = [col for col in display_cols if col in duplicates.columns]
                                st.dataframe(duplicates[display_cols].sort_values(by="LOTë²ˆí˜¸"))
                            else:
                                st.info("LOT ë²ˆí˜¸ ì¤‘ë³µì´ ì—†ìŠµë‹ˆë‹¤.")
                else:
                    # ë°ì´í„°ê°€ ì—†ì„ ê²½ìš°
                    st.info("ê²€ì‚¬ ë°ì´í„°ê°€ ì—†ìŠµë‹ˆë‹¤. 'ì‹¤ì  ë°ì´í„° ìž…ë ¥' íƒ­ì—ì„œ ë°ì´í„°ë¥¼ ìž…ë ¥í•´ì£¼ì„¸ìš”.")
            
            # ê²€ì¦ ì™„ë£Œ í›„ ìš”ì•½ ì •ë³´
            if not inspection_data.empty:
                st.subheader("ê²€ì¦ ìš”ì•½")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # ê²€ì‚¬ ë°ì´í„° ìˆ˜
                    filtered_count = len(df) if 'df' in locals() else 0
                    total_count = len(inspection_data)
                    st.metric("ì´ ê²€ì‚¬ ë°ì´í„°", f"{total_count}ê±´", f"ì¡°íšŒ ê¸°ê°„: {filtered_count}ê±´")
                
                with col2:
                    # í‰ê·  ë¶ˆëŸ‰ë¥ 
                    if "ë¶ˆëŸ‰ë¥ (%)" in inspection_data.columns:
                        avg_defect_rate = inspection_data["ë¶ˆëŸ‰ë¥ (%)"].mean()
                        st.metric("í‰ê·  ë¶ˆëŸ‰ë¥ ", f"{avg_defect_rate:.2f}%")
                    else:
                        st.metric("í‰ê·  ë¶ˆëŸ‰ë¥ ", "ë°ì´í„° ì—†ìŒ")
                
                with col3:
                    # ê°€ìž¥ ë§Žì€ ëª¨ë¸
                    if "ëª¨ë¸ëª…" in inspection_data.columns and not inspection_data.empty:
                        top_model = inspection_data["ëª¨ë¸ëª…"].value_counts().idxmax()
                        model_count = inspection_data["ëª¨ë¸ëª…"].value_counts().max()
                        st.metric("ìµœë‹¤ ê²€ì‚¬ ëª¨ë¸", f"{top_model}", f"{model_count}ê±´")
                    else:
                        st.metric("ìµœë‹¤ ê²€ì‚¬ ëª¨ë¸", "ë°ì´í„° ì—†ìŒ")
                
                # ì–´ì œì™€ ì˜¤ëŠ˜ì˜ ê²€ì‚¬ ë°ì´í„° ë¹„êµ
                today = datetime.now().date()
                yesterday = today - timedelta(days=1)
                
                if "ê²€ì‚¬ì¼ìž" in inspection_data.columns:
                    try:
                        # ë‚ ì§œ í˜•ì‹ ë³€í™˜ (í•„ìš”í•œ ê²½ìš°)
                        if inspection_data["ê²€ì‚¬ì¼ìž"].dtype != 'datetime64[ns]':
                            date_column = pd.to_datetime(inspection_data["ê²€ì‚¬ì¼ìž"])
                        else:
                            date_column = inspection_data["ê²€ì‚¬ì¼ìž"]
                        
                        # ì˜¤ëŠ˜ê³¼ ì–´ì œ ë°ì´í„° ì¹´ìš´íŠ¸
                        today_count = sum(date_column.dt.date == today)
                        yesterday_count = sum(date_column.dt.date == yesterday)
                        
                        # ë³€í™”ìœ¨ ê³„ì‚°
                        if yesterday_count > 0:
                            change_pct = ((today_count - yesterday_count) / yesterday_count) * 100
                            change_text = f"{change_pct:.1f}% ({yesterday_count}ê±´ ëŒ€ë¹„)"
                        else:
                            change_text = "ì–´ì œ ë°ì´í„° ì—†ìŒ"
                        
                        st.metric("ì˜¤ëŠ˜ ê²€ì‚¬ ê±´ìˆ˜", f"{today_count}ê±´", change_text)
                    except Exception as e:
                        st.metric("ì˜¤ëŠ˜ ê²€ì‚¬ ê±´ìˆ˜", "ê³„ì‚° ì˜¤ë¥˜", f"ì˜¤ë¥˜: {str(e)}")
                else:
                    st.metric("ì˜¤ëŠ˜ ê²€ì‚¬ ê±´ìˆ˜", "ë°ì´í„° ì—†ìŒ")

elif st.session_state.page == "quality_report":
    # ì›”ê°„ í’ˆì§ˆ ë¦¬í¬íŠ¸ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>â­ ì›”ê°„ í’ˆì§ˆ ë¦¬í¬íŠ¸</h1></div>", unsafe_allow_html=True)
    
    # ë‚ ì§œ ì„ íƒ
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox("ì—°ë„ ì„ íƒ", options=list(range(datetime.now().year-2, datetime.now().year+1)), index=2)
    with col2:
        selected_month = st.selectbox("ì›” ì„ íƒ", options=list(range(1, 13)), index=datetime.now().month-1)
    
    # ì„ íƒëœ ì›”ì˜ ë¬¸ìžì—´ í‘œí˜„
    month_names = ["1ì›”", "2ì›”", "3ì›”", "4ì›”", "5ì›”", "6ì›”", "7ì›”", "8ì›”", "9ì›”", "10ì›”", "11ì›”", "12ì›”"]
    selected_month_name = month_names[selected_month-1]
    
    # ë°ì´í„° ë¡œë”© í‘œì‹œ
    with st.spinner(f"{selected_year}ë…„ {selected_month_name} í’ˆì§ˆ ë°ì´í„° ë¶„ì„ ì¤‘..."):
        time.sleep(0.5)  # ë°ì´í„° ë¡œë”© ì‹œë®¬ë ˆì´ì…˜
    
    # í’ˆì§ˆ ìš”ì•½ ì§€í‘œ
    st.subheader(f"{selected_year}ë…„ {selected_month_name} í’ˆì§ˆ ìš”ì•½")
    
    # ì£¼ìš” ì§€í‘œ ì¹´ë“œ
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("<div class='metric-card blue-indicator'>", unsafe_allow_html=True)
        st.metric("ì›”ë³„ ê²€ì‚¬ ê±´ìˆ˜", "487ê±´", "+12%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='metric-card green-indicator'>", unsafe_allow_html=True)
        st.metric("ë¶ˆëŸ‰ë¥ ", "0.62%", "-0.08%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col3:
        st.markdown("<div class='metric-card orange-indicator'>", unsafe_allow_html=True)
        st.metric("í’ˆì§ˆ ëª©í‘œ ë‹¬ì„±ë¥ ", "97.5%", "+1.2%")
        st.markdown("</div>", unsafe_allow_html=True)
    with col4:
        st.markdown("<div class='metric-card purple-indicator'>", unsafe_allow_html=True)
        st.metric("ê³ ê° ë°˜í’ˆë¥ ", "0.05%", "-0.02%")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # í’ˆì§ˆ íŠ¸ë Œë“œ ì°¨íŠ¸
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“ˆ 6ê°œì›” í’ˆì§ˆ ì¶”ì´</div>", unsafe_allow_html=True)
    
    # ìƒ˜í”Œ ë°ì´í„° ì¤€ë¹„
    months = [(datetime.now() - timedelta(days=30*i)).strftime("%Y-%m") for i in range(5, -1, -1)]
    month_labels = [(datetime.now() - timedelta(days=30*i)).strftime("%Yë…„ %mì›”") for i in range(5, -1, -1)]
    
    # ë¶ˆëŸ‰ë¥  ë°ì´í„° (ê°œì„  ì¶”ì„¸)
    defect_rates = [0.82, 0.78, 0.74, 0.69, 0.65, 0.62]
    
    # ë°˜í’ˆë¥  ë°ì´í„° (ë” ë‚®ì€ ê°’)
    return_rates = [0.12, 0.10, 0.09, 0.07, 0.06, 0.05]
    
    # í’ˆì§ˆ ëª©í‘œ ë‹¬ì„±ë¥  ë°ì´í„° (ìƒìŠ¹ ì¶”ì„¸)
    quality_achievement = [92.5, 93.2, 94.1, 95.3, 96.2, 97.5]
    
    # ë³µí•© ê·¸ëž˜í”„ ìƒì„±
    fig = go.Figure()
    
    # ë¶ˆëŸ‰ë¥  (ì„  ê·¸ëž˜í”„)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=defect_rates,
        name="ë¶ˆëŸ‰ë¥ (%)",
        line=dict(color="#4361ee", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        yaxis="y1",
        hovertemplate='%{x}<br>ë¶ˆëŸ‰ë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # ë°˜í’ˆë¥  (ì„  ê·¸ëž˜í”„)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=return_rates,
        name="ë°˜í’ˆë¥ (%)",
        line=dict(color="#fb8c00", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        yaxis="y1",
        hovertemplate='%{x}<br>ë°˜í’ˆë¥ : %{y:.2f}%<extra></extra>'
    ))
    
    # í’ˆì§ˆ ëª©í‘œ ë‹¬ì„±ë¥  (ì„  ê·¸ëž˜í”„, ë‘ ë²ˆì§¸ yì¶•)
    fig.add_trace(go.Scatter(
        x=month_labels,
        y=quality_achievement,
        name="í’ˆì§ˆ ëª©í‘œ ë‹¬ì„±ë¥ (%)",
        line=dict(color="#4cb782", width=3),
        mode="lines+markers",
        marker=dict(size=8),
        yaxis="y2",
        hovertemplate='%{x}<br>í’ˆì§ˆ ë‹¬ì„±ë¥ : %{y:.1f}%<extra></extra>'
    ))
    
    # ë¶ˆëŸ‰ë¥  ëª©í‘œì„  (1%)
    fig.add_trace(go.Scatter(
        x=[month_labels[0], month_labels[-1]],
        y=[1.0, 1.0],
        name="ë¶ˆëŸ‰ë¥  ëª©í‘œ(1%)",
        line=dict(color="red", width=2, dash="dash"),
        mode="lines",
        yaxis="y1",
        hoverinfo="skip"
    ))
    
    # ë ˆì´ì•„ì›ƒ ì„¤ì •
    fig.update_layout(
        title=None,
        xaxis=dict(title=None),
        yaxis=dict(
            title="ë¶ˆëŸ‰ë¥ /ë°˜í’ˆë¥  (%)",
            side="left",
            range=[0, 1.2],
            showgrid=False
        ),
        yaxis2=dict(
            title="ëª©í‘œ ë‹¬ì„±ë¥  (%)",
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
    
    # ê³µì •ë³„ í’ˆì§ˆ ë¶„ì„
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>âš™ï¸ ê³µì •ë³„ í’ˆì§ˆ ë¶„ì„</div>", unsafe_allow_html=True)
    
    # ê³µì • ë°ì´í„°
    processes = ["ì„ ì‚­", "ë°€ë§", "ì—°ì‚­", "ë“œë¦´ë§", "ì¡°ë¦½", "ê²€ì‚¬"]
    process_defect_rates = [0.85, 0.65, 0.55, 0.70, 0.45, 0.20]
    process_inspection_counts = [1200, 980, 850, 780, 1500, 2000]
    
    # ê³µì •ë³„ ë°ì´í„°í”„ë ˆìž„
    process_df = pd.DataFrame({
        "ê³µì •": processes,
        "ë¶ˆëŸ‰ë¥ (%)": process_defect_rates,
        "ê²€ì‚¬ê±´ìˆ˜": process_inspection_counts
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        # ê³µì •ë³„ ë¶ˆëŸ‰ë¥  ë§‰ëŒ€ ê·¸ëž˜í”„
        fig = px.bar(
            process_df,
            x="ê³µì •",
            y="ë¶ˆëŸ‰ë¥ (%)",
            color="ê³µì •",
            color_discrete_sequence=px.colors.qualitative.Bold,
            labels={"ë¶ˆëŸ‰ë¥ (%)": "ë¶ˆëŸ‰ë¥  (%)"},
            text_auto='.2f'
        )
        
        # í‰ê·  ë¶ˆëŸ‰ë¥  ë¼ì¸
        avg_defect = np.mean(process_defect_rates)
        fig.add_shape(
            type="line",
            x0=-0.5, y0=avg_defect,
            x1=len(processes)-0.5, y1=avg_defect,
            line=dict(color="#4361ee", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=1, y=avg_defect,
            text=f"í‰ê· : {avg_defect:.2f}%",
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
        # ê³µì •ë³„ ë¶ˆëŸ‰ë¥  ë° ê²€ì‚¬ê±´ìˆ˜ ë²„ë¸” ì°¨íŠ¸
        fig = px.scatter(
            process_df,
            x="ê³µì •",
            y="ë¶ˆëŸ‰ë¥ (%)",
            size="ê²€ì‚¬ê±´ìˆ˜",
            color="ë¶ˆëŸ‰ë¥ (%)",
            color_continuous_scale="Viridis",
            size_max=50,
            labels={"ë¶ˆëŸ‰ë¥ (%)": "ë¶ˆëŸ‰ë¥  (%)"},
            hover_data={"ê²€ì‚¬ê±´ìˆ˜": True}
        )
        
        fig.update_layout(
            title=None,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=300,
            coloraxis_colorbar=dict(title="ë¶ˆëŸ‰ë¥  (%)")
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ê³µì •ë³„ í’ˆì§ˆ ì§€í‘œ í…Œì´ë¸”
    process_df["ê°œì„ í•„ìš”"] = ["" if rate < 0.7 else "âš ï¸" for rate in process_df["ë¶ˆëŸ‰ë¥ (%)"]]
    process_df["í’ˆì§ˆê·¸ë£¹"] = ["A" if rate < 0.5 else "B" if rate < 0.7 else "C" for rate in process_df["ë¶ˆëŸ‰ë¥ (%)"]]
    
    st.dataframe(
        process_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "ë¶ˆëŸ‰ë¥ (%)": st.column_config.ProgressColumn(
                "ë¶ˆëŸ‰ë¥ (%)",
                help="ê³µì •ë³„ ë¶ˆëŸ‰ë¥ ",
                format="%.2f%%",
                min_value=0,
                max_value=1,
            ),
            "ê²€ì‚¬ê±´ìˆ˜": st.column_config.NumberColumn(
                "ê²€ì‚¬ê±´ìˆ˜",
                help="ê³µì •ë³„ ê²€ì‚¬ ê±´ìˆ˜",
                format="%dê±´",
            ),
            "ê°œì„ í•„ìš”": st.column_config.TextColumn(
                "ê°œì„ í•„ìš”",
                help="ë¶ˆëŸ‰ë¥  0.7% ì´ìƒ ê³µì •ì€ ê°œì„  í•„ìš”"
            ),
            "í’ˆì§ˆê·¸ë£¹": st.column_config.SelectboxColumn(
                "í’ˆì§ˆê·¸ë£¹",
                help="ë¶ˆëŸ‰ë¥ ì— ë”°ë¥¸ í’ˆì§ˆ ê·¸ë£¹",
                options=["A", "B", "C"],
                required=True,
            ),
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ë¶ˆëŸ‰ ìœ í˜• ë¶„ì„
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ” ë¶ˆëŸ‰ ìœ í˜• ë¶„ì„</div>", unsafe_allow_html=True)
    
    defect_types = ["ì¹˜ìˆ˜ë¶ˆëŸ‰", "í‘œë©´ê±°ì¹ ê¸°", "ì¹©í•‘", "ì†Œìž¬ê²°í•¨", "ê°€ê³µë¶ˆëŸ‰", "ì¡°ë¦½ë¶ˆëŸ‰", "ê¸°íƒ€"]
    defect_counts = [42, 35, 28, 15, 22, 18, 10]
    
    defect_df = pd.DataFrame({
        "ë¶ˆëŸ‰ìœ í˜•": defect_types,
        "ë°œìƒê±´ìˆ˜": defect_counts,
        "ë¹„ìœ¨(%)": [(count / sum(defect_counts) * 100).round(2) for count in defect_counts]
    })
    
    # ë¶ˆëŸ‰ ìœ í˜•ë³„ íŒŒë ˆí†  ì°¨íŠ¸
    fig = go.Figure()
    
    # ë§‰ëŒ€ ê·¸ëž˜í”„ (ë¶ˆëŸ‰ ê±´ìˆ˜)
    fig.add_trace(go.Bar(
        x=defect_df["ë¶ˆëŸ‰ìœ í˜•"],
        y=defect_df["ë°œìƒê±´ìˆ˜"],
        marker_color="#4361ee",
        name="ë°œìƒê±´ìˆ˜",
        text=defect_df["ë°œìƒê±´ìˆ˜"],
        textposition="auto"
    ))
    
    # ëˆ„ì  ë¹„ìœ¨ ê³„ì‚°
    defect_df = defect_df.sort_values(by="ë°œìƒê±´ìˆ˜", ascending=False)
    cum_percent = np.cumsum(defect_df["ë°œìƒê±´ìˆ˜"]) / sum(defect_df["ë°œìƒê±´ìˆ˜"]) * 100
    
    # ì„  ê·¸ëž˜í”„ (ëˆ„ì  ë¹„ìœ¨)
    fig.add_trace(go.Scatter(
        x=defect_df["ë¶ˆëŸ‰ìœ í˜•"],
        y=cum_percent,
        mode="lines+markers",
        marker=dict(size=8),
        line=dict(color="#fb8c00", width=3),
        name="ëˆ„ì  ë¹„ìœ¨(%)",
        yaxis="y2",
        hovertemplate='%{x}<br>ëˆ„ì  ë¹„ìœ¨: %{y:.1f}%<extra></extra>'
    ))
    
    # 80% ê¸°ì¤€ì„ 
    fig.add_trace(go.Scatter(
        x=[defect_df["ë¶ˆëŸ‰ìœ í˜•"].iloc[0], defect_df["ë¶ˆëŸ‰ìœ í˜•"].iloc[-1]],
        y=[80, 80],
        mode="lines",
        line=dict(color="red", width=2, dash="dash"),
        name="80% ê¸°ì¤€",
        yaxis="y2",
        hoverinfo="skip"
    ))
    
    # ë ˆì´ì•„ì›ƒ ì„¤ì •
    fig.update_layout(
        title=None,
        xaxis=dict(title="ë¶ˆëŸ‰ ìœ í˜•"),
        yaxis=dict(
            title="ë°œìƒ ê±´ìˆ˜",
            side="left",
            showgrid=False
        ),
        yaxis2=dict(
            title="ëˆ„ì  ë¹„ìœ¨ (%)",
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
        st.subheader("í•µì‹¬ ê°œì„  ëŒ€ìƒ")
        st.markdown("**ì£¼ìš” ë¶ˆëŸ‰ ìœ í˜• (80% ë¹„ì¤‘)**")
        
        # ëˆ„ì  80%ê¹Œì§€ì˜ ë¶ˆëŸ‰ ìœ í˜•
        critical_defects = defect_df[cum_percent <= 80]
        
        for idx, row in critical_defects.iterrows():
            st.markdown(f"âš ï¸ **{row['ë¶ˆëŸ‰ìœ í˜•']}**: {row['ë°œìƒê±´ìˆ˜']}ê±´ ({row['ë¹„ìœ¨(%)']}%)")
        
        st.markdown("---")
        st.markdown("**ì‹ ê·œ ë¶ˆëŸ‰ íƒì§€**")
        
        new_defects = ["í‘œë©´ê±°ì¹ ê¸°", "ì¡°ë¦½ë¶ˆëŸ‰"]
        for defect in new_defects:
            st.markdown(f"ðŸ†• **{defect}**: ì „ì›” ëŒ€ë¹„ ì¦ê°€")
    
    # ë¶ˆëŸ‰ ìœ í˜•ë³„ ê°œì„  ê¶Œê³  ì‚¬í•­
    improvement_data = {
        "ë¶ˆëŸ‰ìœ í˜•": ["ì¹˜ìˆ˜ë¶ˆëŸ‰", "í‘œë©´ê±°ì¹ ê¸°", "ì¹©í•‘"],
        "ê·¼ë³¸ì›ì¸": ["ê³µêµ¬ ë§ˆëª¨", "ê°€ê³µ ì¡°ê±´ ë¶€ì ì ˆ", "ì†Œìž¬ í’ˆì§ˆ ë¶ˆëŸ‰"],
        "ê°œì„ ë°©ì•ˆ": ["ê³µêµ¬ êµì²´ ì£¼ê¸° ë‹¨ì¶•", "ê°€ê³µ ì†ë„ ë° ì´ì†¡ ì¡°ì •", "ì†Œìž¬ ê³µê¸‰ì—…ì²´ í’ˆì§ˆ ê´€ë¦¬ ê°•í™”"],
        "ë‹´ë‹¹ë¶€ì„œ": ["ìƒì‚°ë¶€", "ê¸°ìˆ ë¶€", "í’ˆì§ˆë¶€"],
        "ìš°ì„ ìˆœìœ„": ["ìƒ", "ìƒ", "ì¤‘"]
    }
    
    improvement_df = pd.DataFrame(improvement_data)
    
    st.subheader("ì£¼ìš” ë¶ˆëŸ‰ ê°œì„  ê¶Œê³ ì‚¬í•­")
    st.dataframe(improvement_df, use_container_width=True, hide_index=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # ì›”ê°„ í’ˆì§ˆ ìš”ì•½ ë³´ê³ ì„œ
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='emoji-title'>ðŸ“‹ ì›”ê°„ í’ˆì§ˆ ìš”ì•½ ë³´ê³ ì„œ</div>", unsafe_allow_html=True)
    
    st.markdown(f"""
    ### {selected_year}ë…„ {selected_month_name} í’ˆì§ˆ ì„±ê³¼ ìš”ì•½
    
    - **ì „ì²´ ë¶ˆëŸ‰ë¥ **: 0.62% (ì „ì›” ëŒ€ë¹„ 0.08%p ê°ì†Œ)
    - **ë¶ˆëŸ‰ ìœ í˜• ë¶„ì„**: ì¹˜ìˆ˜ë¶ˆëŸ‰ê³¼ í‘œë©´ê±°ì¹ ê¸°ê°€ ì „ì²´ ë¶ˆëŸ‰ì˜ ì•½ 45%ë¥¼ ì°¨ì§€í•¨
    - **ê³µì •ë³„ ë¶„ì„**: ì„ ì‚­ ê³µì •ì´ ê°€ìž¥ ë†’ì€ ë¶ˆëŸ‰ë¥ (0.85%)ì„ ë³´ìž„
    - **í’ˆì§ˆ ê°œì„  í™œë™**: ê³µêµ¬ êµì²´ ì£¼ê¸° ë‹¨ì¶•, ê°€ê³µ ì¡°ê±´ ìµœì í™”ë¡œ í‘œë©´ê±°ì¹ ê¸° ë¶ˆëŸ‰ ê°ì†Œ
    - **ê¶Œê³  ì‚¬í•­**: ì¹˜ìˆ˜ë¶ˆëŸ‰ ê°œì„ ì„ ìœ„í•œ ê³µì • ëª¨ë‹ˆí„°ë§ ì‹œìŠ¤í…œ ë„ìž… ê²€í† 
    
    ### ë‹¤ìŒ ë‹¬ í’ˆì§ˆ ê°œì„  ê³„íš
    
    1. ì„ ì‚­ ê³µì • ê°€ê³µ ì¡°ê±´ ìµœì í™” ì—°êµ¬
    2. ì¹˜ìˆ˜ë¶ˆëŸ‰ ê°œì„ ì„ ìœ„í•œ ìž‘ì—…ìž êµìœ¡ í”„ë¡œê·¸ëž¨ ì‹¤ì‹œ
    3. ìƒˆë¡œìš´ ì¸¡ì • ìž¥ë¹„ ë„ìž…ìœ¼ë¡œ ë¶ˆëŸ‰ íƒì§€ìœ¨ í–¥ìƒ
    """)
    
    # ë³´ê³ ì„œ ë‹¤ìš´ë¡œë“œ ë²„íŠ¼
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button(
            label="ðŸ“„ PDF ë³´ê³ ì„œ ë‹¤ìš´ë¡œë“œ",
            data=b"Sample PDF Report",
            file_name=f"í’ˆì§ˆë³´ê³ ì„œ_{selected_year}_{selected_month}.pdf",
            mime="application/pdf"
        )
    
    with download_col2:
        st.download_button(
            label="ðŸ“Š Excel ë°ì´í„° ë‹¤ìš´ë¡œë“œ",
            data=b"Sample Excel Data",
            file_name=f"í’ˆì§ˆë°ì´í„°_{selected_year}_{selected_month}.xlsx",
            mime="application/vnd.ms-excel"
        )
    
    st.markdown("</div>", unsafe_allow_html=True)

def save_inspector(inspector_data):
    try:
        response = supabase.table('inspectors').insert(inspector_data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"ê²€ì‚¬ì› ì •ë³´ ì €ìž¥ ì¤‘ ì˜¤ë¥˜: {str(e)}")
        # ì„¸ì…˜ì— ë°ì´í„° ì €ìž¥(ë°±ì—…)
        if 'saved_inspectors' not in st.session_state:
            st.session_state.saved_inspectors = []
        st.session_state.saved_inspectors.append(inspector_data)
        raise e

def update_inspector(inspector_id, updated_data):
    try:
        response = supabase.table('inspectors').update(updated_data).eq('id', inspector_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"ê²€ì‚¬ì› ì •ë³´ ì—…ë°ì´íŠ¸ ì¤‘ ì˜¤ë¥˜: {str(e)}")
        raise e

def delete_inspector(inspector_id):
    try:
        response = supabase.table('inspectors').delete().eq('id', inspector_id).execute()
        return True
    except Exception as e:
        st.error(f"ê²€ì‚¬ì› ì •ë³´ ì‚­ì œ ì¤‘ ì˜¤ë¥˜: {str(e)}")
        return False

def inspector_management_ui():
    st.title("ê²€ì‚¬ì› ê´€ë¦¬")
    
    # ê²€ì‚¬ì› ëª©ë¡ í‘œì‹œ
    inspectors = load_inspectors()
    st.dataframe(inspectors)
    
    # ìƒˆ ê²€ì‚¬ì› ë“±ë¡ í¼
    with st.form("new_inspector_form"):
        st.subheader("ìƒˆ ê²€ì‚¬ì› ë“±ë¡")
        col1, col2 = st.columns(2)
        
        with col1:
            new_id = st.text_input("ê²€ì‚¬ì› ID")
            new_name = st.text_input("ì´ë¦„")
        
        with col2:
            new_dept = st.selectbox("ë¶€ì„œ", options=["CNC_1", "CNC_2", "PQC_LINE"])
            new_process = st.selectbox("ê³µì •", options=["ì„ ì‚­", "ë°€ë§", "ê²€ì‚¬", "ê¸°íƒ€"])
        
        new_years = st.number_input("ê·¼ì†ë…„ìˆ˜", min_value=0.0, step=0.5)
        submitted = st.form_submit_button("ë“±ë¡")
        
        if submitted:
            if not new_id or not new_name:
                st.error("ê²€ì‚¬ì› IDì™€ ì´ë¦„ì€ í•„ìˆ˜ìž…ë‹ˆë‹¤.")
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
                    st.success(f"{new_name} ê²€ì‚¬ì›ì´ ì„±ê³µì ìœ¼ë¡œ ë“±ë¡ë˜ì—ˆìŠµë‹ˆë‹¤.")
                    st.rerun()  # íŽ˜ì´ì§€ ìƒˆë¡œê³ ì¹¨
                except Exception as e:
                    st.error(f"ë“±ë¡ ì‹¤íŒ¨: {str(e)}")

def sync_offline_data():
    if 'saved_inspectors' in st.session_state and st.session_state.saved_inspectors:
        with st.spinner("ì˜¤í”„ë¼ì¸ ë°ì´í„° ë™ê¸°í™” ì¤‘..."):
            success_count = 0
            for inspector in st.session_state.saved_inspectors[:]:
                try:
                    save_inspector(inspector)
                    st.session_state.saved_inspectors.remove(inspector)
                    success_count += 1
                except Exception:
                    continue
            
            if success_count > 0:
                st.success(f"{success_count}ê°œì˜ ê²€ì‚¬ì› ë°ì´í„°ê°€ ë™ê¸°í™”ë˜ì—ˆìŠµë‹ˆë‹¤.")
            
            if st.session_state.saved_inspectors:
                st.warning(f"{len(st.session_state.saved_inspectors)}ê°œì˜ ë°ì´í„°ëŠ” ì—¬ì „ížˆ ë™ê¸°í™”ë˜ì§€ ì•Šì•˜ìŠµë‹ˆë‹¤.")

# ìƒì‚°ëª¨ë¸ ë°ì´í„° ê°€ì ¸ì˜¤ê¸°
def load_product_models():
    """
    ìƒì‚°ëª¨ë¸ ë°ì´í„°ë¥¼ ë¡œë“œí•©ë‹ˆë‹¤.
    """
    try:
        # CSV íŒŒì¼ì´ ìžˆëŠ”ì§€ ë¨¼ì € í™•ì¸
        if os.path.exists("data/product_models.csv"):
            df = pd.read_csv("data/product_models.csv")
            return df
        # JSON íŒŒì¼ì´ ìžˆëŠ”ì§€ í™•ì¸
        elif (DATA_DIR / "product_models.json").exists():
            with open(DATA_DIR / "product_models.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "models" in data:
                    df = pd.DataFrame(data["models"])
                    # ì €ìž¥ í˜•ì‹ì„ CSVë¡œ í†µì¼
                    df.to_csv("data/product_models.csv", index=False)
                    return df
        
        # ë°ì´í„°ê°€ ì—†ìœ¼ë©´ ë¹ˆ DataFrame ìƒì„±
        return pd.DataFrame(columns=["id", "ëª¨ë¸ëª…", "ê³µì •"])
    except Exception as e:
        print(f"ìƒì‚°ëª¨ë¸ ë°ì´í„° ë¡œë“œ ì¤‘ ì˜¤ë¥˜: {str(e)}")
        return pd.DataFrame(columns=["id", "ëª¨ë¸ëª…", "ê³µì •"])

# ìƒì‚°ëª¨ë¸ ë°ì´í„° ì €ìž¥
def save_product_models(df):
    """
    ìƒì‚°ëª¨ë¸ ë°ì´í„°ë¥¼ ì €ìž¥í•©ë‹ˆë‹¤.
    
    Args:
        df (pandas.DataFrame): ì €ìž¥í•  ìƒì‚°ëª¨ë¸ ë°ì´í„°
        
    Returns:
        bool: ì €ìž¥ ì„±ê³µ ì—¬ë¶€
    """
    try:
        # ë°ì´í„° ë””ë ‰í† ë¦¬ í™•ì¸
        if not os.path.exists("data"):
            os.makedirs("data")
            
        # ë°ì´í„° ì €ìž¥ (CSV í˜•ì‹)
        df.to_csv("data/product_models.csv", index=False)
        return True
    except Exception as e:
        print(f"ìƒì‚°ëª¨ë¸ ë°ì´í„° ì €ìž¥ ì¤‘ ì˜¤ë¥˜: {str(e)}")
        return False

# ì—¬ê¸°ì„œë¶€í„° ì œí’ˆ ëª¨ë¸ ê´€ë¦¬ íŽ˜ì´ì§€ ì½”ë“œ

if st.session_state.page == "product_model":
    # ìƒì‚°ëª¨ë¸ ê´€ë¦¬ íŽ˜ì´ì§€
    st.markdown("<div class='title-area'><h1>ðŸ“¦ ìƒì‚°ëª¨ë¸ ê´€ë¦¬</h1></div>", unsafe_allow_html=True)
    
    # ê´€ë¦¬ìž ê¶Œí•œ í™•ì¸
    if st.session_state.user_role != "ê´€ë¦¬ìž":
        st.warning("ì´ íŽ˜ì´ì§€ëŠ” ê´€ë¦¬ìžë§Œ ì ‘ê·¼í•  ìˆ˜ ìžˆìŠµë‹ˆë‹¤.")
        st.stop()
    
    # ìƒì‚°ëª¨ë¸ ë°ì´í„° ë¡œë“œ
    product_models_df = load_product_models()
    
    # íƒ­ ìƒì„±
    tab1, tab2 = st.tabs(["ðŸ“‹ ìƒì‚°ëª¨ë¸ ëª©ë¡", "âž• ìƒì‚°ëª¨ë¸ ì¶”ê°€/ìˆ˜ì •"])
    
    with tab1:
        st.subheader("ìƒì‚°ëª¨ë¸ ëª©ë¡")
        
        # ê²€ìƒ‰ í•„í„°
        col1, col2 = st.columns(2)
        with col1:
            search_model = st.text_input("ëª¨ë¸ëª… ê²€ìƒ‰", placeholder="ê²€ìƒ‰ì–´ë¥¼ ìž…ë ¥í•˜ì„¸ìš”")
        with col2:
            process_options = ["ì „ì²´"]
            if not product_models_df.empty and "ê³µì •" in product_models_df.columns:
                process_options += sorted(product_models_df["ê³µì •"].unique().tolist())
            process_filter = st.selectbox("ê³µì • í•„í„°", options=process_options)
        
        # í•„í„°ë§ ì ìš©
        filtered_df = product_models_df.copy()
        if search_model and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["ëª¨ë¸ëª…"].str.contains(search_model, case=False)]
        if process_filter != "ì „ì²´" and not filtered_df.empty:
            filtered_df = filtered_df[filtered_df["ê³µì •"] == process_filter]
        
        # ê²°ê³¼ í‘œì‹œ
        if not filtered_df.empty:
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", format="%d"),
                    "ëª¨ë¸ëª…": st.column_config.TextColumn("ëª¨ë¸ëª…"),
                    "ê³µì •": st.column_config.TextColumn("ê³µì •")
                }
            )
        else:
            st.info("ê²€ìƒ‰ ì¡°ê±´ì— ë§žëŠ” ìƒì‚°ëª¨ë¸ì´ ì—†ìŠµë‹ˆë‹¤.")
    
    with tab2:
        st.subheader("ìƒì‚°ëª¨ë¸ ì¶”ê°€/ìˆ˜ì •")
        
        # ìž‘ì—… ì„ íƒì„ ë³„ë„ ì»´í¬ë„ŒíŠ¸ë¡œ ë¶„ë¦¬
        edit_mode = st.radio(
            "ìž‘ì—… ì„ íƒ", 
            ["ìƒˆ ëª¨ë¸ ì¶”ê°€", "ê¸°ì¡´ ëª¨ë¸ ìˆ˜ì •", "ëª¨ë¸ ì‚­ì œ"], 
            horizontal=True
        )
        
        st.markdown("---")
        
        # ìƒˆ ëª¨ë¸ ì¶”ê°€ ì–‘ì‹
        if edit_mode == "ìƒˆ ëª¨ë¸ ì¶”ê°€":
            st.subheader("ìƒˆ ëª¨ë¸ ì¶”ê°€")
            
            with st.form("add_model_form"):
                # ìƒˆ ID ìƒì„± (ê¸°ì¡´ ìµœëŒ€ ID + 1)
                new_id = 1
                if not product_models_df.empty and "id" in product_models_df.columns:
                    new_id = int(product_models_df["id"].max()) + 1
                
                st.number_input("ëª¨ë¸ ID", value=new_id, disabled=True, key="new_model_id")
                model_name = st.text_input("ëª¨ë¸ëª…", placeholder="ì˜ˆ: PA1, B7SUB6", key="new_model_name")
                process_name = st.text_input("ê³µì •", placeholder="ì˜ˆ: C1, C2, ì—°ì‚­", key="new_process")
                
                add_button = st.form_submit_button("ìƒì‚°ëª¨ë¸ ì¶”ê°€", use_container_width=True)
                
                if add_button:
                    if not model_name or not process_name:
                        st.error("ëª¨ë“  í•„ë“œë¥¼ ìž…ë ¥í•´ì£¼ì„¸ìš”.")
                    else:
                        # ìƒˆ ëª¨ë¸ ì¶”ê°€
                        new_model = {"id": new_id, "ëª¨ë¸ëª…": model_name, "ê³µì •": process_name}
                        updated_df = pd.concat([product_models_df, pd.DataFrame([new_model])], ignore_index=True)
                        
                        # ì €ìž¥
                        if save_product_models(updated_df):
                            st.success("ìƒì‚°ëª¨ë¸ì´ ì„±ê³µì ìœ¼ë¡œ ì¶”ê°€ë˜ì—ˆìŠµë‹ˆë‹¤!")
                            st.experimental_rerun()
                        else:
                            st.error("ìƒì‚°ëª¨ë¸ ì €ìž¥ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤.")
        
        # ê¸°ì¡´ ëª¨ë¸ ìˆ˜ì • ì–‘ì‹
        elif edit_mode == "ê¸°ì¡´ ëª¨ë¸ ìˆ˜ì •":
            st.subheader("ê¸°ì¡´ ëª¨ë¸ ìˆ˜ì •")
            
            # ìˆ˜ì •í•  ëª¨ë¸ì´ ìžˆëŠ”ì§€ í™•ì¸
            if product_models_df.empty:
                st.warning("ìˆ˜ì •í•  ìƒì‚°ëª¨ë¸ì´ ì—†ìŠµë‹ˆë‹¤. ë¨¼ì € ëª¨ë¸ì„ ì¶”ê°€í•´ì£¼ì„¸ìš”.")
            else:
                # ìˆ˜ì •í•  ëª¨ë¸ ì„ íƒ
                model_ids = product_models_df["id"].astype(str).tolist()
                model_labels = [f"{row['id']} - {row['ëª¨ë¸ëª…']} ({row['ê³µì •']})" for _, row in product_models_df.iterrows()]
                
                selected_id_index = st.selectbox(
                    "ìˆ˜ì •í•  ëª¨ë¸ ì„ íƒ", 
                    range(len(model_ids)), 
                    format_func=lambda i: model_labels[i],
                    key="edit_model_select"
                )
                
                selected_id = int(model_ids[selected_id_index])
                selected_row = product_models_df[product_models_df["id"] == selected_id].iloc[0]
                
                with st.form("edit_model_form"):
                    st.number_input("ëª¨ë¸ ID", value=selected_id, disabled=True, key="edit_model_id")
                    edited_model_name = st.text_input("ëª¨ë¸ëª…", value=selected_row["ëª¨ë¸ëª…"], key="edit_model_name")
                    edited_process = st.text_input("ê³µì •", value=selected_row["ê³µì •"], key="edit_process")
                    
                    edit_button = st.form_submit_button("ë³€ê²½ì‚¬í•­ ì €ìž¥", use_container_width=True)
                    
                    if edit_button:
                        if not edited_model_name or not edited_process:
                            st.error("ëª¨ë“  í•„ë“œë¥¼ ìž…ë ¥í•´ì£¼ì„¸ìš”.")
                        else:
                            # ëª¨ë¸ ì—…ë°ì´íŠ¸
                            updated_df = product_models_df.copy()
                            updated_df.loc[updated_df["id"] == selected_id, "ëª¨ë¸ëª…"] = edited_model_name
                            updated_df.loc[updated_df["id"] == selected_id, "ê³µì •"] = edited_process
                            
                            # ì €ìž¥
                            if save_product_models(updated_df):
                                st.success("ìƒì‚°ëª¨ë¸ì´ ì„±ê³µì ìœ¼ë¡œ ìˆ˜ì •ë˜ì—ˆìŠµë‹ˆë‹¤!")
                                st.experimental_rerun()
                            else:
                                st.error("ìƒì‚°ëª¨ë¸ ìˆ˜ì • ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤.")
        
        # ëª¨ë¸ ì‚­ì œ ì–‘ì‹
        else:  # ëª¨ë¸ ì‚­ì œ
            st.subheader("ëª¨ë¸ ì‚­ì œ")
            
            # ì‚­ì œí•  ëª¨ë¸ì´ ìžˆëŠ”ì§€ í™•ì¸
            if product_models_df.empty:
                st.warning("ì‚­ì œí•  ìƒì‚°ëª¨ë¸ì´ ì—†ìŠµë‹ˆë‹¤.")
            else:
                # ì‚­ì œí•  ëª¨ë¸ ì„ íƒ
                model_ids = product_models_df["id"].astype(str).tolist()
                model_labels = [f"{row['id']} - {row['ëª¨ë¸ëª…']} ({row['ê³µì •']})" for _, row in product_models_df.iterrows()]
                
                selected_id_index = st.selectbox(
                    "ì‚­ì œí•  ëª¨ë¸ ì„ íƒ", 
                    range(len(model_ids)), 
                    format_func=lambda i: model_labels[i],
                    key="delete_model_select"
                )
                
                selected_id = int(model_ids[selected_id_index])
                selected_row = product_models_df[product_models_df["id"] == selected_id].iloc[0]
                
                st.info(f"ì„ íƒí•œ ëª¨ë¸: {selected_row['ëª¨ë¸ëª…']} (ê³µì •: {selected_row['ê³µì •']})")
                
                with st.form("delete_model_form"):
                    confirm_delete = st.checkbox("ì‚­ì œë¥¼ í™•ì¸í•©ë‹ˆë‹¤", key="confirm_delete")
                    delete_button = st.form_submit_button("ëª¨ë¸ ì‚­ì œ", use_container_width=True)
                    
                    if delete_button:
                        if not confirm_delete:
                            st.error("ì‚­ì œë¥¼ í™•ì¸í•˜ë ¤ë©´ ì²´í¬ë°•ìŠ¤ë¥¼ ì„ íƒí•´ì£¼ì„¸ìš”.")
                        else:
                            # ëª¨ë¸ ì‚­ì œ
                            updated_df = product_models_df[product_models_df["id"] != selected_id].reset_index(drop=True)
                            
                            # ì €ìž¥
                            if save_product_models(updated_df):
                                st.success("ìƒì‚°ëª¨ë¸ì´ ì„±ê³µì ìœ¼ë¡œ ì‚­ì œë˜ì—ˆìŠµë‹ˆë‹¤!")
                                st.experimental_rerun()
                            else:
                                st.error("ìƒì‚°ëª¨ë¸ ì‚­ì œ ì¤‘ ì˜¤ë¥˜ê°€ ë°œìƒí–ˆìŠµë‹ˆë‹¤.")

