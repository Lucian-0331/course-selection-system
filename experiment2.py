import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import psycopg2
import numpy as np
from collections import defaultdict
import re
import random
import datetime
import streamlit.components.v1 as components
import json
import os

# ==========================================
# 🌟 雲端行為追蹤資料庫設定 (Supabase)
# ==========================================
# 🔑 終極連線字串 (已加入 sslmode=require 確保安全與連線穩定)
SUPABASE_URI = "postgresql://postgres.vtcpjriwbkvkimzlrfoo:Hh125974778@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

# 🚀 加上快取魔法：讓這段只在剛載入時跑一次，完美解決 1~2 秒的卡頓！
@st.cache_resource
def init_tracker_db():
    try:
        with psycopg2.connect(SUPABASE_URI) as conn:
            with conn.cursor() as cursor:
                # 這裡更新為 v5
                cursor.execute('''CREATE TABLE IF NOT EXISTS user_behavior_logs_v5 (
                                id SERIAL PRIMARY KEY,
                                時間 TEXT,
                                使用者行為 TEXT,
                                事件細節 TEXT,
                                x REAL,
                                y REAL,
                                url TEXT,
                                使用者id TEXT
                            )''')
            conn.commit()
        return True
    except Exception as e:
        print(f"Supabase Init Error: {e}")
        return False
        
init_tracker_db()

# ==========================================
# 1. 全局頁面設定與共用 CSS
# ==========================================
st.set_page_config(page_title="🎓 選課決策系統", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<meta name="google" content="notranslate">
<style>
    /* --- 全局共用 CSS --- */
    .stApp { background-color: #EAE6E3; }
    [data-testid="stSidebar"] { background-color: #F8F6F1; border-right: 1px solid #D4CCC5; }
    header { background-color: transparent !important; }
    
    /* 卡片與容器樣式 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; border-radius: 20px; border: none;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px); box-shadow: 0px 10px 24px rgba(160, 150, 140, 0.15);
    }
    
    h1, h2, h3, h4 { color: #333333 !important; font-weight: 800 !important; font-family: 'sans-serif'; }
    p, span, label { color: #555555 !important; font-family: 'sans-serif'; }
    
    /* 輸入框與下拉選單 */
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #F8F6F4 !important; color: #333333 !important; 
        border-radius: 10px !important; border: 1px solid #EAE6E3 !important; 
    }

    /* 按鈕樣式：法式奶油白 */
    .stButton>button, .stFormSubmitButton>button, [data-testid="stLinkButton"]>a { 
        width: 100%; border-radius: 20px; font-weight: 800;                        
        background-color: #EFEBE8 !important; border: 1px solid #DCD5CE !important;  
        color: #333333 !important; letter-spacing: 1px; transition: all 0.3s ease; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.04); height: 45px !important;
        text-decoration: none !important; display: inline-flex; align-items: center; justify-content: center;
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover, [data-testid="stLinkButton"]>a:hover { 
        background-color: #E4DCD3 !important; border-color: #D2C8BE !important;
        color: #111111 !important; box-shadow: 0 4px 12px rgba(180, 170, 160, 0.3); 
        transform: translateY(-2px);
    }
    
    /* 側邊欄按鈕微調 */
    [data-testid="stSidebar"] .stButton>button {
        background-color: transparent !important; border: none !important; box-shadow: none !important;
        text-align: left; justify-content: flex-start; font-size: 1.1rem; height: auto !important; margin-bottom: 5px;
    }
    [data-testid="stSidebar"] .stButton>button:hover { background-color: #EAE3DC !important; }

    .stProgress > div > div > div > div { background-color: #A3968C; }

    /* 首頁推薦標籤 (Tag) 樣式 */
    .tag { display: inline-block; background-color: #F0EBE6; color: #555555; padding: 4px 10px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; margin-right: 8px; margin-top: 8px; }
    .tag-match { background-color: #4A7C59; color: white; }
    .tag-hot { background-color: #C85A5A; color: white; }

    /* --- 課表專用 CSS --- */
    .timetable { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; font-size: 14px; table-layout: fixed; }
    .timetable th, .timetable td { border: 2px solid #EAE6E3; padding: 6px 4px; width: 16%; height: 75px; vertical-align: middle; word-wrap: break-word; overflow: hidden; }
    .timetable th { background-color: #F8F6F4; font-weight: 800; color: #555; border-radius: 5px; height: auto; padding: 10px 5px;}
    .timetable td { color: #888; }
    .timetable td.filled { background-color: #DCD7D4; font-weight: 900; color: #222; border-radius: 8px; font-size: 12px !important; line-height: 1.3; }
    .timetable td.conflict { background-color: #FADBD8; color: #C0392B; font-weight: 900; border: 2px solid #E74C3C; border-radius: 8px; font-size: 11px !important; line-height: 1.2; }
    .stats-card { background-color: #F8F6F4; padding: 15px; border-radius: 15px; border: 1px solid #EAE6E3; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🌟 實驗行為追蹤資料回傳處理 (Callback - 連線至 Supabase)
# ==========================================
def process_tracker_data():
    payload = st.session_state.tracker_bridge
    if not payload or str(payload).strip() == "": 
        return
        
    try:
        parsed = json.loads(payload)
        payload_id = str(parsed.get("id"))
        
        # 🛡️ 終極防線：使用 Set 集合記錄所有處理過的 ID，徹底斷絕重複寫入！
        if "processed_payloads" not in st.session_state:
            st.session_state.processed_payloads = set()
            
        if payload_id in st.session_state.processed_payloads:
            st.session_state.tracker_bridge = ""  # 嘗試清空殘留值
            return  # 這個 ID 已經寫入過了，直接擋在門外！
            
        st.session_state.processed_payloads.add(payload_id)
        
        logs = parsed.get("data", [])
        current_user_id = st.session_state.get("student_id", "Unknown_User")
            
        if logs:
            with psycopg2.connect(SUPABASE_URI) as conn:
                with conn.cursor() as cursor:
                    for log in logs:
                        # 這裡更新為 v5
                        cursor.execute('''INSERT INTO user_behavior_logs_v5 
                                          (時間, 使用者行為, 事件細節, x, y, url, 使用者id) 
                                          VALUES (%s, %s, %s, %s, %s, %s, %s)''', 
                                       (log.get('time'), log.get('action_type'), log.get('action_detail'),
                                        log.get('x'), log.get('y'), log.get('url'), current_user_id))
                conn.commit()
            st.session_state.tracker_msg = f"✅ 成功寫入 {len(logs)} 筆資料至雲端！(標籤: {current_user_id})"
            st.session_state.tracker_bridge = "" 
    except Exception as e:
        st.session_state.tracker_msg = f"❌ 雲端寫入失敗: {e}"

# ==========================================
# 2. 統一資料讀取函數 (🚀 導入網址參數、精準路徑與動態抽樣)
# ==========================================
url_params = st.query_params
# 抓取舊系統的課程 ID 參數 (預設 old_ed)
course_type = url_params.get("course", "old_ed")
session_key = f"sampled_courses_{course_type}"

if session_key not in st.session_state:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, '0610-course.db')

        with sqlite3.connect(db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            if not tables:
                raise ValueError(f"連線成功，但 {db_path} 裡面找不到任何資料表！")
            
            actual_table_name = tables[0][0]
            
            # 🔍 對應 old_ed 與 old_pro 進行篩選
            if course_type == "old_ed":
                query = f'SELECT * FROM "{actual_table_name}" WHERE 課程類別 LIKE \'%一般通識%\' ORDER BY RANDOM() LIMIT 8'
            elif course_type == "old_pro":
                query = f'SELECT * FROM "{actual_table_name}" WHERE 課程類別 LIKE \'%資訊類通識%\' ORDER BY RANDOM() LIMIT 8'
            else:
                query = f'SELECT * FROM "{actual_table_name}" ORDER BY RANDOM() LIMIT 8'
                
            df = pd.read_sql_query(query, conn)

    except Exception as e:
        st.error(f"⚠️ 資料庫讀取失敗！錯誤訊息: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=['選課代號', '配當系所.1', '開課班級簡稱', '科目簡稱', 'yms_smester', '系所', '開課班級', '課程名稱', '學期', '滿意度', '難度', '十八週進度', '評分標準'])
        df.loc[0] = ['無', '請選擇...', '請選擇...', '請選擇...', '1', '請選擇...', '請選擇...', '請選擇...', '上學期', 3.0, 3.0, '{}', '{}']
    else:
        df['系所'] = df['配當系所.1'].fillna('未知系所')
        df['開課班級'] = df['開課班級簡稱'].fillna('未知班級')
        df['課程名稱'] = df['科目簡稱'].astype(str) + " (" + df['開課班級'] + ")"

        def map_semester(x):
            x_str = str(x).strip()
            return '上學期' if x_str in ['1', '1.0'] else ('下學期' if x_str in ['2', '2.0'] else '(無)')
        
        df['學期'] = df['yms_smester'].apply(map_semester)
        df = df.drop_duplicates(subset=['選課代號', '學期']).reset_index(drop=True)
        
        np.random.seed(42)
        # 舊系統保留了「滿意度」與「難度」的欄位需求
        df['滿意度'] = np.random.uniform(2.5, 5.0, size=len(df)).round(1)
        df['難度'] = np.random.uniform(2.0, 5.0, size=len(df)).round(1)
        
    radar_dict = {}
    for _, row in df.iterrows():
        radar_dict[row['選課代號']] = np.random.uniform(1.5, 5.0, 5).round(1).tolist()
        
    st.session_state[session_key] = {"data": df, "radar": radar_dict}

data = st.session_state[session_key]["data"]
radar_data = st.session_state[session_key]["radar"]
categories = ["作業負擔", "考試難度", "實務性", "理論性", "互動程度"]

@st.cache_data
def get_fixed_trend_data(course_code):
    random.seed(course_code)
    return pd.DataFrame({"Year": ['109', '110', '111', '112', '113'], "Students": [random.randint(40, 120) for _ in range(5)], "AvgScore": [random.randint(65, 95) for _ in range(5)]})

# ==========================================
# 3. 初始化全局記憶體
# ==========================================
# 🌟 隱形標籤大法：從網址獲取 ID (例如 /?id=P01)
if 'student_id' not in st.session_state: 
    q_params = st.query_params
    st.session_state.student_id = q_params.get("id", "Unknown_User")

if 'current_page' not in st.session_state: st.session_state.current_page = "課程檢索系統"
if 'saved_dept' not in st.session_state: st.session_state.saved_dept = "請選擇..."
if 'saved_class' not in st.session_state: st.session_state.saved_class = "請選擇..."
if 'saved_semester' not in st.session_state: st.session_state.saved_semester = "請選擇..."
if 'saved_course' not in st.session_state: st.session_state.saved_course = "請選擇..."
if 'target_course_id' not in st.session_state: st.session_state.target_course_id = None 
if 'search_term' not in st.session_state: st.session_state.search_term = ""

if 'avatar' not in st.session_state: st.session_state.avatar = "https://www.w3schools.com/howto/img_avatar.png" 
if 'show_uploader' not in st.session_state: st.session_state.show_uploader = False

if 'last_chart_clicked_course' not in st.session_state: st.session_state.last_chart_clicked_course = None
if 'clear_signal' not in st.session_state: st.session_state.clear_signal = 0

if 'prefs' not in st.session_state:
    st.session_state.prefs = {
        "prof": {"🏭 生產與製造": False, "📈 品質管理": False, "💻 程式與資訊": False, "📊 數據分析": False, "⚙️ 系統模擬": False, "💼 科技管理": False},
        "cross": {"🌍 人文與歷史": False, "🎨 藝術與美學": False, "🏛️ 社會與心理": False, "⚖️ 法律與政治": False, "💰 經濟與商管": False, "🌱 自然與環境": False, "🗣️ 外語能力": False},
        "course": {"理論課": False, "實驗課": False, "線上課程": False, "混合制": False},
        "workload": "適中 😊"
    }

if 'my_courses' not in st.session_state: st.session_state.my_courses = []
for c in st.session_state.my_courses:
    if "enrolled" not in c: c["enrolled"] = False
if 'comments_db' not in st.session_state: st.session_state.comments_db = {}
if "name" not in st.session_state: st.session_state.name = "王小明 (Ming Wang)"
if "department" not in st.session_state: st.session_state.department = "工工系"
if "year" not in st.session_state: st.session_state.year = "三年級"
if "editing" not in st.session_state: st.session_state.editing = False

def navigate_to(page_name, course_id=None, course_name=None):
    st.session_state.current_page = page_name
    if course_id: st.session_state.target_course_id = course_id
    if course_name: st.session_state.saved_course = course_name

# ==========================================
# 4. 側邊欄導覽列與實驗控制面板
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>🎓 選課決策系統</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #DCD5CE; margin-bottom: 20px; text-align: center;'>
        <span style='font-size: 20px;'>👤</span><br>
        <span style='font-weight: 800; color: #333;'>{st.session_state.name}</span><br>
        <span style='font-size: 12px; color: #888;'>{st.session_state.department}</span>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔍 課程檢索系統", use_container_width=True): navigate_to("課程檢索系統")
    if st.button("❤️ 我的收藏", use_container_width=True): navigate_to("我的收藏")
    
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    
    with st.expander("👁️ 眼動儀實驗控制面板", expanded=True):
        st.markdown(f"<div style='color:#2E7D32; font-weight:bold; font-size:12px; margin-bottom:8px;'>目前受測者 ID: {st.session_state.student_id}</div>", unsafe_allow_html=True)
        
        # --- 🚀 終極隱形魔法：精準鎖定 TRACKER_BRIDGE 輸入框外層並移出畫面 ---
        st.markdown("""
        <style>
            div[data-testid="stTextInput"]:has(input[aria-label="TRACKER_BRIDGE"]) {
                position: absolute !important;
                left: -9999px !important;
                opacity: 0 !important;
                height: 0px !important;
                width: 0px !important;
                margin: 0 !important;
                padding: 0 !important;
                overflow: hidden !important;
                pointer-events: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # 這裡直接呼叫輸入框，CSS 會自動把它變不見
        st.text_input("TRACKER_BRIDGE", key="tracker_bridge", on_change=process_tracker_data, label_visibility="collapsed")
        
        if st.session_state.get("tracker_msg"):
            st.markdown(f"<div style='color:#1565C0; font-weight:bold; font-size:12px; margin-bottom:8px;'>{st.session_state.tracker_msg}</div>", unsafe_allow_html=True)
            
        # 2. 修改 tracker_html，將 btn-save 加上 display:none 隱藏
        tracker_html = f"""
        <div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px;">
            <button id="btn-start" style="padding:10px; background:#E8F5E9; color:#2E7D32; border:1px solid #C8E6C9; border-radius:8px; font-weight:bold; cursor:pointer;">▶️ 開啟行為追蹤 (1Hz 心跳)</button>
            <button id="btn-stop" style="display:none; padding:10px; background:#FFEBEE; color:#C62828; border:1px solid #FFCDD2; border-radius:8px; font-weight:bold; cursor:pointer;">⏸️ 暫停並強制上傳</button>
            <button id="btn-save" style="display:none;">💾 手動強制寫入</button>
            <div id="status-light" style="font-size:12px; font-weight:bold; color:#777; text-align:center;">本地暫存: 0 筆等待發送</div>
        </div>
        <script>
            // -----------------------------------------------------------
            // ⚠️ 這裡請保留你原本寫的所有 JavaScript 程式碼，完全不用動！
            // 從 const p = window.parent; 一直到 btnSave.onclick 結束的邏輯
            // -----------------------------------------------------------
            const p = window.parent;
            const d = p.document;
            const LOCAL_KEY = 'tracker_v4_backup';
            
            if(typeof p.__IS_TRACKING__ === 'undefined') p.__IS_TRACKING__ = false;
            
            const backSignal = "{st.session_state.clear_signal}";
            if (p.__CLEAR_SIG__ !== backSignal) {{
                localStorage.removeItem(LOCAL_KEY);
                p.__CLEAR_SIG__ = backSignal;
            }}
            
            p.__ADD_LOG__ = function(type, detail, x_pos = null, y_pos = null) {{
                if(!p.__IS_TRACKING__) return;
                
                const now = new Date();
                const ms = Date.now();
                const pad = (n, w=2) => String(n).padStart(w, '0');
                const timeStr = now.getFullYear() + '-' + pad(now.getMonth()+1) + '-' + pad(now.getDate()) + ' ' + 
                                pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds()) + 
                                '.' + pad(now.getMilliseconds(), 3);
                
                const scrollY = d.documentElement.scrollTop || d.body.scrollTop || 0;
                const vW = p.innerWidth;
                const vH = p.innerHeight;
                const dpr = p.devicePixelRatio || 1;
                
                const pageFlag = d.getElementById('current-page-flag');
                const section = pageFlag ? pageFlag.getAttribute('data-page') : '未知頁面';

                const logEntry = {{
                    time: timeStr, timestamp_ms: ms, scroll_y: scrollY, 
                    viewport_w: vW, viewport_h: vH, pixel_ratio: dpr, 
                    current_section: section, action_type: type, 
                    action_detail: detail, x: x_pos, y: y_pos, url: p.location.href
                }};
                
                let backup = JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]');
                backup.push(logEntry);
                localStorage.setItem(LOCAL_KEY, JSON.stringify(backup));
                updateUI();
            }};
            
            if (p.__HEARTBEAT__) clearInterval(p.__HEARTBEAT__);
            p.__HEARTBEAT__ = setInterval(() => {{
                if(p.__IS_TRACKING__) p.__ADD_LOG__('heartbeat', '系統定期快照', null, null);
            }}, 1000);
            
            p.__SEND_BATCH__ = function() {{
                let backup = JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]');
                if(backup.length === 0) return;
                
                try {{
                    const input = d.querySelector('input[aria-label="TRACKER_BRIDGE"]');
                    if(input) {{
                        const dataStr = JSON.stringify({{id: Date.now(), data: backup}});
                        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        input.focus();
                        nativeSetter.call(input, dataStr);
                        input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        
                        localStorage.removeItem(LOCAL_KEY);
                        updateUI();
                    }}
                }} catch(e) {{ console.error("發送失敗，保留於本地備份", e); }}
            }};
            
            if (p.__BATCH_TIMER__) clearInterval(p.__BATCH_TIMER__);
            p.__BATCH_TIMER__ = setInterval(() => {{
                if(p.__IS_TRACKING__) p.__SEND_BATCH__();
            }}, 30000);
            
            if (!p.__BEFORE_UNLOAD_LST__) {{
                window.addEventListener('beforeunload', function(e) {{
                    if(p.__IS_TRACKING__) {{
                        p.__IS_TRACKING__ = false;
                        p.__SEND_BATCH__(); 
                    }}
                }});
                p.__BEFORE_UNLOAD_LST__ = true;
            }}

            if (p.__CLICK_LST__) d.removeEventListener('click', p.__CLICK_LST__, true);
            if (p.__WHEEL_LST__) d.removeEventListener('wheel', p.__WHEEL_LST__, true);
            if (p.__INPUT_LST__) d.removeEventListener('input', p.__INPUT_LST__, true);
            if (p.__VIS_LST__) d.removeEventListener('visibilitychange', p.__VIS_LST__, true);
            
            p.__VIS_LST__ = function() {{
                if (d.visibilityState === 'hidden') {{
                    p.__ADD_LOG__('page_leave', '使用者離開介面 (切換分頁或隱藏視窗)', null, null);
                }} else if (d.visibilityState === 'visible') {{
                    p.__ADD_LOG__('page_return', '使用者返回介面', null, null);
                }}
            }};
            
            p.__CLICK_LST__ = function(e) {{
                let tagName = e.target.tagName ? e.target.tagName.toUpperCase() : 'UNKNOWN';
                let text = e.target.innerText || e.target.value || e.target.getAttribute('aria-label') || '';
                let cleanText = typeof text === 'string' ? text.substring(0, 50).trim().replace(/\\n/g, ' ') : '';
                
                if (tagName === 'PATH' || tagName === 'G' || tagName === 'SVG') {{
                    p.__ADD_LOG__('click_chart_element', '點擊圖表內部元素', e.clientX, e.clientY);
                }} else if (!cleanText && (tagName === 'DIV' || tagName === 'BODY' || tagName === 'HTML' || tagName === 'CANVAS')) {{
                    p.__ADD_LOG__('click_empty', '點擊無文字區塊 [' + tagName + ']', e.clientX, e.clientY);
                }} else {{
                    p.__ADD_LOG__('click_element', '[' + tagName + '] ' + cleanText, e.clientX, e.clientY);
                }}
            }};
            
            let lastWheel = 0;
            p.__WHEEL_LST__ = function(e) {{
                if(Date.now() - lastWheel > 300) {{
                    p.__ADD_LOG__('mouse_scroll', '視窗滾動 (DeltaY: ' + Math.round(e.deltaY) + ')', e.clientX, e.clientY);
                    lastWheel = Date.now();
                }}
            }};
            
            p.__INPUT_LST__ = function(e) {{
                let val = e.target.value || '';
                let cleanVal = val.substring(0, 50).trim();
                if(cleanVal) p.__ADD_LOG__('input', '[' + e.target.tagName + '] 輸入: ' + cleanVal, null, null); 
            }};
            
            d.addEventListener('visibilitychange', p.__VIS_LST__, true);
            d.addEventListener('click', p.__CLICK_LST__, true);
            d.addEventListener('wheel', p.__WHEEL_LST__, true);
            d.addEventListener('input', p.__INPUT_LST__, true);
            
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');
            const btnSave = document.getElementById('btn-save');
            const statusLight = document.getElementById('status-light');
            
            function updateUI() {{
                if(p.__IS_TRACKING__) {{
                    btnStart.style.display = 'none';
                    btnStop.style.display = 'block';
                }} else {{
                    btnStart.style.display = 'block';
                    btnStop.style.display = 'none';
                }}
                
                let backup = JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]');
                const count = backup.length;
                statusLight.innerText = `本地暫存: ${{count}} 筆等待發送 (每30秒自動同步)`;
                statusLight.style.color = count > 50 ? '#D32F2F' : (count > 0 ? '#F57C00' : '#388E3C');
            }}
            
            updateUI();
            if(window.__UI_TIMER__) clearInterval(window.__UI_TIMER__);
            window.__UI_TIMER__ = setInterval(updateUI, 1000); 
            
            btnStart.onclick = () => {{ 
                p.__IS_TRACKING__ = true; 
                p.__ADD_LOG__('experiment_start', '打板點擊：開始實驗', null, null);
                updateUI(); 
            }};
            
            btnStop.onclick = () => {{ 
                if(p.__IS_TRACKING__) {{
                    p.__ADD_LOG__('experiment_end', '打板點擊：結束實驗', null, null);
                }}
                
                p.__IS_TRACKING__ = false; 
                
                p.__SEND_BATCH__();
                updateUI(); 
            }};
            
            btnSave.onclick = () => {{
                p.__SEND_BATCH__();
                setTimeout(() => {{
                    if(JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]').length === 0) {{
                        alert('✅ 所有本地暫存資料已成功發送至雲端！');
                    }}
                }}, 500);
            }};
        </script>
        """
        
        # 將高度從 155 縮減為 115，因為少了一顆按鈕
        components.html(tracker_html, height=115)
        
       # 3. 移除雙欄配置與檢視資料表功能，單純保留清空紀錄按鈕
        if st.button("🗑️ 清空紀錄", use_container_width=True):
            try:
                with psycopg2.connect(SUPABASE_URI) as conn:
                    with conn.cursor() as cursor:
                        # 這裡更新為 v5
                        cursor.execute("TRUNCATE TABLE user_behavior_logs_v5 RESTART IDENTITY;")
                    conn.commit()
                st.session_state.clear_signal += 1 
                st.success("✅ 雲端與本地行為紀錄已徹底清空！")
                st.rerun()
            except Exception as e:
                st.error(f"清空失敗: {e}")

# ==========================================
# 5. 路由系統
# ==========================================
if st.session_state.current_page == "課程檢索系統":
    st.markdown("""
    <style>
        .stApp { overflow: hidden !important; max-height: 100vh; }
        .block-container { padding-top: 3rem; padding-bottom: 0; max-height: 100vh; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 15px;'>🔍 課程檢索</h2>", unsafe_allow_html=True)

    col_left, col_right = st.columns([4, 6])

    # ==========================================
    # 左欄 (4)：條件篩選面板 (固定高度 650px)
    # ==========================================
    with col_left:
        with st.container(height=650, border=True):
            st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:10px;'>🔍 全站課程搜尋</div>", unsafe_allow_html=True)
            # 實驗防呆：搜尋框禁用
            search_term = st.text_input("搜尋關鍵字", key="search_term", placeholder="實驗鎖定中，禁用搜尋", disabled=True, label_visibility="collapsed")
            
            st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:10px; margin-top:15px;'>📂 條件篩選面板</div>", unsafe_allow_html=True)

            filtered = data  # 直接使用抽樣的 8 門課
            
            # 實驗鎖定：自動選取第一個真實資料，並禁用下拉選單
            dept_options = ["請選擇..."] + sorted(data["系所"].unique().tolist())
            dept = st.selectbox("1. 系所：", dept_options, index=1 if len(dept_options) > 1 else 0, disabled=True)
            st.session_state.saved_dept = dept
            
            class_options = ["請選擇..."] + sorted(data[data["系所"]==dept]["開課班級"].unique().tolist()) if dept != "請選擇..." else ["請選擇..."]
            class_sel = st.selectbox("2. 開課班級：", class_options, index=1 if len(class_options) > 1 else 0, disabled=True)
            st.session_state.saved_class = class_sel
            
            sem_options = ["請選擇..."] + sorted(data[(data["系所"]==dept) & (data["開課班級"]==class_sel)]["學期"].unique().tolist()) if class_sel != "請選擇..." else ["請選擇..."]
            semester_sel = st.selectbox("3. 學期：", sem_options, index=1 if len(sem_options) > 1 else 0, disabled=True)
            st.session_state.saved_semester = semester_sel
            
            # 第 4 項：目標課程 (開放點選，列出所有 8 門課)
            course_options = ["請選擇..."] + filtered["課程名稱"].tolist()
            crs_idx = course_options.index(st.session_state.saved_course) if st.session_state.saved_course in course_options else 0
            selected_course = st.selectbox("4. 課程：", course_options, index=crs_idx)
            
            if selected_course != st.session_state.saved_course:
                st.session_state.saved_course = selected_course
                if selected_course != "請選擇...":
                    matched_id = filtered[filtered['課程名稱'] == selected_course]['選課代號'].tolist()
                    if matched_id: st.session_state.target_course_id = matched_id[0]
                else:
                    st.session_state.target_course_id = None

            def reset_all():
                st.session_state.saved_dept = "請選擇..."
                st.session_state.saved_class = "請選擇..."
                st.session_state.saved_semester = "請選擇..."
                st.session_state.saved_course = "請選擇..."
                st.session_state.target_course_id = None
                st.session_state.search_term = ""
            st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True) 
            st.button("🔄 重置條件", on_click=reset_all, use_container_width=True)

    # ==========================================
    # 右欄 (6)：課程完整資訊 (按鈕固定於底部)
    # ==========================================
    with col_right:
        with st.container(height=650, border=True):
            target_course_name = selected_course if selected_course not in ["請選擇...", "先選學期...", "查無結果..."] else None

            if not target_course_name:
                st.info("👈 請從左側選單挑選課程，以查看詳細資訊。")
            else:
                with st.container(height=530, border=False):
                    course_info = filtered[filtered["課程名稱"] == target_course_name].iloc[0]
                    current_code = str(course_info['選課代號'] if '選課代號' in course_info else "Unknown")
                    year_str = str(course_info.get('yms_year', '未知年次'))
                    sem_str = str(course_info.get('學期', '未知學期'))
                    selected_uid = f"[{year_str}-{sem_str}] [{current_code}] {target_course_name}"

                    st.markdown(f"### 📌 課程完整資訊")
                    st.markdown(f"<div style='background-color: #E2DCD5; padding: 6px 16px; border-radius: 8px; display: inline-block; margin-bottom: 18px; font-weight: bold; color: #222; border: 1px solid #D0C8C0;'>{selected_uid}</div>", unsafe_allow_html=True)
                    
                    target_cols = ['選課代號', '開課班級', '科目簡稱', '學分數', '學分', '必選修', '上課時間', 'EMI註記', '授課方式', '授課語言', '系所', '課程描述_中', '課程描述_英']
                    col_info1, col_info2 = st.columns(2)
                    display_index = 0
                    
                    for col_name in target_cols:
                        if col_name not in course_info.index: continue
                        val = course_info[col_name]
                        if col_name == '必選修':
                            val = '必修' if str(val).upper() == 'M' else '選修' if str(val).upper() == 'O' else val
                        
                        if isinstance(val, str) and len(val) > 25:
                            st.markdown(f"<div style='margin-bottom: 14px; background-color: #F8F6F1; padding: 16px; border-radius: 12px; border: 1px solid #E2DCD5;'><span style='font-weight: 800; color: #444; font-size: 1.05rem;'>📑 {col_name}：</span><br><span style='color: #222; font-weight: 600; font-size: 1rem; line-height: 1.6; display: inline-block; margin-top: 8px;'>{val}</span></div>", unsafe_allow_html=True)
                        else:
                            content = f"<div style='margin-bottom: 12px;'><span style='font-weight: 600; color: #555;'>{col_name}：</span> <span style='color: #111; font-weight: 900; font-size: 1.05rem;'>{val}</span></div>"
                            if display_index % 2 == 0:
                                with col_info1: st.markdown(content, unsafe_allow_html=True)
                            else:
                                with col_info2: st.markdown(content, unsafe_allow_html=True)
                            display_index += 1

                    # 🚀 評分標準 (對照組：純文字設計)
                    if '評分標準' in course_info:
                        grading_raw = course_info['評分標準']
                        grading_dict = {}
                        if pd.notna(grading_raw) and str(grading_raw).strip() != "":
                            try:
                                if isinstance(grading_raw, dict): grading_dict = grading_raw
                                else: grading_dict = json.loads(str(grading_raw).replace("'", '"'))
                            except: pass
                        
                        if grading_dict:
                            st.markdown("<div style='margin-top: 15px; background-color: #F8F6F1; padding: 16px; border-radius: 12px; border: 1px solid #E2DCD5;'><span style='font-weight: 800; color: #444; font-size: 1.05rem;'>📑 評分比例與標準：</span><br>", unsafe_allow_html=True)
                            for item, desc in grading_dict.items():
                                st.markdown(f"<span style='color: #222; font-weight: 600; font-size: 1rem; line-height: 1.6; display: block; margin-top: 5px;'>{item}：{desc}</span>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                    # 🚀 十八週進度 (對照組：純文字設計)
                    if '十八週進度' in course_info:
                        syllabus_raw = course_info['十八週進度']
                        syllabus_dict = {}
                        if pd.notna(syllabus_raw) and str(syllabus_raw).strip() != "":
                            try:
                                if isinstance(syllabus_raw, dict): syllabus_dict = syllabus_raw
                                else: syllabus_dict = json.loads(str(syllabus_raw).replace("'", '"'))
                            except: pass
                        
                        if syllabus_dict:
                            st.markdown("<div style='margin-top: 15px; background-color: #F8F6F1; padding: 16px; border-radius: 12px; border: 1px solid #E2DCD5;'><span style='font-weight: 800; color: #444; font-size: 1.05rem;'>🗓️ 十八週課程大綱：</span><br>", unsafe_allow_html=True)
                            for i in range(1, 19):
                                w_key = f"W{i}"
                                w_content = syllabus_dict.get(w_key, "無資料")
                                st.markdown(f"<span style='color: #222; font-weight: 600; font-size: 1rem; line-height: 1.6; display: block; margin-top: 5px;'>第{i}週：{w_content}</span>", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div style='border-top: 1px solid #EAE6E3; margin: 10px 0;'></div>", unsafe_allow_html=True)
                col_btn1, col_btn2, col_btn3 = st.columns(3)
                
                with col_btn1:
                    if st.button("❤️ 加入收藏", key="pure_add_fav", use_container_width=True):
                        if any(c['id'] == current_code for c in st.session_state.my_courses): 
                            st.toast(f"「{target_course_name}」已經在您的收藏清單中囉！", icon="⚠️")
                        else:
                            c_type_raw = str(course_info.get('必選修', '選修')).upper()
                            c_type = '必修' if c_type_raw == 'M' else '選修'
                            try: credits = int(float(course_info.get('學分', 2)))
                            except: credits = 2
                            raw_time = str(course_info.get('上課時間', '')).replace(" ", "")
                            time_slots = []
                            for match in re.finditer(r'\(?([一二三四五六日])\)?([0-9A-Za-z,\-~]+)', raw_time):
                                day, periods_str = match.group(1), match.group(2)
                                for part in re.split(r'[,、]', periods_str):
                                    if '-' in part or '~' in part:
                                        try:
                                            s_str, e_str = part.split('-' if '-' in part else '~')
                                            if s_str.isdigit() and e_str.isdigit():
                                                for p in range(int(s_str), int(e_str) + 1): time_slots.append(f"{day}{p}")
                                            else: time_slots.extend([f"{day}{s_str.upper()}", f"{day}{e_str.upper()}"])
                                        except: pass 
                                    else: time_slots.append(f"{day}{int(part)}" if part.isdigit() else f"{day}{part.upper()}")
                            st.session_state.my_courses.append({"id": current_code, "name": target_course_name, "time": time_slots, "credits": credits, "type": c_type, "enrolled": False})
                            st.toast(f"已將「{target_course_name}」加入您的收藏清單！", icon="✨")
                
                with col_btn2:
                    st.button("➕ 前往模擬排課", key="pure_go_sim", use_container_width=True, on_click=navigate_to, args=("我的收藏",))
                    
                with col_btn3:
                    st.button("🔗 學校選課系統", key="pure_dummy_link", use_container_width=True)

elif st.session_state.current_page == "我的收藏":
    # ==========================================
    # 👑 [我的收藏 - 原生安全鎖定版 CSS] 
    # ==========================================
    st.markdown("""
    <style>
        /* --- 1. 全局鎖定 (Global Lock)：鎖死最外層，不讓整個網頁滑動 --- */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
        }
        .block-container {
            height: 94vh !important; 
            max-width: 96% !important; 
            padding: 1.5rem 0 1rem 0 !important; 
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important; /* 確保外層絕對不出現滾動條 */
        }
        
        /* 讓主垂直區塊變成 Flex 容器，穩定撐開高度 */
        div[data-testid="stVerticalBlock"]:first-of-type {
            display: flex; flex-direction: column; height: 100%;
        }

        /* --- 原本的課表與卡片極致壓縮 CSS (完全保留) --- */
        .timetable-full {
            width: 100%;
            height: 450px !important; 
            border-collapse: collapse;
            table-layout: fixed;
            background-color: white;
        }
        .timetable-full th, .timetable-full td {
            border: 1px solid #EAE6E3;
            text-align: center;
            vertical-align: middle;
            font-size: 11px;
            height: 45px !important; 
        }
        .timetable-full th { background-color: #F8F6F4; font-weight: 800; }
        .timetable-full td.filled {
            background-color: #DCD7D4; color: #222; font-weight: 900;
            border-radius: 4px; font-size: 11px !important; line-height: 1.1;
        }
        .timetable-full td.conflict {
            background-color: #FADBD8; color: #C0392B; font-weight: bold; font-size: 11px !important;
        }

        .fav-card {
            background-color: #F8F6F4; border: 1px solid #EAE6E3;
            border-radius: 10px; padding: 6px 12px;  
            margin-bottom: 6px; display: flex; align-items: center; min-height: 40px;   
        }
        .fav-enrolled {
            border-left: 6px solid #4A7C59 !important; background-color: #F0F4F0 !important;
        }

        [data-testid="column"]:nth-child(1) .stButton>button {
            height: 32px !important; min-height: 32px !important;
            padding: 2px 10px !important; font-size: 0.8rem !important;
        }

        /* --- 2. 內層解放 (Local Scroll)：取代原本的暴力隱藏 --- */
        /* 針對候選清單與課表的內部容器，開啟獨立滾動 */
        [data-testid="stVerticalBlockBorderWrapper"]:has(.timetable-full) > div > div,
        [data-testid="stVerticalBlockBorderWrapper"]:has(.fav-card) > div > div {
            overflow-y: auto !important; /* 解除封印，允許內部滾動 */
            overscroll-behavior: contain !important; /* 避免內部滾動到底時，意外牽動外層 */
            padding-right: 5px; /* 留一點空間給滾動條，避免遮擋文字 */
        }

        /* 美化滾動軸 (讓它看起來更精緻，不破壞你原本的設計感) */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background-color: #E2DCD5; border-radius: 10px; }

        /* 隱藏原生容器多餘的間距 */
        .block-container [data-testid="stVerticalBlock"] > div { padding: 0 !important; }
    </style>
    """, unsafe_allow_html=True)

    # ✨ 標題保留
    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px;'>❤️ 我的收藏與模擬排課</h2>", unsafe_allow_html=True)

    all_favorites = st.session_state.my_courses
    enrolled_courses = [c for c in all_favorites if c["enrolled"]]

    # 🚀 修復 KeyError：支援全時段陣列
    days = ["一", "二", "三", "四", "五", "六", "日"]
    all_periods = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "A", "B", "C", "D"] 
    schedule_matrix = {d: {p: [] for p in all_periods} for d in days}
    conflicts = []
    
    # 將已選課程填入矩陣
    for course in enrolled_courses:
        for t in course["time"]:
            if len(t) >= 2:
                d_key = t[0]
                p_key = str(int(t[1:])) if t[1:].isdigit() else t[1:]
                if d_key in schedule_matrix and p_key in schedule_matrix[d_key]: 
                    schedule_matrix[d_key][p_key].append(course)

    # 建立左右 1:1 分區
    col_l, col_r = st.columns(2)

    # ==========================================
    # 🔴 左側：候選清單 
    # ==========================================
    with col_l:
        with st.container(height=650, border=True): 
            c_header_l, c_header_r = st.columns([3, 1])
            c_header_l.markdown("#### 📝 候選清單")
            if c_header_r.button("🗑️ 清空", key="btn_clear_all", use_container_width=True):
                st.session_state.my_courses = []
                st.rerun()
            
            st.markdown("<hr style='margin: 8px 0;'>", unsafe_allow_html=True)
            
            if not all_favorites:
                st.info("目前尚無收藏課程")
            else:
                for idx, course in enumerate(all_favorites):
                    is_enrolled = course["enrolled"]
                    
                    # 🚀 安全的衝堂檢查邏輯
                    is_conf = False
                    if is_enrolled:
                        for t in course["time"]:
                            if len(t) >= 2:
                                d_k, p_k = t[0], str(int(t[1:])) if t[1:].isdigit() else t[1:]
                                if d_k in schedule_matrix and p_k in schedule_matrix[d_k] and len(schedule_matrix[d_k][p_k]) > 1:
                                    is_conf = True
                                    break
                    
                    card_style = "fav-enrolled" if is_enrolled else ""
                    status_ico = "⛔" if is_conf else ("✅" if is_enrolled else "⚪")
                    
                    # ✨ 修改：時間翻譯機！將 ['一6', '一7', '一8'] 轉換為 (一) 6-8
                    formatted_time = "未定"
                    if course['time']:
                        day_dict = defaultdict(list)
                        for t in course['time']:
                            if len(t) >= 2:
                                day_dict[t[0]].append(int(t[1:]) if t[1:].isdigit() else t[1:])
                        time_parts = []
                        for d, periods in day_dict.items():
                            if all(isinstance(p, int) for p in periods):
                                periods.sort()
                                if len(periods) > 1 and periods[-1] - periods[0] == len(periods) - 1:
                                    time_parts.append(f"({d}) {periods[0]}-{periods[-1]}")
                                else:
                                    time_parts.append(f"({d}) {','.join(map(str, periods))}")
                            else:
                                time_parts.append(f"({d}) {','.join(map(str, periods))}")
                        formatted_time = " ".join(time_parts)

                    # ✨ 修改：將代碼與「翻譯後的時間」合併成單行
                    ci, ca, cd = st.columns([3.5, 1.2, 0.6])
                    ci.markdown(f"""
                        <div class="fav-card {card_style}">
                            <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                <span style="font-size: 13px; font-weight: 800; color: #333;">{status_ico} {course['name']}</span>
                                <span style="font-size: 11px; color: #888; margin-left: 6px;">({course['id']} | {formatted_time})</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if is_enrolled:
                        if ca.button("退選", key=f"d_{idx}", use_container_width=True):
                            st.session_state.my_courses[idx]["enrolled"] = False; st.rerun()
                    else:
                        if ca.button("加選", key=f"a_{idx}", use_container_width=True):
                            st.session_state.my_courses[idx]["enrolled"] = True; st.rerun()
                    
                    if cd.button("🗑️", key=f"x_{idx}", use_container_width=True):
                        st.session_state.my_courses.pop(idx); st.rerun()

    # ==========================================
    # 🟡 右側：預覽課表 
    # ==========================================
    with col_r:
        with st.container(height=650, border=True):
            # 1. 衝突提醒
            for d in days:
                for p in all_periods:
                    cells = schedule_matrix[d][p]
                    if len(cells) > 1:
                        msg = f"週{d} 第{p}節：{' & '.join([c['name'] for c in cells])}"
                        if msg not in conflicts: conflicts.append(msg)

            if conflicts:
                st.markdown(f"<div style='background-color: #FADBD8; border-left: 4px solid #E74C3C; padding: 6px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 12px; color: #C0392B; font-weight: bold;'>⚠️ 發現 {len(conflicts)} 處衝堂</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='background-color: #E8F5E9; border-left: 4px solid #2E7D32; padding: 6px 12px; border-radius: 4px; margin-bottom: 8px; font-size: 12px; color: #2E7D32; font-weight: bold;'>✅ 目前課表狀態良好</div>", unsafe_allow_html=True)

            st.markdown("<h4 style='text-align: center; margin: 5px 0 10px 0;'>📅 預覽課表</h4>", unsafe_allow_html=True)

            # 🚀 動態決定要顯示的節次 (至少 1~10，有晚課才往下延伸)
            display_periods = [p for p in all_periods if p in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"] or any(schedule_matrix[d][p] for d in days)]
            
            # 🚀 動態決定要顯示的天數 (有六日才顯示週末)
            display_days = ["一", "二", "三", "四", "五"]
            for d in ["六", "日"]:
                if any(schedule_matrix[d][p] for p in display_periods):
                    display_days.append(d)

            # 2. 繪製自動延展表格
            table_html = f"<table class='timetable-full'><tr><th style='width:30px;'></th>" + "".join([f"<th>週{d}</th>" for d in display_days]) + "</tr>"
            for p in display_periods:
                table_html += f"<tr><td style='font-weight:bold; background:#F8F6F4;'>{p}</td>"
                for d in display_days:
                    cells = schedule_matrix[d][p]
                    if not cells:
                        table_html += "<td></td>"
                    elif len(cells) == 1:
                        name = cells[0]['name'][:7] + ".." if len(cells[0]['name']) > 7 else cells[0]['name']
                        table_html += f"<td class='filled'>{name}</td>"
                    else:
                        table_html += f"<td class='conflict'>!!!</td>"
                table_html += "</tr>"
            table_html += "</table>"
            
            st.markdown(table_html, unsafe_allow_html=True)