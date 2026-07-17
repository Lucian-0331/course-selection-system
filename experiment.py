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
st.set_page_config(page_title="🎓 選課決策系統", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<meta name="google" content="notranslate">
<style>
    /* --- 全局共用 CSS --- */
    .stApp { background-color: #EAE6E3; }
    [data-testid="stSidebar"] { background-color: #F8F6F1; border-right: 1px solid #D4CCC5; }
    header { background-color: transparent !important; }
    
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
        border-radius: 20px; font-weight: 800; height: 40px !important; 
        background-color: #EFEBE8 !important; border: 1px solid #DCD5CE !important;  
        color: #333333 !important; transition: all 0.3s ease; 
    }
    .stButton>button:hover { 
        background-color: #E4DCD3 !important; border-color: #D2C8BE !important;
        transform: translateY(-2px);
    }
    
    /* 🚨 側邊欄專屬按鈕樣式 (還原保留) 🚨 */
    [data-testid="stSidebar"] .stButton>button {
        background-color: transparent !important; 
        border: none !important; 
        box-shadow: none !important;
        text-align: left !important; 
        justify-content: flex-start !important; 
        font-size: 1.1rem !important; 
        height: auto !important; 
        padding: 10px 15px !important; 
        margin-bottom: 8px !important; 
        display: flex !important;      
        align-items: center !important;
        gap: 12px !important;
        border-radius: 10px !important; /* 蓋掉膠囊形狀 */
    }
    [data-testid="stSidebar"] .stButton>button:hover { 
        background-color: #EAE3DC !important; 
        transform: translateY(0px) !important; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 核心資料與演算法 (🚀 最終完美版：精準類別篩選)
# ==========================================
import os

url_params = st.query_params
course_type = url_params.get("course", "new_ed")
session_key = f"sampled_courses_{course_type}"

if session_key not in st.session_state:
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(current_dir, '0610-course.db')

        with sqlite3.connect(db_path, timeout=10) as conn:
            # 動態抓取資料表名稱
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = cursor.fetchall()
            
            if not tables:
                raise ValueError(f"連線成功，但 {db_path} 裡面找不到任何資料表！")
            
            actual_table_name = tables[0][0]
            
            # 🔍 根據你提供的真實類別進行精準篩選！(使用 LIKE 避免隱藏空白字元干擾)
            if course_type == "new_ed":
                # 篩選：一般通識
                query = f'SELECT * FROM "{actual_table_name}" WHERE 課程類別 LIKE \'%一般通識%\' ORDER BY RANDOM() LIMIT 8'
            elif course_type == "new_pro":
                # 篩選：資訊類通識
                query = f'SELECT * FROM "{actual_table_name}" WHERE 課程類別 LIKE \'%資訊類通識%\' ORDER BY RANDOM() LIMIT 8'
            else:
                query = f'SELECT * FROM "{actual_table_name}" ORDER BY RANDOM() LIMIT 8'
                
            df = pd.read_sql_query(query, conn)

    except Exception as e:
        st.error(f"⚠️ 資料庫讀取失敗！錯誤訊息: {e}")
        df = pd.DataFrame()

    # 🚨 核心安全防護 (空資料防護，同步新增「評分標準」欄位)
    if df.empty:
        df = pd.DataFrame(columns=['選課代號', '配當系所.1', '開課班級簡稱', '科目簡稱', 'yms_smester', '系所', '開課班級', '課程名稱', '學期', '教學參與性', '難度', '十八週進度', '評分標準'])
        df.loc[0] = ['無', '請選擇...', '請選擇...', '請選擇...', '1', '請選擇...', '請選擇...', '請選擇...', '上學期', 3.0, 3.0, '{}', '{}']
    else:
        # 進行欄位轉換
        df['系所'] = df['配當系所.1'].fillna('未知系所')
        df['開課班級'] = df['開課班級簡稱'].fillna('未知班級')
        df['課程名稱'] = df['科目簡稱'].astype(str) + " (" + df['開課班級'] + ")"

        def map_semester(x):
            x_str = str(x).strip()
            return '上學期' if x_str in ['1', '1.0'] else ('下學期' if x_str in ['2', '2.0'] else '(無)')
        
        df['學期'] = df['yms_smester'].apply(map_semester)
        df = df.drop_duplicates(subset=['選課代號', '學期']).reset_index(drop=True)
        
        np.random.seed(42)
        df['教學參與性'] = np.random.uniform(2.5, 5.0, size=len(df)).round(1)
        df['難度'] = np.random.uniform(2.0, 5.0, size=len(df)).round(1)
        
    st.session_state[session_key] = df

data = st.session_state[session_key]

@st.cache_data
def get_fixed_trend_data(course_code):
    random.seed(course_code)
    return pd.DataFrame({"Year": ['109', '110', '111', '112', '113'], "Students": [random.randint(40, 120) for _ in range(5)], "AvgScore": [random.randint(65, 95) for _ in range(5)]})

@st.cache_data
def get_fixed_grade_dist_data(course_code, difficulty):
    random.seed(course_code)
    bins = ["0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-89", "90-100"]
    weights = [0, 0, 0, 1, 2, 5, 15, 30, 35, 12] # Default Normal
    student_count = random.randint(45, 120)
    dist = [w * random.uniform(0.8, 1.2) for w in weights]
    total = sum(dist)
    if total > 0: dist = [int(round((val/total) * student_count)) for val in dist]
    return pd.DataFrame({"Range": bins, "Count": dist})

def generate_fake_comments(course_code, difficulty, engagement):
    random.seed(course_code)
    names = ["工工三甲小神童", "期末被當專業戶", "逢甲路過小精靈", "學分小偷", "準時下課推廣大使", "第一排的學霸"]
    contents = [
        "這門課真的硬，期中考都是計算題，建議一定要把老師發的練習題算三遍以上。",
        "期末專案要跑程式模擬，雖然很肝，但做完會覺得自己變強了很多。",
        "老師超幽默，會舉很多工廠實作的例子！",
        "上課節奏很快，互動超多，完全不會想睡覺！",
        "給分很甜，老師是活菩薩，基本上有交作業都會過。",
        "大班演講課感很重，老師基本上一直唸投影片。"
    ]
    return [{"user": random.choice(names), "content": random.choice(contents)} for _ in range(5)]

# ==========================================
# 3. 初始化全局記憶體
# ==========================================
if 'current_page' not in st.session_state: st.session_state.current_page = "視覺化介面"
if 'saved_dept' not in st.session_state: st.session_state.saved_dept = "請選擇..."
if 'saved_class' not in st.session_state: st.session_state.saved_class = "請選擇..."
if 'saved_semester' not in st.session_state: st.session_state.saved_semester = "請選擇..."
if 'saved_course' not in st.session_state: st.session_state.saved_course = "請選擇..."
if 'target_course_id' not in st.session_state: st.session_state.target_course_id = None 
if 'my_courses' not in st.session_state: st.session_state.my_courses = []
if 'comments_db' not in st.session_state: st.session_state.comments_db = {}

def navigate_to(page_name):
    st.session_state.current_page = page_name

# ==========================================
# 4. 側邊欄
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>🎓 選課決策系統</h2>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background-color: #FFFFFF; padding: 10px; border-radius: 10px; border: 1px solid #DCD5CE; margin-bottom: 20px; text-align: center;'>
        <span style='font-size: 20px;'>👤</span><br>
        <span style='font-weight: 800; color: #333;'>王小明 (Ming Wang)</span><br>
        <span style='font-size: 12px; color: #888;'>工工系</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button("📊 視覺化分析", use_container_width=True): navigate_to("視覺化介面")
    if st.button("❤️ 我的收藏", use_container_width=True): navigate_to("我的收藏")
    st.markdown("<hr>", unsafe_allow_html=True)
    with st.expander("👁️ 眼動儀實驗控制面板", expanded=True):
        st.caption("實驗追蹤中...")
        st.button("🗑️ 清空紀錄", use_container_width=True)

# ==========================================
# 5. 視覺化介面 (大改版佈局)
# ==========================================
if st.session_state.current_page == "視覺化介面":
    st.markdown("""<style>html, body, [data-testid="stAppViewContainer"] { overflow: hidden !important; } .block-container { max-width: 98% !important; padding: 1rem 1rem !important; }</style>""", unsafe_allow_html=True)
    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 5px; margin-top: -15px;'>📊 視覺化分析中心</h2>", unsafe_allow_html=True)

   # 🟦 頂部過濾列
    with st.container(border=True):
        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1.2, 1.2, 1.2, 2.5, 0.8])
        
        dept_options = ["請選擇..."] + sorted(data["系所"].unique().tolist())
        # 實驗控制：自動鎖定第一個真實選項 (index=1)，並加入 disabled=True 讓受測者無法點擊
        dept = col_f1.selectbox("📂 1. 系所", dept_options, index=1 if len(dept_options) > 1 else 0, disabled=True)
        st.session_state.saved_dept = dept
        
        class_options = ["請選擇..."] + sorted(data[data["系所"]==dept]["開課班級"].unique().tolist()) if dept != "請選擇..." else ["請選擇..."]
        # 實驗控制：自動鎖定並關閉點擊
        class_sel = col_f2.selectbox("🏷️ 2. 班級", class_options, index=1 if len(class_options) > 1 else 0, disabled=True)
        st.session_state.saved_class = class_sel
        
        sem_options = ["請選擇..."] + sorted(data[(data["系所"]==dept) & (data["開課班級"]==class_sel)]["學期"].unique().tolist()) if class_sel != "請選擇..." else ["請選擇..."]
        # 實驗控制：自動鎖定並關閉點擊
        semester_sel = col_f3.selectbox("🗓️ 3. 學期", sem_options, index=1 if len(sem_options) > 1 else 0, disabled=True)
        st.session_state.saved_semester = semester_sel
        
        filtered = data[(data["系所"]==dept) & (data["開課班級"]==class_sel) & (data["學期"]==semester_sel)] if semester_sel != "請選擇..." else pd.DataFrame()
        course_options = ["請選擇..."] + filtered["課程名稱"].tolist() if not filtered.empty else ["請選擇..."]
        
        # 捕捉散點圖點擊
        chart_state = st.session_state.get("scatter_chart")
        curr_sel = chart_state.get("selection", {}) if chart_state else {}
        if curr_sel and len(curr_sel.get("points", [])) > 0:
            st.session_state.target_course_id = curr_sel["points"][0]["customdata"][0]
            st.session_state.saved_course = curr_sel["points"][0]["customdata"][1]

        # 🚨 目標課程保持開放 (不加 disabled)，因為受測者還需要透過這裡或左側圖表來選課
        selected_course = col_f4.selectbox("🎯 4. 目標課程", course_options, index=course_options.index(st.session_state.saved_course) if st.session_state.saved_course in course_options else 0)
        if selected_course != "請選擇...":
            st.session_state.saved_course = selected_course
            st.session_state.target_course_id = filtered[filtered['課程名稱'] == selected_course]['選課代號'].tolist()[0]

        with col_f5:
            # 🚨 加上緩衝區讓重置按鈕精準對齊下拉選單的底部 🚨
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🔄 重置", use_container_width=True):
                st.session_state.saved_dept = st.session_state.saved_class = st.session_state.saved_semester = st.session_state.saved_course = "請選擇..."
                st.session_state.target_course_id = None
                st.rerun()

    # 🔲 下方主戰情室
    col_left, col_right = st.columns([1, 1.4])

    # ------------------------------------------
    # ⬅️ 左半部：散點圖 (上) 與 討論區 (下)
    # ------------------------------------------
    with col_left:
        # 【左上：散點圖】
        with st.container(height=330, border=True):
            st.markdown("<div style='font-weight:bold; color:#555; font-size:1rem;'>📈 課程分佈散點圖</div>", unsafe_allow_html=True)
            if filtered.empty:
                st.plotly_chart(go.Figure().update_layout(height=260, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False), annotations=[dict(text="請完成上方篩選", x=0.5, y=0.5, showarrow=False)]), use_container_width=True, key="sc_empty")
            else:
                fig_scatter = px.scatter(filtered, x="難度", y="教學參與性", hover_name="課程名稱", custom_data=["選課代號", "課程名稱"])
                selected_idx = np.where(filtered["課程名稱"] == selected_course)[0].tolist() if selected_course != "請選擇..." else None
                fig_scatter.update_traces(selectedpoints=selected_idx, marker=dict(color='#D9534F', size=14, opacity=0.8, line=dict(width=1, color='white')))
                fig_scatter.update_layout(height=260, xaxis_title="難度", yaxis_title="參與性", xaxis=dict(range=[0.5, 5.5], gridcolor='#EEE'), yaxis=dict(range=[0.5, 5.5], gridcolor='#EEE'), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=10, r=10, t=10, b=10), clickmode='event+select', dragmode=False)
                st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points", key="scatter_chart")

        # 【左下：討論區 (原右下)】
        with st.container(height=330, border=True):
            st.markdown("<div style='font-weight:bold; color:#555; font-size:1rem;'>💬 選課情報討論區</div>", unsafe_allow_html=True)
            if st.session_state.target_course_id:
                c_code = st.session_state.target_course_id
                c_info = data[data["選課代號"] == c_code].iloc[0]
                if c_code not in st.session_state.comments_db: st.session_state.comments_db[c_code] = generate_fake_comments(c_code, c_info['難度'], c_info['教學參與性'])
                for comment in st.session_state.comments_db[c_code]:
                    st.markdown(f'''<div style="background-color: #F8F6F1; padding: 8px; border-radius: 8px; margin-bottom: 6px; border-left: 4px solid #A3968C;"><span style="font-weight: 800; font-size: 11px;">{comment['user']}</span><br><span style="font-size: 12px; color: #444;">{comment['content']}</span></div>''', unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#aaa; font-size:13px; text-align:center; padding-top:50px;'>等待選擇課程...</div>", unsafe_allow_html=True)

    # ------------------------------------------
    # ➡️ 右半部：詳細資訊 (上) 與 雙圖表 (下)
    # ------------------------------------------
    with col_right:
      # 【右上：完整課程詳細資訊 (原左下並擴大)】
        with st.container(height=330, border=True):
            st.markdown("<div style='font-weight:bold; color:#555; font-size:1rem;'>✨ 課程完整資訊</div>", unsafe_allow_html=True)
            if st.session_state.target_course_id:
                c_data = data[data["選課代號"] == st.session_state.target_course_id].iloc[0]
                st.markdown(f"<div style='background-color: #E2DCD5; padding: 4px 12px; border-radius: 8px; display: inline-block; margin-bottom: 10px; font-weight: bold; color: #222; font-size: 13px;'>[112-上學期] [{c_data['選課代號']}] {c_data['科目簡稱']}</div>", unsafe_allow_html=True)
                
                # 內部捲動區：放置大量欄位
                with st.container(height=220, border=False):
                    col_info1, col_info2 = st.columns(2)
                    with col_info1:
                        st.markdown(f"**選課代號：** {c_data['選課代號']}")
                        st.markdown(f"**開課班級：** {c_data['開課班級']}")
                        st.markdown(f"**科目簡稱：** {c_data['科目簡稱']}")
                        st.markdown(f"**學分數：** {c_data.get('學分', 2)}")
                        st.markdown(f"**必選修：** {'必修' if str(c_data['必選修']).upper() == 'M' else '選修'}")
                    with col_info2:
                        st.markdown(f"**上課時間：** (一)09-11")
                        st.markdown(f"**EMI註記：** N")
                        st.markdown(f"**授課方式：** 實體上課")
                        st.markdown(f"**授課語言：** 中文")
                        st.markdown(f"**系所：** {c_data['系所']}")
                    
                    st.markdown(f"""<div style='background-color: #F8F6F1; padding: 10px; border-radius: 8px; margin-top:10px;'><b>📖 課程描述_中：</b><br><span style='font-size:13px;'>本課程將介紹{c_data['科目簡稱']}之核心理論與實務應用，內容包含模型推推導、數據分析與實際案例演練。</span></div>""", unsafe_allow_html=True)
                    st.markdown(f"""<div style='background-color: #F8F6F1; padding: 10px; border-radius: 8px; margin-top:8px;'><b>📖 課程描述_英：</b><br><span style='font-size:13px;'>This course provides an overview of {c_data['科目簡稱']} through theory and practice, focusing on data-driven decision making.</span></div>""", unsafe_allow_html=True)
                    
                    # 🚀 新增：評分標準動態渲染 (修復 Markdown 縮排判定成程式碼的問題)
                    if '評分標準' in c_data:
                        grading_raw = c_data['評分標準']
                        grading_dict = {}
                        if pd.notna(grading_raw) and str(grading_raw).strip() != "":
                            try:
                                if isinstance(grading_raw, dict):
                                    grading_dict = grading_raw
                                else:
                                    clean_grading = str(grading_raw).replace("'", '"')
                                    grading_dict = json.loads(clean_grading)
                            except:
                                pass
                        
                        if grading_dict:
                            st.markdown("<div style='margin-top: 20px; font-weight: bold; color: #333; font-size: 14px;'>📊 評分比例與標準：</div>", unsafe_allow_html=True)
                            grading_html = "<div style='background-color: #FFFFFF; border: 1px solid #DCD5CE; border-radius: 10px; padding: 12px; margin-top: 5px;'>"
                            
                            for item, desc in grading_dict.items():
                                # 🔍 自動從文字中提取百分比
                                pct_match = re.search(r'(\d+)%', desc)
                                pct_val = int(pct_match.group(1)) if pct_match else (int(re.search(r'(\d+)', desc).group(1)) if re.search(r'(\d+)', desc) else 0)
                                
                                # 🚨 改為單行疊加，徹底消除多餘的空白縮排
                                grading_html += f"<div style='margin-bottom: 10px;'>"
                                grading_html += f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 3px;'>"
                                grading_html += f"<span style='font-size: 12px; font-weight: 800; color: #222; background-color: #EFEBE8; padding: 2px 8px; border-radius: 12px;'>📌 {item}</span>"
                                grading_html += f"<span style='font-size: 12px; font-weight: 800; color: #4A7C59;'>{desc}</span>"
                                grading_html += f"</div>"
                                grading_html += f"<div style='background-color: #EAE6E3; border-radius: 4px; height: 6px; width: 100%; overflow: hidden;'>"
                                grading_html += f"<div style='background-color: #4A7C59; height: 100%; width: {pct_val}%; border-radius: 4px;'></div>"
                                grading_html += f"</div>"
                                grading_html += f"</div>"
                                
                            grading_html += "</div>"
                            st.markdown(grading_html, unsafe_allow_html=True)

                    # 🚀 十八週進度動態渲染
                    if '十八週進度' in c_data:
                        syllabus_raw = c_data['十八週進度']
                        syllabus_dict = {}
                        if pd.notna(syllabus_raw) and str(syllabus_raw).strip() != "":
                            try:
                                if isinstance(syllabus_raw, dict):
                                    syllabus_dict = syllabus_raw
                                else:
                                    clean_raw = str(syllabus_raw).replace("'", '"')
                                    syllabus_dict = json.loads(clean_raw)
                            except:
                                pass
                                
                            if syllabus_dict:
                                st.markdown("<div style='margin-top: 20px; font-weight: bold; color: #333; font-size: 14px;'>🗓️ 十八週課程大綱：</div>", unsafe_allow_html=True)
                                html_weeks = "<div style='border: 1px solid #DCD5CE; border-radius: 8px; overflow: hidden; margin-top: 5px;'>"
                                for i in range(1, 19):
                                    w_key = f"W{i}"
                                    w_content = syllabus_dict.get(w_key, "無資料")
                                    bg_color = "#FFFFFF" if i % 2 != 0 else "#F8F6F1"
                                    html_weeks += f"<div style='background-color: {bg_color}; padding: 6px 12px; border-bottom: 1px solid #EAE6E3; display: flex; align-items: flex-start;'><span style='font-weight: 800; color: #4A7C59; width: 45px; font-size: 12px; padding-top: 2px;'>第{i}週</span><span style='font-size: 12px; color: #444; flex: 1; line-height: 1.4;'>{w_content}</span></div>"
                                html_weeks += "</div>"
                                st.markdown(html_weeks, unsafe_allow_html=True)
                
                if st.button("❤️ 加入收藏", key="main_fav", use_container_width=True):
                    st.toast("已加入收藏！", icon="✨")
            else:
                st.info("請從左側點選課程以載入詳細規格。")

        # 【右下：雙小圖表並排 (原右上)】
        with st.container(height=330, border=True):
            st.markdown("<div id='zone-charts' style='display:none;'></div>", unsafe_allow_html=True)
            cc1, cc2 = st.columns(2)
            if st.session_state.target_course_id:
                c_id = st.session_state.target_course_id
                # 左圖：長條圖
                with cc1:
                    st.markdown("<div style='font-weight:bold; color:#555; text-align:center; font-size:0.9rem;'>📊 去年成績分佈</div>", unsafe_allow_html=True)
                    dist_df = get_fixed_grade_dist_data(c_id, 3.0)
                    fig_dist = go.Figure(data=[go.Bar(x=dist_df['Range'], y=dist_df['Count'], marker_color='#85ACCB')])
                    fig_dist.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', xaxis=dict(tickfont=dict(size=8)), yaxis=dict(tickfont=dict(size=8)))
                    st.plotly_chart(fig_dist, use_container_width=True, config={'staticPlot': True}, key="bar_sub")
                # 右圖：折線圖
                with cc2:
                    st.markdown("<div style='font-weight:bold; color:#555; text-align:center; font-size:0.9rem;'>📈 歷年修課趨勢</div>", unsafe_allow_html=True)
                    trend_df = get_fixed_trend_data(c_id)
                    fig_trend = go.Figure()
                    fig_trend.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.AvgScore, name='平均', line=dict(color='#C85A5A', width=2)))
                    fig_trend.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.Students, name='人數', line=dict(color='#4A7C59', width=2), yaxis='y2'))
                    fig_trend.update_layout(height=230, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False, xaxis=dict(tickfont=dict(size=8)), yaxis=dict(range=[0,100], tickfont=dict(size=8)), yaxis2=dict(overlaying='y', side='right', range=[0,150], tickfont=dict(size=8)))
                    st.plotly_chart(fig_trend, use_container_width=True, config={'staticPlot': True}, key="line_sub")
            else:
                st.plotly_chart(go.Figure().update_layout(height=230, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis=dict(visible=False), yaxis=dict(visible=False)), use_container_width=True, key="empty_sub")

# ==========================================
# 6. 我的收藏頁面 (略)
# ==========================================
elif st.session_state.current_page == "我的收藏":
    st.markdown("""
    <style>
        html, body, [data-testid="stAppViewContainer"] { overflow: hidden !important; }
        .block-container { height: 96vh !important; max-width: 98% !important; padding: 1.5rem 1rem 1rem 1rem !important; display: flex !important; flex-direction: column !important; overflow: hidden !important; }
        div[data-testid="stVerticalBlock"]:first-of-type { display: flex; flex-direction: column; height: 100%; }
        .timetable-full { width: 100%; height: 450px !important; border-collapse: collapse; table-layout: fixed; background-color: white; }
        .timetable-full th, .timetable-full td { border: 1px solid #EAE6E3; text-align: center; vertical-align: middle; font-size: 11px; height: 45px !important; }
        .timetable-full th { background-color: #F8F6F4; font-weight: 800; }
        .timetable-full td.filled { background-color: #DCD7D4; color: #222; font-weight: 900; border-radius: 4px; font-size: 11px !important; line-height: 1.1; }
        .timetable-full td.conflict { background-color: #FADBD8; color: #C0392B; font-weight: bold; font-size: 11px !important; }
        .fav-card { background-color: #F8F6F4; border: 1px solid #EAE6E3; border-radius: 10px; padding: 6px 12px; margin-bottom: 6px; display: flex; align-items: center; min-height: 40px; }
        .fav-enrolled { border-left: 6px solid #4A7C59 !important; background-color: #F0F4F0 !important; }
        [data-testid="column"]:nth-child(1) .stButton>button { height: 32px !important; min-height: 32px !important; padding: 2px 10px !important; font-size: 0.8rem !important; }
        [data-testid="stVerticalBlockBorderWrapper"]:has(.timetable-full) > div > div, [data-testid="stVerticalBlockBorderWrapper"]:has(.fav-card) > div > div { overflow-y: auto !important; overscroll-behavior: contain !important; padding-right: 5px; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background-color: #E2DCD5; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px;'>❤️ 我的收藏與模擬排課</h2>", unsafe_allow_html=True)

    all_favorites = st.session_state.my_courses
    enrolled_courses = [c for c in all_favorites if c["enrolled"]]

    days = ["一", "二", "三", "四", "五", "六", "日"]
    all_periods = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "A", "B", "C", "D"] 
    schedule_matrix = {d: {p: [] for p in all_periods} for d in days}
    conflicts = []
    
    for course in enrolled_courses:
        for t in course["time"]:
            if len(t) >= 2:
                d_key = t[0]
                p_key = str(int(t[1:])) if t[1:].isdigit() else t[1:]
                if d_key in schedule_matrix and p_key in schedule_matrix[d_key]: 
                    schedule_matrix[d_key][p_key].append(course)

    col_l, col_r = st.columns(2)

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

    with col_r:
        with st.container(height=650, border=True):
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

            display_periods = [p for p in all_periods if p in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"] or any(schedule_matrix[d][p] for d in days)]
            display_days = ["一", "二", "三", "四", "五"]
            for d in ["六", "日"]:
                if any(schedule_matrix[d][p] for p in display_periods):
                    display_days.append(d)

            table_html = f"<table class='timetable-full'><tr><th style='width:30px;'></th>" + "".join([f"<th>週{d}</th>" for d in display_days]) + "</tr>"
            for p in display_periods:
                table_html += f"<tr><td style='font-weight:bold; background:#F8F6F4;'>{p}</td>"
                for d in display_days:
                    cells = schedule_matrix[d][p]
                    if not cells: table_html += "<td></td>"
                    elif len(cells) == 1:
                        name = cells[0]['name'][:7] + ".." if len(cells[0]['name']) > 7 else cells[0]['name']
                        table_html += f"<td class='filled'>{name}</td>"
                    else: table_html += f"<td class='conflict'>!!!</td>"
                table_html += "</tr>"
            table_html += "</table>"
            st.markdown(table_html, unsafe_allow_html=True)