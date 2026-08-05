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
SUPABASE_URI = "postgresql://postgres.vtcpjriwbkvkimzlrfoo:1234567890@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require"

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
# 🚀 將側邊欄預設為 collapsed (縮起)
st.set_page_config(page_title="🎓 選課決策系統", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<meta name="google" content="notranslate">
<style>
    /* --- 全局共用 CSS --- */
    .stApp { background-color: #EAE6E3; }
    header { background-color: transparent !important; }
    
    /* 🚀 暴力隱藏原生側邊欄與展開按鈕，徹底釋放空間！ */
    [data-testid="collapsedControl"] { display: none !important; }
    [data-testid="stSidebar"] { display: none !important; }
    
    /* 統一容器外框：去掉邊距造成的凹凸感 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF; border-radius: 15px; border: none;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05); padding: 15px !important; margin-bottom: 0px;
    }
    
    h1, h2, h3, h4 { color: #333333 !important; font-weight: 800 !important; font-family: 'sans-serif'; }
    p, span, label { color: #555555 !important; font-family: 'sans-serif'; }
    
    /* 滾動條美化 */
    ::-webkit-scrollbar { width: 5px; }
    ::-webkit-scrollbar-thumb { background-color: #E2DCD5; border-radius: 10px; }
    
    /* 下拉選單美化 */
    .stSelectbox > div > div { background-color: #FDFCFB !important; border-radius: 10px !important; }
    
    /* 全局按鈕基礎美化 */
    .stButton>button { 
        border-radius: 10px; font-weight: 800; height: 40px !important; 
        background-color: #EFEBE8 !important; border: 1px solid #DCD5CE !important;  
        color: #333333 !important; transition: all 0.3s ease; 
    }
    .stButton>button:hover { 
        background-color: #E4DCD3 !important; border-color: #D2C8BE !important;
        transform: translateY(-2px);
    }

    /* 🚀 將 Radio 選單徹底改造為大型質感按鈕 */
    div[role="radiogroup"] {
        gap: 12px !important; 
        margin-top: 10px !important;
        width: 100% !important; /* 確保父容器滿寬 */
    }
    div[role="radiogroup"] > label {
        width: 100% !important; /* 🚀 強制所有按鈕寬度一致（填滿父容器） */
        padding: 16px 20px !important; 
        background-color: #F8F6F1 !important;
        border-radius: 12px !important;
        border: 2px solid #EAE6E3 !important;
        margin: 0 !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
    }
    div[role="radiogroup"] > label:hover {
        border-color: #A3968C !important;
        background-color: #E2DCD5 !important;
        transform: translateY(-2px) !important;
    }
    /* 隱藏 Radio 預設的小圓圈 */
    div[role="radiogroup"] > label > div:first-child { display: none !important; }
    
    /* 放大文字並置中 */
    div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        font-size: 1.15rem !important;
        font-weight: 900 !important;
        color: #555 !important;
        margin: 0 !important;
        text-align: center !important;
    }
    
    /* 🎯 被選中時的樣式 (🚀 改為柔和有質感的莫蘭迪灰褐色) */
    div[role="radiogroup"] > label:has(input:checked),
    div[role="radiogroup"] > label:has(input[aria-checked="true"]) {
        background-color: #A3968C !important;
        border-color: #8C7D70 !important;
        box-shadow: 0 4px 10px rgba(163, 150, 140, 0.3) !important;
    }
    div[role="radiogroup"] > label:has(input:checked) div[data-testid="stMarkdownContainer"] p,
    div[role="radiogroup"] > label:has(input[aria-checked="true"]) div[data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心資料與演算法 (略，保留你原本寫的即可)
# ==========================================
import os

url_params = st.query_params
course_type = url_params.get("course", "new_ed")
session_key = f"sampled_courses_{course_type}"

if session_key not in st.session_state:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, '0721-course.db')

        with sqlite3.connect(db_path, timeout=10) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            if not tables:
                raise ValueError(f"連線成功，但 {db_path} 裡面找不到任何資料表！")
            
            actual_table_name = tables[0][0]
            
            if course_type == "new_ed":
                query = f'SELECT * FROM "{actual_table_name}" WHERE 課程類別 LIKE \'%一般通識%\' ORDER BY RANDOM() LIMIT 8'
            elif course_type == "new_pro":
                query = f'SELECT * FROM "{actual_table_name}" WHERE 課程類別 LIKE \'%資訊類通識%\' ORDER BY RANDOM() LIMIT 8'
            else:
                query = f'SELECT * FROM "{actual_table_name}" ORDER BY RANDOM() LIMIT 8'
                
            df = pd.read_sql_query(query, conn)

    except Exception as e:
        st.error(f"⚠️ 資料庫讀取失敗！錯誤訊息: {e}")
        df = pd.DataFrame()

    if df.empty:
        df = pd.DataFrame(columns=['選課代號', '配當系所.1', '開課班級簡稱', '科目簡稱', 'yms_smester', '系所', '開課班級', '課程名稱', '學期', '教學參與性', '難度', '十八週進度', '評分標準'])
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
        quadrant_points = [
            (3.7, 3.8), (4.2, 4.1), 
            (2.3, 3.9), (1.9, 4.2), 
            (2.1, 2.2), (2.6, 2.4), 
            (3.9, 2.1), (4.3, 2.5)  
        ]
        actual_len = len(df)
        if actual_len <= 8:
            selected_points = quadrant_points[:actual_len]
        else:
            selected_points = [random.choice(quadrant_points) for _ in range(actual_len)]
        np.random.shuffle(selected_points)
        df['難度'] = [p[0] for p in selected_points]
        df['滿意度'] = [p[1] for p in selected_points]
        df['教學參與性'] = [p[1] for p in selected_points]
        
    st.session_state[session_key] = df

data = st.session_state[session_key]

@st.cache_data
def get_fixed_trend_data(course_code, difficulty):
    random.seed(course_code)
    if difficulty >= 4.0: base_min, base_max = 55, 72 
    elif difficulty <= 3.0: base_min, base_max = 80, 96 
    else: base_min, base_max = 68, 85 
    return pd.DataFrame({"Year": ['109', '110', '111', '112', '113'], "Students": [random.randint(40, 120) for _ in range(5)], "AvgScore": [random.randint(base_min, base_max) for _ in range(5)]})

@st.cache_data
def get_fixed_grade_dist_data(course_code, difficulty):
    random.seed(course_code)
    bins = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"]
    if difficulty >= 4.0: weights = [1, 2, 5, 8, 15, 25, 25, 12, 5, 2] 
    elif difficulty <= 3.0: weights = [0, 0, 0, 1, 2, 3, 10, 25, 40, 19]
    else: weights = [0, 0, 1, 2, 4, 8, 20, 35, 20, 10]
    student_count = random.randint(45, 120)
    dist = [w * random.uniform(0.8, 1.2) for w in weights]
    total = sum(dist)
    if total > 0: dist = [int(round((val/total) * student_count)) for val in dist]
    return pd.DataFrame({"Range": bins, "Count": dist})

def generate_fake_comments(course_code, difficulty, engagement):
    random.seed(course_code)  
    names = ["工工三甲小神童", "期末被當專業戶", "逢甲路過小精靈", "學分小偷", "準時下課推廣大使", "坐在第一排的學霸", "熬夜寫code的肝苦人", "不想延畢的大四老屁股", "只求及格的男子", "圖書館地縛靈", "夜衝第一名", "通識獵人", "靠早八續命", "報告雷隊友剋星", "GPA守護者"]
    diff_pool = []
    if difficulty >= 4.0: diff_pool = ["這門課真的硬，期中考都是申論題，沒有看熟上課簡報會死得很慘。", "給分很不甜...我全勤加上作業都有用心寫，最後只拿剛好及格。", "超級硬課！每次上課都在瘋狂抄筆記，腦容量要夠大。", "建議沒有心理準備不要輕易嘗試，期末專案要求非常嚴格。", "Loading 超重，每個禮拜都有作業，常常寫到半夜。", "老師標準定很高，分數完全不放水，想拿高分要拚老命。", "考試範圍超級廣，考前抱佛腳絕對沒救。", "雖然很硬，但上完會覺得抗壓性變高了...", "被當率不低，選之前真的要評估一下這學期的學分重不重。", "涼度是零，每一堂課都在高速運轉，不能恍神。"]
    elif difficulty <= 3.0: diff_pool = ["給分超甜！老師根本是活菩薩，基本上有交作業都會過。", "超級涼課～很適合拿來湊學分，期中也是開書考。", "只要出席率正常，考前看個一兩天就能輕鬆拿高分了。", "難度不高，老師考前會大洩題，背熟就對了。", "佛心老師推推，報告有認真上台講分數都很漂亮。", "根本是快樂學分班，沒有太大的壓力。", "上課聽得懂，考題都很基本，不會出刁鑽的陷阱題。", "缺學分的選這堂就對了，躺著過。", "loading 很輕，一學期才兩次小作業，負擔超小。", "老師給分很大方，期末成績出來比預期的還高很多。"]
    else: diff_pool = ["難度適中，有花時間讀書的話分數不會太難看。", "中規中矩的課，考試都從投影片出，給分合理。", "不是涼課但也沒到硬，作業負擔一般般。", "分數給得算公允，一分耕耘一分收穫。", "只要上課有聽，考前稍微複習一下就能穩穩拿學分。", "不會刻意刁難學生，跟著進度走就沒問題。", "難易度剛剛好，不會讓人覺得太廢，也不會壓力太大。", "算是偏扎實的課，但只要肯花時間一定會過。", "普普通通，沒有特別甜也沒有特別硬。"]
    eng_pool = []
    if engagement >= 4.0: eng_pool = ["上課節奏很快，互動超多，常常要小組討論，完全不會想睡覺！", "老師很愛點人回答問題，強迫你一定要專心上課。", "每堂課都有隨堂小活動或 Kahoot，參與感拉滿。", "這門課極度吃重團隊合作，遇到好隊友帶你上天堂。", "課堂氣氛很熱絡，老師很會帶動討論。", "發言都有加分，大家搶答超踴躍，絕對睡不著。", "幾乎每週都要上台短短分享一下，訓練膽量的好地方。", "老師超幽默，會一直丟問題下來，整堂課絕無冷場。", "滿滿的實作跟討論，很喜歡這種不會死氣沉沉的上課方式。"]
    elif engagement <= 3.0: eng_pool = ["大班演講課感很重，老師基本上一直唸投影片。", "可以在下面做自己的事，老師不太管下面在幹嘛。", "上課有點催眠，不需要太多互動，適合喜歡安靜聽課的人。", "就是一直聽課做筆記，沒什麼分組或發言的機會。", "老師自己講自己的，底下睡成一片也不會管。", "滿傳統的授課方式，適合習慣填鴨式教學的人。", "節奏偏慢，很容易恍神滑手機。", "幾乎零互動，期中跟期末有去考就好。", "點完名就可以做自己的事了，非常自由。"]
    else: eng_pool = ["老師偶爾會丟問題給大家想，互動頻率剛剛好。", "上課氛圍還算輕鬆，不會有一直被盯著的壓力。", "會有簡單的分組討論，但不會佔用太多時間。", "老師會看大家反應調整講課速度，還算能跟上。", "偶爾會叫大家舉手回答，但不強迫，整體算隨和。", "互動不多不少，剛剛好適合不喜歡太嗨但又不想睡著的人。", "有時候會放影片給大家看再寫心得，滿輕鬆的。", "算是很典型的點名、聽課、下課的節奏。"]
    harvest_pool = ["雖然期末有點趕，但整個做完回頭看，真的覺得自己成長很多。", "老師教的東西很貼近實務，感覺以後出社會用得到。", "這門課讓我對這個領域完全改觀，重新找回學習的熱忱。", "以前覺得很抽象的理論，上完這堂課竟然瞬間通了。", "學到了很多解決問題的思維方式，不是只背死書而已。", "最大的收穫是學會怎麼把不同科目的知識串起來用。", "老師分享了很多他以前在業界的經驗，這些都是書本上學不到的。", "過程中踩了很多坑，但解決之後成就感超大，非常值得！", "推翻了我很多以前的刻板印象，整個視野都被打開了。", "上課的每一週都覺得有接收到新的東西，非常充實的一學期。", "訓練了很棒的邏輯分析能力，對未來做專題或寫報告超級有幫助。", "就算不是本科系的去聽，也能帶走一套很有用的思考框架。"]
    general_pool = ["老師人很好，下課問問題都很有耐心解答。", "助教批改作業的速度很快，而且給的 feedback 很詳細。", "教室冷氣超冷，記得帶外套...", "早八的課真的起不來，但我還是為了這堂課硬撐過去了。", "每次搶這堂課都搶破頭，能選到真的運氣好。", "課本滿厚的，建議去買二手書比較划算。", "教室插座不多，帶筆電去的話記得先充飽電。", "老師偶爾會遲到個幾分鐘，但通常都會準時下課。", "期中考前一週會有重點大放送，千萬不能翹課！", "點名方式是用傳簽到單的，有時候會忘記簽。", "上完這堂課剛好可以去排學餐，時間完美。", "老師講話聲音滿輕柔的，坐太後面會聽不太清楚。"]
    final_comments = []
    final_comments.extend(random.sample(harvest_pool, 2))  
    final_comments.extend(random.sample(diff_pool, 2))     
    final_comments.extend(random.sample(eng_pool, 2))      
    final_comments.extend(random.sample(general_pool, 1))  
    random.shuffle(final_comments)
    chosen_names = random.sample(names, 7)
    return [{"user": chosen_names[i], "content": final_comments[i]} for i in range(7)]

# ==========================================
# 3. 初始化全局記憶體
# ==========================================
if 'current_page' not in st.session_state: st.session_state.current_page = "視覺化介面"
if 'saved_course' not in st.session_state: st.session_state.saved_course = "請選擇..."
if 'target_course_id' not in st.session_state: st.session_state.target_course_id = None 
if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'comments_db' not in st.session_state: st.session_state.comments_db = {}

# ==========================================
# 3. 初始化全局記憶體 (🚀 補回這個被漏掉的關鍵區塊)
# ==========================================
if 'current_page' not in st.session_state: st.session_state.current_page = "視覺化介面"
if 'saved_course' not in st.session_state: st.session_state.saved_course = "請選擇..."
if 'target_course_id' not in st.session_state: st.session_state.target_course_id = None 
if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'comments_db' not in st.session_state: st.session_state.comments_db = {}
if 'student_id' not in st.session_state: st.session_state.student_id = "User_" + str(random.randint(1000, 9999))
if 'clear_signal' not in st.session_state: st.session_state.clear_signal = 0

def navigate_to(page_name):
    st.session_state.current_page = page_name

# ==========================================
# 4. 視覺化介面 (🚀 UI 極淨微調版)
# ==========================================
if st.session_state.current_page == "視覺化介面":
    st.markdown("""<style>html, body, [data-testid="stAppViewContainer"] { overflow: hidden !important; } .block-container { max-width: 98% !important; padding: 1rem 1rem !important; }</style>""", unsafe_allow_html=True)
    
    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px; margin-top: -30px;'>📊 視覺化分析中心</h2>", unsafe_allow_html=True)
    
    # 🚀 縮小左側邊欄寬度 (從原本的 1.2, 4 改為 0.85, 4.15)
    col_nav, col_main = st.columns([0.85, 4.15])

    # ------------------------------------------
    # 👁️ 隱藏在原生側邊欄的眼動儀控制面板 (實驗者專用)
    # ------------------------------------------
    with st.sidebar:
        with st.expander("👁️ 實驗控制面板 (主試者專用)", expanded=True):
            st.markdown(f"<div style='color:#2E7D32; font-weight:bold; font-size:12px; margin-bottom:8px;'>目前受測者 ID: {st.session_state.student_id}</div>", unsafe_allow_html=True)
            st.markdown("""<style>div[data-testid="stTextInput"]:has(input[aria-label="TRACKER_BRIDGE"]) {position: absolute !important; left: -9999px !important; opacity: 0 !important; height: 0px !important; width: 0px !important; pointer-events: none !important;}</style>""", unsafe_allow_html=True)
            st.text_input("TRACKER_BRIDGE", key="tracker_bridge", label_visibility="collapsed")
            
            tracker_html = f"""
            <div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 8px; margin-bottom: 10px;">
                <button id="btn-start" style="padding:10px; background:#E8F5E9; color:#2E7D32; border:1px solid #C8E6C9; border-radius:8px; font-weight:bold; cursor:pointer;">▶️ 手動開啟追蹤</button>
                <button id="btn-stop" style="display:none; padding:10px; background:#FFEBEE; color:#C62828; border:1px solid #FFCDD2; border-radius:8px; font-weight:bold; cursor:pointer;">⏸️ 暫停並強制上傳</button>
                <div id="status-light" style="font-size:12px; font-weight:bold; color:#777; text-align:center;">本地暫存: 0 筆等待發送</div>
            </div>
            <script>
                const p = window.parent; const d = p.document; const LOCAL_KEY = 'tracker_v4_backup';
                if(typeof p.__IS_TRACKING__ === 'undefined') p.__IS_TRACKING__ = false;
                const backSignal = "{st.session_state.clear_signal}";
                if (p.__CLEAR_SIG__ !== backSignal) {{ localStorage.removeItem(LOCAL_KEY); p.__CLEAR_SIG__ = backSignal; }}
                p.__ADD_LOG__ = function(type, detail, x_pos = null, y_pos = null) {{
                    if(!p.__IS_TRACKING__) return; 
                    const now = new Date(); const ms = Date.now(); const pad = (n, w=2) => String(n).padStart(w, '0');
                    const timeStr = now.getFullYear() + '-' + pad(now.getMonth()+1) + '-' + pad(now.getDate()) + ' ' + pad(now.getHours()) + ':' + pad(now.getMinutes()) + ':' + pad(now.getSeconds()) + '.' + pad(now.getMilliseconds(), 3);
                    const scrollY = d.documentElement.scrollTop || d.body.scrollTop || 0;
                    const vW = p.innerWidth; const vH = p.innerHeight; const dpr = p.devicePixelRatio || 1;
                    const logEntry = {{time: timeStr, timestamp_ms: ms, scroll_y: scrollY, viewport_w: vW, viewport_h: vH, pixel_ratio: dpr, current_section: '網頁互動', action_type: type, action_detail: detail, x: x_pos, y: y_pos, url: p.location.href}};
                    let backup = JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]'); backup.push(logEntry); localStorage.setItem(LOCAL_KEY, JSON.stringify(backup)); updateUI();
                }};
                if (p.__HEARTBEAT__) clearInterval(p.__HEARTBEAT__);
                p.__HEARTBEAT__ = setInterval(() => {{ if(p.__IS_TRACKING__) p.__ADD_LOG__('heartbeat', '系統定期快照', null, null); }}, 1000);
                p.__SEND_BATCH__ = function() {{
                    let backup = JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]'); if(backup.length === 0) return;
                    try {{
                        const input = d.querySelector('input[aria-label="TRACKER_BRIDGE"]');
                        if(input) {{
                            const dataStr = JSON.stringify({{id: Date.now(), data: backup}});
                            const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            input.focus(); nativeSetter.call(input, dataStr); input.dispatchEvent(new Event('input', {{ bubbles: true }})); input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            localStorage.removeItem(LOCAL_KEY); updateUI();
                        }}
                    }} catch(e) {{ console.error("發送失敗", e); }}
                }};
                if (p.__BATCH_TIMER__) clearInterval(p.__BATCH_TIMER__);
                p.__BATCH_TIMER__ = setInterval(() => {{ if(p.__IS_TRACKING__) p.__SEND_BATCH__(); }}, 30000);
                p.__CLICK_LST__ = function(e) {{ if(!p.__IS_TRACKING__) return; let tagName = e.target.tagName ? e.target.tagName.toUpperCase() : 'UNKNOWN'; let text = e.target.innerText || e.target.value || e.target.getAttribute('aria-label') || ''; let cleanText = typeof text === 'string' ? text.substring(0, 50).trim().replace(/\\n/g, ' ') : ''; p.__ADD_LOG__('click_element', '[' + tagName + '] ' + cleanText, e.clientX, e.clientY); }};
                if (p.__CLICK_LST_BOUND__) d.removeEventListener('click', p.__CLICK_LST_BOUND__, true);
                p.__CLICK_LST_BOUND__ = p.__CLICK_LST__; d.addEventListener('click', p.__CLICK_LST_BOUND__, true);
                
                const btnStart = document.getElementById('btn-start'); const btnStop = document.getElementById('btn-stop'); const statusLight = document.getElementById('status-light');
                function updateUI() {{
                    if(p.__IS_TRACKING__) {{ btnStart.style.display = 'none'; btnStop.style.display = 'block'; }} 
                    else {{ btnStart.style.display = 'block'; btnStop.style.display = 'none'; }}
                    let backup = JSON.parse(localStorage.getItem(LOCAL_KEY) || '[]'); const count = backup.length;
                    statusLight.innerText = `本地暫存: ${{count}} 筆等待發送 (每30秒自動同步)`;
                    statusLight.style.color = count > 50 ? '#D32F2F' : (count > 0 ? '#F57C00' : '#388E3C');
                }}
                updateUI(); if(window.__UI_TIMER__) clearInterval(window.__UI_TIMER__); window.__UI_TIMER__ = setInterval(updateUI, 1000); 
                btnStart.onclick = () => {{ p.__IS_TRACKING__ = true; p.__ADD_LOG__('experiment_start', '打板點擊：手動開始實驗', null, null); updateUI(); }};
                btnStop.onclick = () => {{ if(p.__IS_TRACKING__) {{ p.__ADD_LOG__('experiment_end', '打板點擊：結束實驗', null, null); }} p.__IS_TRACKING__ = false; p.__SEND_BATCH__(); updateUI(); }};
            </script>
            """
            components.html(tracker_html, height=110)
            if st.button("🗑️ 清空紀錄", use_container_width=True):
                try:
                    with psycopg2.connect(SUPABASE_URI) as conn:
                        with conn.cursor() as cursor: cursor.execute("TRUNCATE TABLE user_behavior_logs_v4 RESTART IDENTITY;")
                        conn.commit()
                    st.session_state.clear_signal += 1 
                    st.success("✅ 紀錄已清空！")
                    st.rerun()
                except Exception as e: st.error(f"清空失敗: {e}")

    # ------------------------------------------
    # 🟦 左側邊欄：課程選擇列表 (鎖定高度 776px)
    # ------------------------------------------
    with col_nav:
        with st.container(height=776, border=True):
            st.markdown("<div style='font-weight:bold; color:#555; font-size:1.1rem; margin-bottom:15px;'>📚 點擊切換課程</div>", unsafe_allow_html=True)
            
            # 🚀 移除 "請選擇..."，保留乾淨的 8 門課清單
            course_options = data["課程名稱"].tolist()
            
            # 💡 修改 1：將 Radio 綁定的初始狀態設為 None，確保一開始是淨空的
            if "course_radio" not in st.session_state:
                st.session_state.course_radio = None

            # 🚀 關鍵修復：加入「last_chart_sel」紀錄，解決散點圖與按鈕狀態互相打架的 Bug
            chart_state = st.session_state.get("scatter_chart")
            curr_sel = chart_state.get("selection", {}) if chart_state else {}
            
            if "last_chart_sel" not in st.session_state:
                st.session_state.last_chart_sel = None

            # 只有當「散點圖的選擇發生改變時」，才讓散點圖去覆蓋目標課程 (擋掉無限回彈)
            if curr_sel != st.session_state.last_chart_sel:
                st.session_state.last_chart_sel = curr_sel
                if curr_sel and len(curr_sel.get("points", [])) > 0:
                    st.session_state.target_course_id = curr_sel["points"][0]["customdata"][0]
                    st.session_state.saved_course = curr_sel["points"][0]["customdata"][1]
                    st.session_state.course_radio = st.session_state.saved_course

            # 產生 Radio Menu (受測者直接點，不用下拉)
            # 💡 修改 2：加入 index=None 參數，這是讓選單可以「都不選」的關鍵魔法！
            selected_course = st.radio(
                "選擇目標課程", 
                course_options, 
                key="course_radio", 
                index=None, 
                label_visibility="collapsed"
            )
            
            # 確保有選東西時才去存 ID，沒選就給 None
            if selected_course:
                st.session_state.saved_course = selected_course
                st.session_state.target_course_id = data[data['課程名稱'] == selected_course]['選課代號'].tolist()[0]
            else:
                st.session_state.target_course_id = None

    # ------------------------------------------
    # 🔲 右側主戰場：2x2 矩陣 (鎖定高度各 380px)
    # ------------------------------------------
    with col_main:
        col_left, col_right = st.columns([1, 1.4])

        # 【左上：散點圖】
        with col_left:
            with st.container(height=380, border=True):
                st.markdown("<div style='font-weight:bold; color:#555; font-size:1rem;'>📈 課程分佈散點圖</div>", unsafe_allow_html=True)
                fig_scatter = px.scatter(data, x="難度", y="教學參與性", hover_name="課程名稱", custom_data=["選課代號", "課程名稱"])
                selected_idx = np.where(data["課程名稱"] == selected_course)[0].tolist() if selected_course and selected_course in data["課程名稱"].values else None
                fig_scatter.update_traces(selectedpoints=selected_idx, marker=dict(color='#D9534F', size=14, opacity=0.8, line=dict(width=1, color='white')))
                fig_scatter.update_layout(height=310, xaxis_title="難度", yaxis_title="參與性", xaxis=dict(range=[0.5, 5.5], gridcolor='#EEE'), yaxis=dict(range=[0.5, 5.5], gridcolor='#EEE'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), clickmode='event+select', dragmode=False)
                st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points", key="scatter_chart")

        # 【左下：討論區】
        with col_left:
            with st.container(height=380, border=True):
                st.markdown("<div style='font-weight:bold; color:#555; font-size:1rem;'>💬 選課情報討論區</div>", unsafe_allow_html=True)
                if st.session_state.target_course_id:
                    c_code = st.session_state.target_course_id
                    c_info = data[data["選課代號"] == c_code].iloc[0]
                    if c_code not in st.session_state.comments_db: 
                        st.session_state.comments_db[c_code] = generate_fake_comments(c_code, c_info['難度'], c_info['教學參與性'])
                    
                    for comment in st.session_state.comments_db[c_code]:
                        st.markdown(f"""
                        <div style="background-color: #F8F6F1; padding: 12px 14px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #A3968C; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
                            <div style="font-weight: 800; font-size: 15px; color: #333; margin-bottom: 4px;">{comment['user']}</div>
                            <div style="font-size: 14px; color: #444; line-height: 1.6;">{comment['content']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.markdown("<div style='color:#aaa; font-size:14px; text-align:center; padding-top:100px;'>等待選擇課程...</div>", unsafe_allow_html=True)

        # 【右上：完整課程詳細資訊】
        with col_right:
            with st.container(height=380, border=True):
                st.markdown("<div style='font-weight:bold; color:#555; font-size:1rem;'>✨ 課程完整資訊</div>", unsafe_allow_html=True)
                if st.session_state.target_course_id:
                    c_data = data[data["選課代號"] == st.session_state.target_course_id].iloc[0]
                    st.markdown(f"<div style='background-color: #E2DCD5; padding: 4px 12px; border-radius: 8px; display: inline-block; margin-bottom: 10px; font-weight: bold; color: #222; font-size: 13px;'>[112-上學期] [{c_data['選課代號']}] {c_data['科目簡稱']}</div>", unsafe_allow_html=True)
                    
                    # 🚀 由於拔掉了最下方的加入收藏按鈕，我順手將這個資訊顯示框的高度拉高到 280 (原本是 230)，減少受測者上下滾動的麻煩
                    with st.container(height=280, border=False):
                        col_info1, col_info2 = st.columns(2)
                        with col_info1:
                            st.markdown(f"**選課代號：** {c_data['選課代號']}")
                            st.markdown(f"**開課班級：** {c_data['開課班級']}")
                            st.markdown(f"**科目簡稱：** {c_data['科目簡稱']}")
                            st.markdown(f"**學分數：** {c_data.get('學分數', 2)}")
                            st.markdown(f"**必選修：** {'必修' if str(c_data['必選修']).upper() == 'M' else '選修'}")
                        with col_info2:
                            st.markdown(f"**上課時間：** {c_data['上課時間']}")
                            st.markdown(f"**EMI註記：** {c_data['EMI註記']}")
                            st.markdown(f"**授課方式：** {c_data['授課方式']}")
                            st.markdown(f"**授課語言：** {c_data['授課語言']}")
                            st.markdown(f"**系所：** {c_data['系所']}")
                        
                        st.markdown(f"""<div style='background-color: #F8F6F1; padding: 10px; border-radius: 8px; margin-top:10px;'><b>📖 課程描述_中：</b><br><span style='font-size:13px;'>{c_data.get('課程描述_中', f'本課程將介紹{c_data["科目簡稱"]}之核心理論與實務應用。')}</span></div>""", unsafe_allow_html=True)
                        st.markdown(f"""<div style='background-color: #F8F6F1; padding: 10px; border-radius: 8px; margin-top:8px;'><b>📖 課程描述_英：</b><br><span style='font-size:13px;'>{c_data.get('課程描述_英', f'This course provides an overview of {c_data["科目簡稱"]} through theory and practice.')}</span></div>""", unsafe_allow_html=True)
                        
                        if '評分標準' in c_data:
                            grading_raw = c_data['評分標準']
                            grading_dict = {}
                            if pd.notna(grading_raw) and str(grading_raw).strip() != "":
                                try:
                                    if isinstance(grading_raw, dict): grading_dict = grading_raw
                                    else: grading_dict = json.loads(str(grading_raw).replace("'", '"'))
                                except: pass
                            
                            if grading_dict:
                                st.markdown("<div style='margin-top: 20px; font-weight: bold; color: #333; font-size: 15px;'>📊 評分比例與標準：</div>", unsafe_allow_html=True)
                                grading_html = "<div style='background-color: #FFFFFF; border: 1px solid #DCD5CE; border-radius: 10px; padding: 14px; margin-top: 5px;'>"
                                for item, desc in grading_dict.items():
                                    pct_match = re.search(r'(\d+)%', desc)
                                    pct_val = int(pct_match.group(1)) if pct_match else (int(re.search(r'(\d+)', desc).group(1)) if re.search(r'(\d+)', desc) else 0)
                                    grading_html += f"<div style='margin-bottom: 12px;'><div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;'><span style='font-size: 14px; font-weight: 800; color: #222; background-color: #EFEBE8; padding: 4px 10px; border-radius: 14px;'>📌 {item}</span><span style='font-size: 14px; font-weight: 800; color: #4A7C59;'>{desc}</span></div><div style='background-color: #EAE6E3; border-radius: 4px; height: 8px; width: 100%; overflow: hidden;'><div style='background-color: #4A7C59; height: 100%; width: {pct_val}%; border-radius: 4px;'></div></div></div>"
                                grading_html += "</div>"
                                st.markdown(grading_html, unsafe_allow_html=True)

                        if '十八週進度' in c_data:
                            syllabus_raw = c_data['十八週進度']
                            parsed_syllabus = None
                            if pd.notna(syllabus_raw) and str(syllabus_raw).strip() != "":
                                try:
                                    if isinstance(syllabus_raw, (dict, list)): parsed_syllabus = syllabus_raw
                                    else: parsed_syllabus = json.loads(str(syllabus_raw).replace("'", '"'))
                                except: pass
                                    
                            if parsed_syllabus:
                                st.markdown("<div style='margin-top: 20px; font-weight: bold; color: #333; font-size: 15px;'>🗓️ 十八週課程大綱：</div>", unsafe_allow_html=True)
                                html_weeks = "<div style='border: 1px solid #DCD5CE; border-radius: 8px; overflow: hidden; margin-top: 5px;'>"
                                week_contents = parsed_syllabus if isinstance(parsed_syllabus, list) else [parsed_syllabus.get(f"W{i}", "無資料") for i in range(1, 19)]
                                for i, w_content in enumerate(week_contents, start=1):
                                    bg_color = "#FFFFFF" if i % 2 != 0 else "#F8F6F1"
                                    html_weeks += f"<div style='background-color: {bg_color}; padding: 8px 12px; border-bottom: 1px solid #EAE6E3; display: flex; align-items: flex-start;'><span style='font-weight: 800; color: #4A7C59; width: 55px; font-size: 14px; padding-top: 2px;'>第{i}週</span><span style='font-size: 14px; color: #444; flex: 1; line-height: 1.5;'>{w_content}</span></div>"
                                html_weeks += "</div>"
                                st.markdown(html_weeks, unsafe_allow_html=True)
                else:
                    st.info("請從左側點選課程以載入詳細規格。")

        # 【右下：雙小圖表並排】
        with col_right:
            with st.container(height=380, border=True):
                st.markdown("<div id='zone-charts' style='display:none;'></div>", unsafe_allow_html=True)
                cc1, cc2 = st.columns(2)
                if st.session_state.target_course_id:
                    c_id = st.session_state.target_course_id
                    real_difficulty = float(c_data['難度']) 
                    
                    with cc1:
                        st.markdown("<div style='font-weight:bold; color:#555; text-align:center; font-size:0.9rem;'>📊 去年成績分佈</div>", unsafe_allow_html=True)
                        dist_df = get_fixed_grade_dist_data(c_id, real_difficulty)
                        fig_dist = go.Figure(data=[go.Bar(x=dist_df['Range'], y=dist_df['Count'], marker_color='#85ACCB')])
                        fig_dist.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(tickfont=dict(size=8)), yaxis=dict(tickfont=dict(size=8)))
                        st.plotly_chart(fig_dist, use_container_width=True, config={'staticPlot': True}, key="bar_sub")
                        
                    with cc2:
                        st.markdown("<div style='font-weight:bold; color:#555; text-align:center; font-size:0.9rem;'>📈 歷年修課趨勢</div>", unsafe_allow_html=True)
                        trend_df = get_fixed_trend_data(c_id, real_difficulty)
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.AvgScore, name='平均', line=dict(color='#C85A5A', width=2)))
                        fig_trend.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.Students, name='人數', line=dict(color='#4A7C59', width=2), yaxis='y2'))
                        fig_trend.update_layout(height=280, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis=dict(tickfont=dict(size=8)), yaxis=dict(range=[0,100], tickfont=dict(size=8)), yaxis2=dict(overlaying='y', side='right', range=[0,150], tickfont=dict(size=8)))
                        st.plotly_chart(fig_trend, use_container_width=True, config={'staticPlot': True}, key="line_sub")
                else:
                    st.plotly_chart(go.Figure().update_layout(height=280, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False)), use_container_width=True, key="empty_sub")