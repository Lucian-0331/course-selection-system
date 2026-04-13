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

# ==========================================
# 🌟 雲端行為追蹤資料庫設定 (Supabase V4)
# ==========================================
SUPABASE_URI = "postgresql://postgres.vtcpjriwbkvkimzlrfoo:Hh125974778@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

@st.cache_resource
def init_tracker_db():
    try:
        with psycopg2.connect(SUPABASE_URI) as conn:
            with conn.cursor() as cursor:
                cursor.execute('''CREATE TABLE IF NOT EXISTS user_behavior_logs_v4 (
                                id SERIAL PRIMARY KEY,
                                時間 TEXT,
                                timestamp_ms BIGINT,
                                scroll_y REAL,
                                viewport_w INT,
                                viewport_h INT,
                                pixel_ratio REAL,
                                current_section TEXT,
                                action_type TEXT,
                                action_detail TEXT,
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
    
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #F8F6F4 !important; color: #333333 !important; 
        border-radius: 10px !important; border: 1px solid #EAE6E3 !important; 
    }

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
    
    /* --- 替換這段側邊欄按鈕樣式 --- */
    [data-testid="stSidebar"] .stButton>button {
        background-color: transparent !important; 
        border: none !important; 
        box-shadow: none !important;
        text-align: left !important; 
        justify-content: flex-start !important; 
        font-size: 1.1rem !important; 
        height: auto !important; 
        padding: 10px 15px !important; /* 增加內距讓按鈕有呼吸空間 */
        margin-bottom: 8px !important; /* 增加按鈕之間的上下距離 */
        display: flex !important;      /* 強制啟用 Flex 佈局 */
        align-items: center !important;
        gap: 12px !important;          /* 強制隔開 Emoji 與文字 */
    }
    [data-testid="stSidebar"] .stButton>button:hover { 
        background-color: #EAE3DC !important; 
        transform: translateY(0px) !important; /* 覆蓋掉全域的懸浮跳動，讓側邊欄保持穩定 */
    }

    .stProgress > div > div > div > div { background-color: #A3968C; }

    .tag { display: inline-block; background-color: #F0EBE6; color: #555555; padding: 4px 10px; border-radius: 8px; font-size: 0.85rem; font-weight: 600; margin-right: 8px; margin-top: 8px; }
    .tag-match { background-color: #4A7C59; color: white; }
    .tag-hot { background-color: #C85A5A; color: white; }

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
# 🌟 實驗行為追蹤資料回傳處理
# ==========================================
def process_tracker_data():
    payload = st.session_state.tracker_bridge
    if not payload or str(payload).strip() == "": 
        return
        
    try:
        parsed = json.loads(payload)
        payload_id = str(parsed.get("id"))
        
        if "processed_payloads" not in st.session_state:
            st.session_state.processed_payloads = set()
            
        if payload_id in st.session_state.processed_payloads:
            st.session_state.tracker_bridge = "" 
            return 
            
        st.session_state.processed_payloads.add(payload_id)
        
        logs = parsed.get("data", [])
        current_user_id = st.session_state.get("student_id", "Unknown_User")
            
        if logs:
            with psycopg2.connect(SUPABASE_URI) as conn:
                with conn.cursor() as cursor:
                    for log in logs:
                        cursor.execute('''INSERT INTO user_behavior_logs_v4 
                                          (時間, timestamp_ms, scroll_y, viewport_w, viewport_h, pixel_ratio, 
                                           current_section, action_type, action_detail, x, y, url, 使用者id) 
                                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''', 
                                       (log.get('time'), log.get('timestamp_ms'), log.get('scroll_y'), 
                                        log.get('viewport_w'), log.get('viewport_h'), log.get('pixel_ratio'), 
                                        log.get('current_section'), log.get('action_type'), log.get('action_detail'),
                                        log.get('x'), log.get('y'), log.get('url'), current_user_id))
                conn.commit()
            st.session_state.tracker_msg = f"✅ 成功批次寫入 {len(logs)} 筆資料至雲端！(標籤: {current_user_id})"
            st.session_state.tracker_bridge = "" 
    except Exception as e:
        st.session_state.tracker_msg = f"❌ 雲端寫入失敗: {e}"

# ==========================================
# 2. 統一資料讀取函數
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    try:
        with sqlite3.connect('courses.db', timeout=10) as conn:
            df = pd.read_sql_query("SELECT * FROM official_courses ORDER BY 選課代號", conn)
        df['系所'] = df['配當系所.1'].fillna('未知系所')
        df['開課班級'] = df['開課班級簡稱'].fillna('未知班級')
        df['課程名稱'] = df['科目簡稱'] + " (" + df['開課班級'] + ")"
        def map_semester(x):
            x_str = str(x).strip()
            if x_str in ['1', '1.0']: return '上學期'
            if x_str in ['2', '2.0']: return '下學期'
            return '(無)'
        df['學期'] = df['yms_smester'].apply(map_semester)
        df = df.drop_duplicates(subset=['選課代號', '學期']).reset_index(drop=True)
        
        np.random.seed(42)
        df['滿意度'] = np.random.uniform(2.5, 5.0, size=len(df)).round(1)
        df['難度'] = np.random.uniform(2.0, 5.0, size=len(df)).round(1)
        
        radar_dict = {}
        for _, row in df.iterrows():
            radar_dict[row['選課代號']] = np.random.uniform(1.5, 5.0, 5).round(1).tolist()
        return df, radar_dict
    except Exception as e:
        return pd.DataFrame(), {}

data, radar_data = load_data()
categories = ["作業負擔", "考試難度", "實務性", "理論性", "互動程度"]

@st.cache_data
def get_fixed_trend_data(course_code):
    random.seed(course_code)
    return pd.DataFrame({"Year": ['109', '110', '111', '112', '113'], "Students": [random.randint(40, 120) for _ in range(5)], "AvgScore": [random.randint(65, 95) for _ in range(5)]})

# ==========================================
# 3. 初始化全局記憶體
# ==========================================
if 'student_id' not in st.session_state: 
    q_params = st.query_params
    st.session_state.student_id = q_params.get("id", "Unknown_User")

if 'current_page' not in st.session_state: st.session_state.current_page = "系統首頁"
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
    
    if st.button("🏠 系統首頁", use_container_width=True): navigate_to("系統首頁")
    if st.button("📊 視覺化介面", use_container_width=True): navigate_to("視覺化介面")
    if st.button("❤️ 我的收藏", use_container_width=True): navigate_to("我的收藏")
    if st.button("⚙️ 個人設定", use_container_width=True): navigate_to("個人設定")
    
    st.markdown("<hr style='margin:15px 0;'>", unsafe_allow_html=True)
    
    with st.expander("👁️ 眼動儀實驗控制面板", expanded=True):
        st.markdown(f"<div style='color:#2E7D32; font-weight:bold; font-size:12px; margin-bottom:8px;'>目前受測者 ID: {st.session_state.student_id}</div>", unsafe_allow_html=True)
        
        st.markdown('<div style="position:absolute; left:-9999px; opacity:0; width:1px; height:1px;">', unsafe_allow_html=True)
        st.text_input("TRACKER_BRIDGE", key="tracker_bridge", on_change=process_tracker_data)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.session_state.get("tracker_msg"):
            st.markdown(f"<div style='color:#1565C0; font-weight:bold; font-size:12px; margin-bottom:8px;'>{st.session_state.tracker_msg}</div>", unsafe_allow_html=True)
            
        tracker_html = f"""
        <div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px;">
            <button id="btn-start" style="padding:10px; background:#E8F5E9; color:#2E7D32; border:1px solid #C8E6C9; border-radius:8px; font-weight:bold; cursor:pointer;">▶️ 開啟行為追蹤 (1Hz 心跳)</button>
            <button id="btn-stop" style="display:none; padding:10px; background:#FFEBEE; color:#C62828; border:1px solid #FFCDD2; border-radius:8px; font-weight:bold; cursor:pointer;">⏸️ 暫停並強制上傳</button>
            <button id="btn-save" style="padding:10px; background:#E3F2FD; color:#1565C0; border:1px solid #BBDEFB; border-radius:8px; font-weight:bold; cursor:pointer;">💾 手動強制寫入</button>
            <div id="status-light" style="font-size:12px; font-weight:bold; color:#777; text-align:center;">本地暫存: 0 筆等待發送</div>
        </div>
        <script>
            const p = window.parent;
            const d = p.document;
            const LOCAL_KEY = 'tracker_v4_backup';
            
            if(typeof p.__IS_TRACKING__ === 'undefined') p.__IS_TRACKING__ = false;
            
            const backSignal = "{st.session_state.clear_signal}";
            if (p.__CLEAR_SIG__ !== backSignal) {{
                localStorage.removeItem(LOCAL_KEY);
                p.__CLEAR_SIG__ = backSignal;
            }}
            
            // 🌟 終極語意標籤偵測引擎：頁面識別 + 由下而上 (Bottom-Up) 判定邏輯
            function getCurrentSection(vH) {{
                // 1. 先抓取 Python 埋入的頁面身分證
                const pageFlag = d.getElementById('current-page-flag');
                const pageName = pageFlag ? pageFlag.getAttribute('data-page') : '未知頁面';

                if (pageName === '系統首頁') return '首頁導覽';
                if (pageName === '我的收藏') return '排課與收藏區';
                if (pageName === '個人設定') return '個人設定區';

                // 判斷元素是否出現在畫面的輔助函數 (只要頂端進入畫面底部，且尚未完全滾出畫面)
                const isVisible = (id) => {{
                    const el = d.getElementById(id);
                    if (!el) return false;
                    const rect = el.getBoundingClientRect();
                    return (rect.top < vH * 0.8 && rect.top > -600); 
                }};

                // 2. 依照不同頁面，進行「由下而上」的判定
                if (pageName === '視覺化介面') {{
                    if (isVisible('zone-v-radar')) return '雷達圖與綜合資訊區';
                    if (isVisible('zone-v-scatter')) return '散點圖選課區';
                    if (isVisible('zone-v-filter')) return '條件篩選面板';
                    return '視覺化介面_瀏覽中';
                }}

                if (pageName === '詳細課程') {{
                    if (isVisible('zone-d-comment')) return '留言與討論區';
                    if (isVisible('zone-d-trend')) return '歷年修課趨勢(折線圖)';
                    if (isVisible('zone-d-info')) return '課程文字詳細資訊';
                    return '詳細課程_瀏覽中';
                }}

                return pageName + '_瀏覽中';
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
                
                // 動態取得目前精確區塊
                const section = getCurrentSection(vH);

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
                // 1. 在關機前，先強制記錄一個「結束實驗」的動作
                if(p.__IS_TRACKING__) {{
                    p.__ADD_LOG__('experiment_end', '打板點擊：結束實驗', null, null);
                }}
                
                // 2. 記錄完遺言後，才正式關閉追蹤
                p.__IS_TRACKING__ = false; 
                
                // 3. 把最後一包資料送出去
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
        components.html(tracker_html, height=155)
        
        col_db1, col_db2 = st.columns(2)
        with col_db1:
            if st.button("📊 檢視資料表", use_container_width=True):
                st.session_state.show_tracker_db = not st.session_state.get("show_tracker_db", False)
        with col_db2:
            if st.button("🗑️ 清空紀錄", use_container_width=True):
                try:
                    with psycopg2.connect(SUPABASE_URI) as conn:
                        with conn.cursor() as cursor:
                            cursor.execute("TRUNCATE TABLE user_behavior_logs_v4 RESTART IDENTITY;")
                        conn.commit()
                    st.session_state.clear_signal += 1 
                    st.success("✅ 雲端與本地行為紀錄已徹底清空！")
                    st.rerun()
                except Exception as e:
                    st.error(f"清空失敗: {e}")
                    
        if st.session_state.get("show_tracker_db", False):
            try:
                with psycopg2.connect(SUPABASE_URI) as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT id, 時間, timestamp_ms, current_section, scroll_y, action_type, 事件細節, x, y FROM user_behavior_logs_v4 ORDER BY id DESC LIMIT 50")
                        rows = cursor.fetchall()
                        cols = [desc[0] for desc in cursor.description]
                        df_logs = pd.DataFrame(rows, columns=cols)
                        
                if not df_logs.empty:
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)
                    st.caption(f"顯示最新 {len(df_logs)} 筆資料")
                else:
                    st.info("目前雲端尚無行為紀錄。")
            except Exception as e:
                st.error(f"讀取資料表失敗: {e}")

    st.button("🚪 登出系統", use_container_width=True)

# ==========================================
# 5. 路由系統 (注入頁面身分證)
# ==========================================
# 🎯 【頁面身分證】：讓 JS 知道現在在哪個畫面
st.markdown(f"<div id='current-page-flag' data-page='{st.session_state.current_page}' style='display:none;'></div>", unsafe_allow_html=True)

if st.session_state.current_page == "系統首頁":
    # ==========================================
    # 👑 [首頁終極 CSS] 實體內容對齊法 (拔除複雜佈局，回歸穩定)
    # ==========================================
    st.markdown("""
    <style>
        /* 1. 螢幕高度鎖死與呼吸空間 */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
        }
        .block-container {
            height: 94vh !important; 
            max-width: 95% !important; 
            padding: 1.5rem 0 1rem 0 !important; 
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
            gap: 15px !important;
        }
        div[data-testid="stVerticalBlock"]:first-of-type {
            display: flex; flex-direction: column; height: 100%; gap: 10px;
        }

        /* 2. 標題字體保護 */
        .welcome-title {
            font-size: clamp(26px, 3vw, 38px) !important;
            font-weight: 900 !important;
            color: #222 !important;
            margin: 0 !important;
        }

        /* 3. 區域劃分 (上方固定，下方填滿) */
        div[data-testid="stVerticalBlock"]:has(#top-marker) { flex: 0 0 auto; }
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) { 
            flex: 1 1 0; min-height: 0; 
        }
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) > div > [data-testid="stHorizontalBlock"] {
            height: 100%; gap: 20px !important;
        }

        /* 4. 左右側攔位基本設定 (內部微滾動) */
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"] {
            height: 100%; overflow-y: auto; overflow-x: hidden; padding: 15px 20px;
            background-color: #FDFCFB; border: 1px solid #EAE6E3;
            border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.02);
        }

        /* 隱藏捲軸 */
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"]::-webkit-scrollbar { width: 4px; }
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"]::-webkit-scrollbar-thumb {
            background-color: #E2DCD5; border-radius: 10px;
        }

        /* 5. 卡片樣式設計 (實體對齊的核心：控制 Margin) */
        /* 右側卡片：加上微距拉長總高度 */
        .info-card-full {
            background-color: #FFFFFF; border: 1px solid #EAE6E3;
            border-radius: 12px; padding: 12px 15px; margin-bottom: 14px; /* 設定空隙 */
            box-shadow: 0 1px 4px rgba(0,0,0,0.02);
            display: flex; justify-content: space-between; align-items: center;
        }

        /* 左側：消除 st.container 的內部干擾 */
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"]:nth-child(1) [data-testid="stVerticalBlock"] {
            gap: 0 !important;
        }

        /* 左側卡片文字區塊 */
        .info-card-top {
            background-color: #FFFFFF; border: 1px solid #EAE6E3;
            border-bottom: none; 
            border-radius: 12px 12px 0 0; padding: 12px 15px 8px 15px; 
            box-shadow: 0 1px 4px rgba(0,0,0,0.01);
            position: relative; z-index: 2;
        }
        
        .card-header { font-weight: 800; font-size: 1.1rem; color: #222; margin-bottom: 5px; }
        .card-meta { font-size: 0.85rem; color: #666; margin-bottom: 8px; }
        .tag-row { display: flex; flex-wrap: wrap; gap: 6px; }
        
        /* 左側卡片按鈕 (無縫貼合 + 底部留空隙) */
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"]:nth-child(1) .stButton {
            margin-top: -14px !important; /* 強制向上吸附文字區塊 */
            margin-bottom: 14px !important; /* 與右側卡片維持相同空隙 */
        }
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"]:nth-child(1) .stButton>button {
            background-color: #FAFAFA !important; border: 1px solid #EAE6E3 !important;
            border-top: 1px dashed #DCD5CE !important; 
            border-radius: 0 0 12px 12px !important; 
            height: 38px !important; color: #666 !important;
            font-weight: 700 !important; font-size: 0.9rem !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.01) !important;
            position: relative; top: -1px; z-index: 1;
        }
        div[data-testid="stVerticalBlock"]:has(#bottom-marker) [data-testid="column"]:nth-child(1) .stButton>button:hover {
            background-color: #F0EBE6 !important; color: #222 !important; border-color: #D2C8BE !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 變數計算
    current_enrolled_credits = sum(c['credits'] for c in st.session_state.my_courses if c.get('enrolled', False))
    total_after_this_sem = 85 + current_enrolled_credits
    needed_credits = max(128 - total_after_this_sem, 0)

    # ==========================================
    # 🟨 上方區塊 (歡迎詞 + 時間 + 學分)
    # ==========================================
    with st.container():
        st.markdown('<div id="top-marker"></div>', unsafe_allow_html=True)
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f'<div class="welcome-title">👋 歡迎回來，{st.session_state.name.split(" ")[0]}！</div>', unsafe_allow_html=True)
            st.markdown("<p style='font-size: 1rem; color: #666; margin: 4px 0 12px 0;'>掌握您的學習進度與最新動態，為新學期做好規劃。</p>", unsafe_allow_html=True)
        with c2:
            components.html("""
                <body style="margin: 0; padding: 0; background: transparent;"><div style="text-align: right; font-family: sans-serif; color: #555; font-size: 13px; font-weight: 700; background: #FFF; border: 1px solid #EAE6E3; padding: 6px 14px; border-radius: 20px; display: inline-block; float: right; box-shadow: 0 2px 5px rgba(0,0,0,0.02);">🕒 <span id="clock"></span></div>
                <script>function u(){const n=new Date();document.getElementById('clock').innerText=`${n.getFullYear()}/${n.getMonth()+1}/${n.getDate()} ${String(n.getHours()).padStart(2,'0')}:${String(n.getMinutes()).padStart(2,'0')}:${String(n.getSeconds()).padStart(2,'0')}`}setInterval(u,1000);u();</script></body>
            """, height=35)

        col1, col2, col3 = st.columns(3)
        # 💡 提示文字：完美對齊基準線
        tip_html = "<span style='color: #C85A5A; font-size: 0.85rem; font-weight: 600; margin-left: 10px;'>💡 建議本學期再修 2-3 門必修課</span>" if needed_credits > 40 else "<span style='color: #4A7C59; font-size: 0.85rem; font-weight: 600; margin-left: 10px;'>✨ 進度領先！可探索興趣領域</span>"

        for label, val, total, color, tip in [
            ("本學期預選", current_enrolled_credits, 25, "#4A7C59", ""),
            ("累積畢業學分", total_after_this_sem, 128, "#222", ""),
            ("距離畢業還需", needed_credits, 128, "#C85A5A", tip_html)
        ]:
            with [col1, col2, col3][["本學期預選", "累積畢業學分", "距離畢業還需"].index(label)]:
                with st.container(border=True):
                    st.markdown(f"<div style='font-size: 0.95rem; color: #666; font-weight: 600; margin-bottom: 2px;'>{label}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='display: flex; align-items: baseline; margin: 0 0 6px 0;'><span style='font-size: 1.8rem; font-weight: 900; color: {color}; line-height: 1;'>{val}</span><small style='font-size: 0.85rem; color: #999; margin-left: 5px;'>/ {total}</small>{tip}</div>", unsafe_allow_html=True)
                    st.progress(min(val/total, 1.0))

    # ==========================================
    # 🟥/🟦 下方雙欄區塊 (實體內容對齊法)
    # ==========================================
    with st.container():
        st.markdown('<div id="bottom-marker"></div>', unsafe_allow_html=True)
        cl, cr = st.columns(2)
        
        # --- 🔴 左下區塊：為您推薦的專屬課程 ---
        with cl:
            st.markdown("<h3 style='font-size: 1.3rem; color: #333; margin: 0 0 25px 0;'>🚀 為您推薦的專屬課程</h3>", unsafe_allow_html=True)
            recs = [
                {"name": "人因工程與實驗設計", "prof": "王教授", "time": "(四) 02-04", "match": "95%", "tags": ["專業必修", "實作"]},
                {"name": "系統動力學", "prof": "李教授", "time": "(二) 02-04", "match": "88%", "tags": ["專業選修", "邏輯"]},
                {"name": "資料庫設計", "prof": "張教授", "time": "(三) 06-08", "match": "82%", "tags": ["專業選修", "軟體"]},
            ]
            for i, c in enumerate(recs):
                with st.container():
                    st.markdown(f"""
                    <div class="info-card-top">
                        <div class="card-header">{c['name']}</div>
                        <div class="card-meta">👨‍🏫 {c['prof']} &nbsp;|&nbsp; 🕒 {c['time']}</div>
                        <div class="tag-row">
                            <span class="tag tag-match" style="margin:0; padding: 2px 8px;">{c['match']} 契合</span>
                            <span class="tag" style="margin:0; padding: 2px 8px;">{c['tags'][0]}</span>
                            <span class="tag" style="margin:0; padding: 2px 8px;">{c['tags'][1]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.button("查看詳情", key=f"btn_hm_{i}", use_container_width=True, on_click=navigate_to, args=("詳細課程", None, c['name']))
        
        # --- 🔵 右下區塊：全校熱門搶手課程 ---
        with cr:
            st.markdown("<h3 style='font-size: 1.3rem; color: #333; margin: 0 0 14px 0;'>🔥 全校熱門搶手課程</h3>", unsafe_allow_html=True)
            # 💡 新增第 6 門課，實體拉高總體積以對齊左側
            hots = [
                {"r": 1, "n": "Python 程式設計與資料分析", "d": "通識中心", "q": "剩 2 名", "c": "#C85A5A"},
                {"r": 2, "n": "人工智慧概論", "d": "資工系", "q": "剩 5 名", "c": "#C85A5A"},
                {"r": 3, "n": "投資理財實務", "d": "財金系", "q": "剩 12 名", "c": "#D4A373"},
                {"r": 4, "n": "心理學導論", "d": "通識中心", "q": "剩 20 名", "c": "#4A7C59"},
                {"r": 5, "n": "職場溝通與表達", "d": "通識中心", "q": "剩 25 名", "c": "#4A7C59"},
                {"r": 6, "n": "資料視覺化導論", "d": "資管系", "q": "剩 30 名", "c": "#D4A373"}
            ]
            for h in hots:
                st.markdown(f"""
                <div class="info-card-full">
                    <div style="display: flex; align-items: center;">
                        <div style="width: 32px; height: 32px; background: #F8F6F4; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: 900; margin-right: 12px; color: #555; font-size: 1rem;">{h['r']}</div>
                        <div>
                            <div style="font-weight: 800; color: #222; font-size: 1.05rem;">{h['n']}</div>
                            <div style="font-size: 0.85rem; color: #777;">{h['d']}</div>
                        </div>
                    </div>
                    <div style="background: {h['c']}15; color: {h['c']}; padding: 5px 12px; border-radius: 20px; font-weight: 800; font-size: 0.85rem;">⏳ {h['q']}</div>
                </div>
                """, unsafe_allow_html=True)
elif st.session_state.current_page == "視覺化介面":
    # ==========================================
    # 👑 [視覺化介面 CSS] 左側篩選(30%) + 右側圖表上下對切(70%)
    # ==========================================
    st.markdown("""
    <style>
        /* 1. 鎖定全螢幕高度，消除全域滾動 */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
        }
        .block-container {
            height: 94vh !important; 
            max-width: 96% !important; 
            padding: 1.5rem 0 1rem 0 !important; 
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
            gap: 10px !important;
        }
        
        /* 讓主垂直區塊變成 Flex 容器 */
        div[data-testid="stVerticalBlock"]:first-of-type {
            display: flex; flex-direction: column; height: 100%; gap: 10px;
        }

        /* 固定標題列高度 */
        div[data-testid="stVerticalBlock"]:first-of-type > div:nth-child(2) {
            flex: 0 0 auto;
        }

        /* 核心佈局：讓左右雙欄填滿剩餘高度 */
        div[data-testid="stVerticalBlock"]:first-of-type > div:nth-child(3) {
            flex: 1 1 auto; min-height: 0;
        }
        div[data-testid="stVerticalBlock"]:first-of-type > div:nth-child(3) > [data-testid="stHorizontalBlock"] {
            height: 100%; gap: 20px !important;
        }

        /* --- 🟨 左側篩選面板 (把底色拔掉，交給 Python 端的 st.container 去畫卡片) --- */
        [data-testid="column"]:nth-child(1) {
            height: 100%; overflow-y: auto; overflow-x: hidden;
            padding: 0px !important; 
        }
        /* 針對左側新增的 container 畫出圓角白框 */
        [data-testid="column"]:nth-child(1) > [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #FDFCFB; border: 1px solid #EAE6E3;
            border-radius: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.02);
            padding: 20px !important; height: 100%;
        }

        /* --- 右側區塊總管 --- */
        [data-testid="column"]:nth-child(2) {
            height: 100%; display: flex; flex-direction: column;
            gap: 15px !important; padding: 0 !important; overflow-y: auto; overflow-x: hidden;
        }
        [data-testid="column"]:nth-child(2) > [data-testid="stVerticalBlock"] {
            height: 100%; gap: 15px !important; display: flex; flex-direction: column;
        }

        /* --- 🟪 右上：散點圖區塊 (佔比 50%) --- */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(#zone-v-scatter) {
            flex: 1 1 50%; min-height: 320px; display: flex; flex-direction: column;
            padding: 15px !important; overflow: hidden;
            border-radius: 20px !important;
            background-color: #FFFFFF;
        }

        /* --- 🟥 右下：雷達圖與資訊區塊 (佔比 50%) --- */
        div[data-testid="stVerticalBlockBorderWrapper"]:has(#zone-v-radar) {
            flex: 1 1 50%; min-height: 320px; display: flex; flex-direction: column;
            padding: 15px 20px !important; overflow: hidden;
            border-radius: 20px !important;
            background-color: #FFFFFF;
        }

        /* 美化滾動軸 */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background-color: #E2DCD5; border-radius: 10px; }
        
        /* 壓縮左側元件間距，提升資訊密度 */
        [data-testid="column"]:nth-child(1) .stSelectbox { margin-bottom: -10px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 5px; margin-top: -10px;'>📊 視覺化分析中心</h2>", unsafe_allow_html=True)

    # 建立左右大分區：左(1) 右(2.5) 的比例最貼近你的草圖
    col_left_panel, col_right_panel = st.columns([1, 2.5])

    # ==========================================
    # 🟨 左側：條件篩選面板 (全高度)
    # ==========================================
    with col_left_panel:
        with st.container(border=True): # ✨ 新增這個容器來製造專屬框框
            st.markdown("<div id='zone-v-filter' style='position:absolute; top:-30px; left:0; width:1px; height:1px;'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:5px; font-size:1.1rem;'>🔍 全站課程搜尋</div>", unsafe_allow_html=True)
            search_term = st.text_input("搜尋關鍵字", key="search_term", placeholder="請輸入課程名稱或選課代號...", label_visibility="collapsed")
            
            st.markdown("<hr style='margin: 15px 0 10px 0;'>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:10px; font-size:1.1rem;'>📂 條件篩選面板</div>", unsafe_allow_html=True)

            # 🌟 邏輯原封不動，只是從原本的 st.columns 水平排列改為垂直排列
            if search_term:
                st.selectbox("1. 系所：", ["(搜尋模式)"], disabled=True)
                st.selectbox("2. 開課班級：", ["(搜尋模式)"], disabled=True)
                st.selectbox("3. 學期：", ["(搜尋模式)"], disabled=True)
                
                filtered_by_search = data[data["課程名稱"].str.contains(search_term, na=False, case=False) | data["選課代號"].astype(str).str.contains(search_term, na=False, case=False)]
                
                if not filtered_by_search.empty:
                    course_options = ["請選擇..."] + filtered_by_search["課程名稱"].tolist()
                    chart_state = st.session_state.get("scatter_chart")
                    
                    curr_sel = chart_state.get("selection", {}) if chart_state else {}
                    if curr_sel and len(curr_sel.get("points", [])) > 0:
                        clicked_course_id = curr_sel["points"][0]["customdata"][0]
                        clicked_course = curr_sel["points"][0]["customdata"][1]
                        
                        if st.session_state.get("last_chart_clicked_course") != clicked_course:
                            st.session_state.last_chart_clicked_course = clicked_course
                            js_code = f"""
                            <script>
                                const p = window.parent;
                                if (p.__ADD_LOG__) {{
                                    p.__ADD_LOG__('click_chart', '[散點圖] 點選課程: {clicked_course}', 0.0, 0.0);
                                }}
                            </script>
                            """
                            components.html(js_code, height=0, width=0)
                            st.toast(f"✅ 已捕捉圖表點擊：{clicked_course}")
                        
                        st.session_state.saved_course = clicked_course
                        st.session_state.target_course_id = clicked_course_id
                    elif curr_sel and len(curr_sel.get("points", [])) == 0:
                        st.session_state.last_chart_clicked_course = None
                    
                    if st.session_state.saved_course not in course_options:
                        st.session_state.saved_course = "請選擇..."
                        st.session_state.target_course_id = None
                        
                    crs_idx = course_options.index(st.session_state.saved_course)
                    selected_course = st.selectbox("4. 搜尋結果：", course_options, index=crs_idx)
                    
                    if selected_course != st.session_state.saved_course:
                        st.session_state.saved_course = selected_course
                        if selected_course != "請選擇...":
                            matched_id = filtered_by_search[filtered_by_search['課程名稱'] == selected_course]['選課代號'].tolist()
                            if matched_id: st.session_state.target_course_id = matched_id[0]
                    has_valid_filter = True
                    filtered = filtered_by_search
                else:
                    selected_course = st.selectbox("4. 搜尋結果：", ["查無結果..."], disabled=True)
                    st.session_state.saved_course = "請選擇..."
                    st.session_state.target_course_id = None
                    has_valid_filter = False
                    filtered = pd.DataFrame()
            else:
                dept_options = ["請選擇..."] + sorted(data[data["系所"] != "未知系所"]["系所"].unique().tolist())
                d_idx = dept_options.index(st.session_state.saved_dept) if st.session_state.saved_dept in dept_options else 0
                dept = st.selectbox("1. 系所：", dept_options, index=d_idx)
                st.session_state.saved_dept = dept

                if dept != "請選擇...":
                    filtered_by_dept = data[data["系所"] == dept]
                    raw_classes = filtered_by_dept["開課班級"].unique().tolist()
                    sorted_classes = sorted(raw_classes, key=lambda x: (1 if '一' in x else 2 if '二' in x else 3 if '三' in x else 9, 1 if '甲' in x else 2 if '乙' in x else 9, x))
                    class_options = ["請選擇..."] + sorted_classes
                    c_idx = class_options.index(st.session_state.saved_class) if st.session_state.saved_class in class_options else 0
                    class_sel = st.selectbox("2. 開課班級：", class_options, index=c_idx)
                    st.session_state.saved_class = class_sel
                else: 
                    class_sel = st.selectbox("2. 開課班級：", ["先選系所..."], disabled=True)
                    st.session_state.saved_class = "請選擇..."

                if class_sel not in ["請選擇...", "先選系所..."]:
                    filtered_by_class = filtered_by_dept[filtered_by_dept["開課班級"] == class_sel]
                    if '通識' in dept:
                        semester_sel = st.selectbox("3. 學期：", ["(無)"], disabled=True)
                        filtered_by_semester = filtered_by_class.drop_duplicates(subset=['課程名稱'])
                    else:
                        sorted_semesters = sorted(filtered_by_class["學期"].unique().tolist(), key=lambda sem: 1 if sem == '上學期' else 2)
                        sem_options = ["請選擇..."] + sorted_semesters
                        s_idx = sem_options.index(st.session_state.saved_semester) if st.session_state.saved_semester in sem_options else 0
                        semester_sel = st.selectbox("3. 學期：", sem_options, index=s_idx)
                        st.session_state.saved_semester = semester_sel
                        filtered_by_semester = filtered_by_class[filtered_by_class["學期"] == semester_sel] if semester_sel != "請選擇..." else pd.DataFrame()
                else:
                    semester_sel = st.selectbox("3. 學期：", ["先選班級..."], disabled=True)
                    st.session_state.saved_semester = "請選擇..."
                    filtered_by_semester = pd.DataFrame()

                if not filtered_by_semester.empty or (dept != "請選擇..." and '通識' in dept and class_sel != "請選擇..."):
                    course_options = ["請選擇..."] + filtered_by_semester["課程名稱"].tolist()
                    chart_state = st.session_state.get("scatter_chart")
                    
                    curr_sel = chart_state.get("selection", {}) if chart_state else {}
                    if curr_sel and len(curr_sel.get("points", [])) > 0:
                        clicked_course_id = curr_sel["points"][0]["customdata"][0]
                        clicked_course = curr_sel["points"][0]["customdata"][1]
                        
                        if st.session_state.get("last_chart_clicked_course") != clicked_course:
                            st.session_state.last_chart_clicked_course = clicked_course
                            js_code = f"""
                            <script>
                                const p = window.parent;
                                if (p.__ADD_LOG__) {{
                                    p.__ADD_LOG__('click_chart', '[散點圖] 點選課程: {clicked_course}', 0.0, 0.0);
                                }}
                            </script>
                            """
                            components.html(js_code, height=0, width=0)
                            st.toast(f"✅ 已捕捉圖表點擊：{clicked_course}")
                        
                        st.session_state.saved_course = clicked_course
                        st.session_state.target_course_id = clicked_course_id
                    elif curr_sel and len(curr_sel.get("points", [])) == 0:
                        st.session_state.last_chart_clicked_course = None
                    
                    if st.session_state.saved_course not in course_options:
                        st.session_state.saved_course = "請選擇..."
                        st.session_state.target_course_id = None

                    crs_idx = course_options.index(st.session_state.saved_course)
                    selected_course = st.selectbox("4. 課程：", course_options, index=crs_idx)
                    
                    if selected_course != st.session_state.saved_course:
                        st.session_state.saved_course = selected_course
                        if selected_course != "請選擇...":
                            matched_id = filtered_by_semester[filtered_by_semester['課程名稱'] == selected_course]['選課代號'].tolist()
                            if matched_id: st.session_state.target_course_id = matched_id[0]
                    
                    has_valid_filter = True
                    filtered = filtered_by_semester
                else:
                    selected_course = st.selectbox("4. 課程：", ["先選學期..."], disabled=True)
                    st.session_state.saved_course = "請選擇..."
                    st.session_state.target_course_id = None
                    has_valid_filter = False
                    filtered = pd.DataFrame()

            def reset_all():
                st.session_state.saved_dept = "請選擇..."
                st.session_state.saved_class = "請選擇..."
                st.session_state.saved_semester = "請選擇..."
                st.session_state.saved_course = "請選擇..."
                st.session_state.target_course_id = None
                st.session_state.search_term = ""
            
            st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True) 
            st.button("🔄 重置條件", on_click=reset_all, use_container_width=True)


    # ==========================================
    # 🟪/🟥 右側：圖表區 (上下對半)
    # ==========================================
    with col_right_panel:
        
        # --- 🟪 右上區塊：散點圖 ---
        with st.container(border=True):
            st.markdown("<div id='zone-v-scatter' style='position:absolute; top:-10px; left:0; width:1px; height:1px;'></div>", unsafe_allow_html=True)
            st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:-10px; font-size:1.05rem;'>📈 課程分佈散點圖</div>", unsafe_allow_html=True)
            
            if not has_valid_filter:
                # ✨ 修改 1：拔除 st.info，把提示文字直接寫進空白的 Plotly 圖表中
                fig_scatter = go.Figure().update_layout(
                    plot_bgcolor='rgba(0,0,0,0)', 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    height=280, 
                    margin=dict(l=20, r=20, t=20, b=20), 
                    xaxis=dict(showticklabels=False, showgrid=False, zeroline=False), 
                    yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
                    annotations=[dict(
                        text="👈 請從左側面板進行篩選，<br>或輸入關鍵字搜尋以載入圖表。",
                        x=0.5, y=0.5, xref="paper", yref="paper",
                        showarrow=False,
                        font=dict(size=14, color="#888888")
                    )]
                )
                st.plotly_chart(fig_scatter, use_container_width=True, key="empty_chart", config={'displayModeBar': False})
            else:
                fig_scatter = px.scatter(filtered, x="難度", y="滿意度", hover_name="課程名稱", hover_data={"難度": True, "滿意度": True, "選課代號": True}, custom_data=["選課代號", "課程名稱"])
                selected_idx = np.where(filtered["課程名稱"] == selected_course)[0].tolist() if selected_course not in ["請選擇...", "先選學期...", "查無結果..."] else None
                fig_scatter.update_traces(selectedpoints=selected_idx, marker=dict(color='#D9534F', size=13, opacity=0.8, line=dict(width=1, color='white')))
                # ✨ 高度微調：設定固定高度避免撐開 flex box
                fig_scatter.update_layout(xaxis_title="課程難易度", yaxis_title="滿意度", xaxis=dict(range=[0.5, 5.5], gridcolor='#EFEFEF', fixedrange=True), yaxis=dict(range=[0.5, 5.5], gridcolor='#EFEFEF', fixedrange=True), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=280, margin=dict(l=20, r=20, t=30, b=10), clickmode='event+select', dragmode=False)
                st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points", config={'displayModeBar': False}, key="scatter_chart")

        target_course_name = selected_course if selected_course not in ["請選擇...", "先選學期...", "查無結果..."] else None

        # --- 🟥 右下區塊：綜合資訊與雷達圖 ---
        with st.container(border=True):
            st.markdown("<div id='zone-v-radar' style='position:absolute; top:-10px; left:0; width:1px; height:1px;'></div>", unsafe_allow_html=True)
            col_info, col_radar = st.columns([1.1, 1])
            
            with col_info:
                if target_course_name:
                    course_info = data[data["課程名稱"] == target_course_name].iloc[0]
                    sat_text = "高滿意" if course_info['滿意度'] >= 4 else ("中滿意" if course_info['滿意度'] >= 3 else "低滿意")
                    diff_text = "高難度" if course_info['難度'] >= 4 else ("中難度" if course_info['難度'] >= 2.5 else "低難度")
                    
                    # ✨ [還原理想排版 1]：標題與「查看詳細資訊 ➔」按鈕並排於最上方
                    col_title, col_btn_detail = st.columns([5, 3])
                    with col_title:
                        st.markdown(f"<div style='background-color: #DCD7D4; padding: 5px 15px; border-radius: 15px; font-weight: bold; font-size: 16px; color: #333; display: inline-block; margin-bottom: 10px; margin-top: 5px;'>{target_course_name}</div>", unsafe_allow_html=True)
                    with col_btn_detail:
                        st.button("查看詳細資訊 ➔", key="btn_to_detail", use_container_width=True, on_click=navigate_to, args=("詳細課程", course_info['選課代號'], target_course_name))
                    
                    sem_val = course_info.get('學期', '未知')
                    # ✨ [還原理想排版 2]：整合文字資訊，加上 🗓️ 日期圖示與授課教師
                    st.markdown(f"""
                        <div style="background-color: #EFECE9; border-radius: 12px; padding: 10px 15px; margin-bottom: 10px;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #555;">📌 選課代號：{course_info['選課代號']} &nbsp;|&nbsp; 🎓 學分數：{course_info.get('學分', course_info.get('學分數', 2))} &nbsp;|&nbsp; 🗓️ {sem_val}</p>
                            <p style="margin: 0; font-size: 14px; color: #333; font-weight: 700;">授課教師：依校方系統公告</p>
                        </div>
                        <div style="background-color: #EFECE9; border-radius: 12px; padding: 10px 15px; margin-bottom: 15px;">
                            <p style="margin: 3px 0; font-size: 15px; color: #555;">🔥 綜合滿意度： <strong>{course_info['滿意度']}/5</strong></p>
                            <p style="margin: 3px 0; font-size: 15px; color: #555;">💦 課程難易度： <strong>{course_info['難度']}/5</strong></p>
                            <p style="margin: 3px 0 0 0; font-size: 13px; color: #777;">(位於：{sat_text}/{diff_text}區)</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # ✨ [還原理想排版 3]：底部並排「加入收藏」與「模擬排課」按鈕，完美吃套全域圓角 CSS
                    c_btn_a, c_btn_b = st.columns(2)
                    with c_btn_a:
                        if st.button("❤️ 加入收藏", key="vis_add_fav", use_container_width=True):
                            c_code = str(course_info['選課代號'])
                            if any(c['id'] == c_code for c in st.session_state.my_courses): 
                                st.toast(f"「{target_course_name}」已在清單中！", icon="⚠️")
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
                                st.session_state.my_courses.append({"id": c_code, "name": target_course_name, "time": time_slots, "credits": credits, "type": c_type, "enrolled": False})
                                st.toast(f"已加入收藏！", icon="✨")
                    with c_btn_b:
                        st.button("➕ 模擬排課", key="vis_to_sim", use_container_width=True, on_click=navigate_to, args=("我的收藏",))
                else:
                    # ✨ 空狀態的佔位符也一併調整對齊
                    st.markdown("""
                        <div style="background-color: #E8E2DE; padding: 5px 15px; border-radius: 15px; font-weight: bold; font-size: 16px; color: #999; display: inline-block; margin-bottom: 10px; margin-top: 5px;">等待選擇課程...</div>
                        <div style="background-color: #F5F5F5; border-radius: 12px; padding: 10px 15px; margin-bottom: 10px;">
                            <p style="margin: 0 0 8px 0; font-size: 14px; color: #aaa;">📌 選課代號：--- &nbsp;|&nbsp; 🎓 學分數：--- &nbsp;|&nbsp; 🗓️ ---</p>
                            <p style="margin: 0; font-size: 14px; color: #aaa; font-weight: 700;">授課教師：---</p>
                        </div>
                        <div style="background-color: #F5F5F5; border-radius: 12px; padding: 10px 15px;"><p style="margin: 3px 0; font-size: 15px; color: #aaa;">🔥 綜合滿意度： - / 5</p><p style="margin: 3px 0; font-size: 15px; color: #aaa;">💦 課程難易度： - / 5</p><p style="margin: 3px 0 0 0; font-size: 13px; color: #aaa;">(位於：---)</p></div>
                    """, unsafe_allow_html=True)

            with col_radar:
                st.markdown("<div style='font-weight:bold; color:#555; text-align:center; font-size:1rem; margin-bottom: -15px;'>🌟 多維度屬性分析</div>", unsafe_allow_html=True)
                values_closed = radar_data.get(course_info['選課代號'] if target_course_name else None, [0, 0, 0, 0, 0]) + radar_data.get(course_info['選課代號'] if target_course_name else None, [0, 0, 0, 0, 0])[:1] if target_course_name else [0, 0, 0, 0, 0, 0]
                fill_color = 'rgba(135, 206, 250, 0.6)' if target_course_name else 'rgba(200, 200, 200, 0.2)'
                line_color = '#5BC0DE' if target_course_name else '#cccccc'
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=values_closed, theta=categories + [categories[0]], fill='toself', fillcolor=fill_color, line=dict(color=line_color), marker=dict(size=1)))
                
                # ✨ 修改 2：加大底部的 margin (b=30)，讓「互動程度」不會被切掉
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor='rgba(0,0,0,0)', 
                        radialaxis=dict(range=[0, 5], showticklabels=False), 
                        angularaxis=dict(tickfont=dict(size=11, color='#555' if target_course_name else '#aaa'))
                    ), 
                    showlegend=False, 
                    height=250, 
                    paper_bgcolor='rgba(0,0,0,0)', 
                    plot_bgcolor='rgba(0,0,0,0)', 
                    margin=dict(l=30, r=30, t=30, b=30) 
                )
                st.plotly_chart(fig_radar, use_container_width=True, theme=None, config={'staticPlot': True})

elif st.session_state.current_page == "詳細課程":
    # ==========================================
    # 👑 [詳細課程頁面專屬 CSS] 
    # ==========================================
    st.markdown("""
    <style>
        /* 1. 鎖定全螢幕高度 */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
        }
        .block-container {
            height: 94vh !important; 
            max-width: 96% !important; 
            padding: 1.5rem 0 0.5rem 0 !important; 
            display: flex !important;
            flex-direction: column !important;
            overflow: hidden !important;
        }

        /* 2. 佈局容器：頂部(固定)-中間(延展)-底部(固定) */
        .main-content-area {
            flex: 1 1 auto;
            display: flex;
            gap: 20px;
            min-height: 0; /* 關鍵：允許子元素縮小以符合 Flex */
            margin-bottom: 10px;
        }

        /* 紅色區塊：詳細資訊 (左側) */
        .left-info-col {
            flex: 1; /* 一半寬度 */
            display: flex;
            flex-direction: column;
            background-color: #FFFFFF;
            border: 1px solid #EAE6E3;
            border-radius: 20px;
            padding: 20px;
            overflow: hidden; /* 由內層控制滾動 */
        }
        .scrollable-info {
            flex: 1;
            overflow-y: auto;
            padding-right: 10px;
        }

        /* 右側欄：黃色(圖表) + 紫色(留言) */
        .right-dash-col {
            flex: 1; /* 一半寬度 */
            display: flex;
            flex-direction: column;
            gap: 15px;
            overflow: hidden;
        }

        /* 黃色區塊：折線圖 (右上) */
        .top-chart-box {
            flex: 0 0 45%; /* 固定比例 */
            background-color: #FFFFFF;
            border: 1px solid #EAE6E3;
            border-radius: 20px;
            padding: 15px;
            overflow: hidden;
        }

        /* 紫色區塊：留言板 (右下) */
        .bottom-comment-box {
            flex: 1; /* 填滿剩餘高度 */
            background-color: #FFFFFF;
            border: 1px solid #EAE6E3;
            border-radius: 20px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .scrollable-comments {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 10px;
            padding-right: 5px;
        }

        /* 底部按鈕列 */
        .fixed-footer {
            flex: 0 0 auto;
            background: transparent;
            padding: 10px 0;
            border-top: 1px solid #DCD5CE;
        }

        /* 美化滾動軸 */
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background-color: #E2DCD5; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

    # --- 頂部標題與返回 ---
    col_header_left, col_header_right = st.columns([5, 1])
    with col_header_left:
        st.markdown("<h2 style='color: #333; font-weight: 800; margin: 0;'>📖 課程詳細資訊</h2>", unsafe_allow_html=True)
    with col_header_right:
        st.button("🔙 返回前頁", use_container_width=True, on_click=navigate_to, args=("視覺化介面",))

    target_id = st.session_state.get('target_course_id')
    target_name = st.session_state.get('saved_course', "請選擇...")
    matches = pd.DataFrame()
    if target_id and not data.empty:
        matches = data[data['選課代號'].astype(str) == str(target_id)]
    if matches.empty and target_name not in ["請選擇...", "先選學期...", "查無結果..."] and not data.empty:
        matches = data[data['課程名稱'].astype(str).str.contains(target_name, na=False, regex=False)]

    if matches.empty:
        st.warning("⚠️ 請先選擇一門課程後，再查看詳細資訊。")
    else:
        course_data = matches.iloc[0]
        current_code = str(course_data['選課代號'])
        year_str = str(course_data.get('yms_year', '未知'))
        sem_str = str(course_data.get('學期', '未知'))
        name_str = str(course_data.get('課程名稱', target_name))
        selected_uid = f"[{year_str}-{sem_str}] [{current_code}] {name_str}"
        if current_code not in st.session_state.comments_db: st.session_state.comments_db[current_code] = []
        current_comments = st.session_state.comments_db[current_code]

        # --- 中間主戰場 (紅/黃/紫) ---
        main_col_left, main_col_right = st.columns(2)

        # 🔴 紅色區塊 (左側)
        with main_col_left:
            with st.container(border=True):
                st.markdown("<div id='zone-d-info'></div>", unsafe_allow_html=True)
                st.markdown(f"#### 📌 課程完整資訊")
                st.markdown(f"<div style='background-color: #E2DCD5; padding: 4px 12px; border-radius: 8px; display: inline-block; margin-bottom: 15px; font-weight: bold; color: #222; font-size: 14px;'>{selected_uid}</div>", unsafe_allow_html=True)
                
                # 開啟內部滾動
                with st.container(height=520, border=False):
                    target_cols = ['選課代號', '開課班級', '科目簡稱', '學分數', '學分', '必選修', '上課時間', 'EMI註記', '授課方式', '授課語言', '系所', '課程描述_中', '課程描述_英']
                    for col_name in target_cols:
                        if col_name not in course_data.index: continue
                        val = course_data[col_name]
                        if col_name == '必選修':
                            val = '必修' if str(val).upper() == 'M' else '選修'
                        
                        if isinstance(val, str) and len(val) > 25:
                            st.markdown(f"<div style='margin-bottom: 12px; background-color: #F8F6F1; padding: 12px; border-radius: 10px; border: 1px solid #E2DCD5;'><span style='font-weight: 800; color: #444;'>📑 {col_name}：</span><br><span style='color: #222; font-size: 0.95rem; line-height: 1.5;'>{val}</span></div>", unsafe_allow_html=True)
                        else:
                            st.markdown(f"<div style='margin-bottom: 8px;'><span style='font-weight: 600; color: #555;'>{col_name}：</span> <span style='color: #111; font-weight: 800;'>{val}</span></div>", unsafe_allow_html=True)

        # 右側欄 (黃/紫)
        with main_col_right:
            # 🟡 黃色區塊 (右上 - 圖表)
            with st.container(border=True):
                st.markdown("#### 📈 歷年修課趨勢")
                trend_df = get_fixed_trend_data(current_code)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.AvgScore, name='平均成績', line=dict(color='#C85A5A', width=3), yaxis='y1')) 
                fig.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.Students, name='修課人數', line=dict(color='#4A7C59', width=3), yaxis='y2')) 
                fig.update_layout(
                    margin=dict(l=40, r=40, t=10, b=10), height=200, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    legend=dict(orientation="h", y=1.2, font=dict(size=10)),
                    xaxis=dict(tickfont=dict(size=10), gridcolor='#EEE'),
                    yaxis=dict(range=[0, 100], tickfont=dict(size=10)),
                    yaxis2=dict(overlaying='y', side='right', range=[0, 150], tickfont=dict(size=10)),
                    dragmode=False
                )
                # ✨ 這裡就是徹底靜態化的魔法：加入 config={'staticPlot': True}
                st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

            # 🟣 紫色區塊 (右下 - 留言板)
            with st.container(border=True):
                st.markdown("#### 💬 討論區")
                # 留言內容滾動區
                with st.container(height=200, border=False):
                    if not current_comments: 
                        st.caption("目前尚無留言...")
                    else:
                        for comment in current_comments:
                            st.markdown(f'''<div style="background-color: #F8F6F1; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #A3968C;"><span style="font-weight: 800; font-size: 13px;">{comment['user']}</span><br><span style="font-size: 13px; color: #444;">{comment['content']}</span></div>''', unsafe_allow_html=True)
                
                # 輸入區
                with st.form(key='comment_form', clear_on_submit=True):
                    c_input, c_btn = st.columns([4, 1])
                    new_comment = c_input.text_input("輸入心得...", label_visibility="collapsed")
                    if c_btn.form_submit_button("🚀") and new_comment:
                        st.session_state.comments_db[current_code].append({"user": st.session_state.get("name", "王小明"), "content": new_comment})
                        st.rerun()

        # --- 底部固定功能紐 (藍色區塊) ---
        st.write("") # 增加一點呼吸感
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            if st.button("❤️ 加入收藏", key="btn_fav_detail", use_container_width=True):
                if any(c['id'] == current_code for c in st.session_state.my_courses): st.toast("已在收藏中！")
                else:
                    c_type = '必修' if str(course_data.get('必選修')).upper() == 'M' else '選修'
                    st.session_state.my_courses.append({"id": current_code, "name": name_str, "time": [], "credits": 2, "type": c_type, "enrolled": False})
                    st.toast("已加入收藏！")
        with col_f2:
            st.button("➕ 模擬排課", key="btn_sim_detail", use_container_width=True, on_click=navigate_to, args=("我的收藏",))
        with col_f3:
            st.link_button("🔗 學校選課系統", url="https://course.fcu.edu.tw/", use_container_width=True)

elif st.session_state.current_page == "我的收藏":
    # ==========================================
    # 👑 [我的收藏 - 原生安全鎖定版 CSS] 
    # ==========================================
    st.markdown("""
    <style>
        /* 1. 鎖定全螢幕，禁止全域滾動 */
        html, body, [data-testid="stAppViewContainer"] {
            overflow: hidden !important;
        }
        .block-container {
            height: 94vh !important; 
            max-width: 96% !important; 
            padding: 1.5rem 0 0.5rem 0 !important; 
            display: flex !important;
            flex-direction: column !important;
        }

        /* 2. 課表專屬 CSS：強制拉高以填滿剩餘空間 */
        .timetable-full {
            width: 100%;
            height: 490px; /* 🚀 魔法在這裡：強制表格高度，完美平分底部空白 */
            border-collapse: collapse;
            table-layout: fixed;
            background-color: white;
        }
        .timetable-full th, .timetable-full td {
            border: 1px solid #EAE6E3;
            text-align: center;
            vertical-align: middle;
            font-size: 11px;
        }
        .timetable-full th {
            background-color: #F8F6F4;
            font-weight: 800;
        }
        .timetable-full td.filled {
            background-color: #DCD7D4;
            color: #222;
            font-weight: 900;
            border-radius: 4px;
        }
        .timetable-full td.conflict {
            background-color: #FADBD8;
            color: #C0392B;
            font-weight: bold;
        }

        /* 3. 課程卡片樣式優化 */
        .fav-card {
            background-color: #F8F6F4;
            border: 1px solid #EAE6E3;
            border-radius: 10px;
            padding: 8px 12px;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            min-height: 50px;
        }
        .fav-enrolled {
            border-left: 6px solid #4A7C59 !important;
            background-color: #F0F4F0 !important;
        }

        /* 隱藏原生容器多餘的間距 */
        [data-testid="stVerticalBlock"] > div { padding: 0 !important; }
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
    # 🔴 左側：候選清單 (原生固定高度容器)
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
                    
                    # 課程條目排版
                    ci, ca, cd = st.columns([3.5, 1.2, 0.6])
                    ci.markdown(f"""
                        <div class="fav-card {card_style}">
                            <div style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                                <span style="font-size: 13px; font-weight: 800; color: #333;">{status_ico} {course['name']}</span><br>
                                <span style="font-size: 11px; color: #888;">代碼: {course['id']}</span>
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
    # 🟡 右側：預覽課表 (原生固定高度容器)
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
                st.error(f"⚠️ 發現 {len(conflicts)} 處衝堂")
            else:
                st.success("✅ 目前課表狀態良好")

            st.markdown("<h4 style='text-align: center; margin: 10px 0;'>📅 預覽課表</h4>", unsafe_allow_html=True)

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
elif st.session_state.current_page == "個人設定":
    st.markdown("<h2 style='margin-bottom: 20px; color: #333; font-weight: 800;'>👤 個人設定</h2>", unsafe_allow_html=True)

    def reset_all_prefs():
        for k in st.session_state.prefs["prof"]: st.session_state.prefs["prof"][k] = False
        for k in st.session_state.prefs["cross"]: st.session_state.prefs["cross"][k] = False
        for k in st.session_state.prefs["course"]: st.session_state.prefs["course"][k] = False
        st.session_state.prefs["workload"] = "適中 😊"
        st.session_state.show_uploader = False

    with st.container(border=True):
        col_header_left, col_header_right = st.columns([5, 1])
        with col_header_left: st.markdown("### 基本資料")
        with col_header_right:
            if st.button("✏️ 編輯", use_container_width=True): st.session_state.editing = True
                
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(st.session_state.avatar, width=120)
            if st.button("📸 更換頭像", use_container_width=True):
                st.session_state.show_uploader = not st.session_state.show_uploader
                st.rerun()
                
            if st.session_state.show_uploader:
                uploaded_file = st.file_uploader("上傳新頭像", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
                if uploaded_file is not None:
                    st.session_state.avatar = uploaded_file.getvalue()
                    st.session_state.show_uploader = False
                    st.rerun()

        with col2:
            if st.session_state.editing:
                with st.form("edit_profile"):
                    name_input = st.text_input("姓名", value=st.session_state.name)
                    dept_input = st.text_input("系級", value=st.session_state.department)
                    year_input = st.text_input("年級", value=st.session_state.year)
                    col_form1, col_form2 = st.columns(2)
                    with col_form1: submitted = st.form_submit_button("💾 儲存")
                    with col_form2: cancel = st.form_submit_button("❌ 取消")
                    if submitted:
                        st.session_state.name, st.session_state.department, st.session_state.year, st.session_state.editing = name_input, dept_input, year_input, False
                        st.rerun()
                    if cancel:
                        st.session_state.editing = False
                        st.rerun()
            else:
                st.markdown(f"#### {st.session_state.name}")
                st.write(f"**🎓 系級：** {st.session_state.department}")
                st.write(f"**📚 年級：** {st.session_state.year}")
            
            st.markdown("<hr style='margin: 15px 0; border-color: #EAE6E3;'>", unsafe_allow_html=True)
            
            current_enrolled_req = sum(c['credits'] for c in st.session_state.my_courses if c.get('enrolled', False) and c['type'] == '必修')
            current_enrolled_opt = sum(c['credits'] for c in st.session_state.my_courses if c.get('enrolled', False) and c['type'] != '必修')
            req_credits = 55 + current_enrolled_req
            opt_credits = 30 + current_enrolled_opt
            total_creds = req_credits + opt_credits
            
            st.write(f"**🎓 畢業門檻進度 (目前累積 {total_creds} / 128 學分)：**")
            col_grad1, col_grad2 = st.columns(2)
            with col_grad1: 
                st.write(f"**必修 ({req_credits} / 72)**")
                st.progress(min(req_credits / 72, 1.0))
            with col_grad2: 
                st.write(f"**選修 ({opt_credits} / 56)**")
                st.progress(min(opt_credits / 56, 1.0))

    with st.container(border=True):
        st.markdown("### ⭐ 興趣與跨域探索")
        st.caption("下列選項將影響系統為您推薦的智能排課結果")
        col_interest_left, col_interest_right = st.columns(2)
        with col_interest_left:
            st.markdown("##### 專業領域 (系內課群)")
            for field in st.session_state.prefs["prof"].keys(): 
                st.session_state.prefs["prof"][field] = st.checkbox(field, value=st.session_state.prefs["prof"][field])
                
        with col_interest_right:
            st.markdown("##### 跨域/通識偏好 (向度分類)")
            for field in st.session_state.prefs["cross"].keys(): 
                st.session_state.prefs["cross"][field] = st.checkbox(field, value=st.session_state.prefs["cross"][field])

    with st.container(border=True):
        st.markdown("### ⚙️ 課程偏好設定")
        col_pref1, col_pref2 = st.columns(2)
        with col_pref1:
            st.write("**偏好的作業負擔程度：**")
            workload_options = ["輕鬆 😌", "適中 😊", "充實 💪", "極具挑戰 🔥"]
            idx = workload_options.index(st.session_state.prefs["workload"])
            st.session_state.prefs["workload"] = st.radio("選擇作業負擔程度", workload_options, index=idx, label_visibility="collapsed", horizontal=True)
            st.caption(f"目前狀態：{st.session_state.prefs['workload']}")
            
        with col_pref2:
            st.write("**課程類型偏好：**")
            course_types = ["理論課", "實驗課", "線上課程", "混合制"]
            cols_type = st.columns(4)
            for i, course in enumerate(course_types):
                with cols_type[i]: 
                    st.session_state.prefs["course"][course] = st.checkbox(course, value=st.session_state.prefs["course"][course])

    st.write("") 
    col_save1, col_save2, col_save3 = st.columns([1, 1, 2])
    with col_save1:
        if st.button("💾 儲存所有設定", use_container_width=True): st.success("✅ 設定已存檔！")
    with col_save2:
        if st.button("🔄 重置偏好", on_click=reset_all_prefs, use_container_width=True): st.warning("⚠️ 已重置預設興趣與課程偏好")