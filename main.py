import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import numpy as np
from collections import defaultdict
import re
import random

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
# 2. 共用資料讀取函數
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    try:
        with sqlite3.connect('courses.db') as conn:
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
def load_and_clean_data():
    try:
        try: df = pd.read_excel("data.xlsx", sheet_name="1131-114開課")
        except: df = pd.read_csv("data.xlsx - 1131-114開課.csv")
            
        df.columns = df.columns.astype(str).str.strip()
        cols_to_drop = ['sub_id', 'scr_dup', '配當系所', '課程編碼', '工具分類', 'seq_no', '周次', 'EMI註記', '配當年', '進度內容']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        rename_dict = {'yms_year': '年次', 'yms_smester': '學期', 'cls_id': '課程代碼', '開課班級簡稱': '開課班級', '科目簡稱': '課程名稱', '配當系所.1': '配當系所'}
        df = df.rename(columns=rename_dict)
        
        if '開課班級' in df.columns and '課程名稱' in df.columns:
            df['開課班級'] = df['開課班級'].fillna('未知班級')
            df['課程名稱'] = df['課程名稱'].astype(str) + " (" + df['開課班級'].astype(str) + ")"
        
        if '學期' in df.columns:
            df['學期'] = df['學期'].astype(str).replace({'1': '上學期', '2': '下學期', '1.0': '上學期', '2.0': '下學期'})
        
        name_col = '課程名稱' if '課程名稱' in df.columns else df.columns[7]
        code_col = '選課代號' if '選課代號' in df.columns else df.columns[5]
        
        if all(col in df.columns for col in ['年次', '學期']):
            df_unique = df.drop_duplicates(subset=['年次', '學期', code_col]).copy()
        else:
            df_unique = df.drop_duplicates(subset=[code_col]).copy()
            
        df_unique = df_unique.fillna("無")
        
        if all(col in df_unique.columns for col in ['年次', '學期']):
            df_unique['UID'] = "[" + df_unique['年次'].astype(str) + "-" + df_unique['學期'] + "] [" + df_unique[code_col].astype(str) + "] " + df_unique[name_col].astype(str)
        else:
            df_unique['UID'] = "[" + df_unique[code_col].astype(str) + "] " + df_unique[name_col].astype(str)
        return df_unique
    except Exception as e:
        return pd.DataFrame()

@st.cache_data
def get_fixed_trend_data(course_code):
    random.seed(course_code)
    return pd.DataFrame({"Year": ['109', '110', '111', '112', '113'], "Students": [random.randint(40, 120) for _ in range(5)], "AvgScore": [random.randint(65, 95) for _ in range(5)]})

df_courses = load_and_clean_data()

# ==========================================
# 3. 初始化全局記憶體 (防彈保險箱)
# ==========================================
if 'current_page' not in st.session_state: st.session_state.current_page = "系統首頁"
if 'saved_dept' not in st.session_state: st.session_state.saved_dept = "請選擇..."
if 'saved_class' not in st.session_state: st.session_state.saved_class = "請選擇..."
if 'saved_semester' not in st.session_state: st.session_state.saved_semester = "請選擇..."
if 'saved_course' not in st.session_state: st.session_state.saved_course = "請選擇..."
if 'target_course_id' not in st.session_state: st.session_state.target_course_id = None 
if 'search_term' not in st.session_state: st.session_state.search_term = ""

# 🎯 頭像相關記憶體
if 'avatar' not in st.session_state: st.session_state.avatar = "https://www.w3schools.com/howto/img_avatar.png" 
if 'show_uploader' not in st.session_state: st.session_state.show_uploader = False

# 🎯 個人偏好設定記憶體 (保證切換頁面不重置)
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
if "student_id" not in st.session_state: st.session_state.student_id = "B110565033"
if "department" not in st.session_state: st.session_state.department = "工工系"
if "year" not in st.session_state: st.session_state.year = "三年級"
if "editing" not in st.session_state: st.session_state.editing = False

def navigate_to(page_name, course_id=None, course_name=None):
    st.session_state.current_page = page_name
    if course_id: st.session_state.target_course_id = course_id
    if course_name: st.session_state.saved_course = course_name

# ==========================================
# 4. 側邊欄導覽列 
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
    st.markdown("---")
    st.button("🚪 登出系統", use_container_width=True)

# ==========================================
# 5. 路由系統
# ==========================================

if st.session_state.current_page == "系統首頁":
    current_enrolled_credits = sum(c['credits'] for c in st.session_state.my_courses if c.get('enrolled', False))
    accumulated_credits = 85 
    total_after_this_sem = accumulated_credits + current_enrolled_credits
    needed_credits = max(128 - total_after_this_sem, 0)

    st.title(f"👋 歡迎回來，{st.session_state.name.split(' ')[0]}！")
    st.markdown("<p style='font-size: 1.1rem; margin-bottom: 30px;'>在這裡掌握您的學習進度與最新課程動態，為新學期做好完美規劃。</p>", unsafe_allow_html=True)

    st.markdown("### 📊 畢業學分進度")
    col1, col2, col3 = st.columns(3)
    with col1:
        with st.container(border=True):
            st.markdown("<h4 style='color: #666;'>本學期預選學分</h4>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='font-size: 2.5rem; color: #4A7C59;'>{current_enrolled_credits} <span style='font-size: 1.2rem; color: #888;'>/ 25 學分</span></h2>", unsafe_allow_html=True)
            st.progress(min(current_enrolled_credits / 25, 1.0))
    with col2:
        with st.container(border=True):
            st.markdown("<h4 style='color: #666;'>累積畢業學分</h4>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='font-size: 2.5rem; color: #222;'>{total_after_this_sem} <span style='font-size: 1.2rem; color: #888;'>/ 128</span></h2>", unsafe_allow_html=True)
            st.progress(min(total_after_this_sem / 128, 1.0))
    with col3:
        with st.container(border=True):
            st.markdown("<h4 style='color: #666;'>距離畢業還需</h4>", unsafe_allow_html=True)
            st.markdown(f"<h2 style='font-size: 2.5rem; color: #C85A5A;'>{needed_credits} <span style='font-size: 1.2rem; color: #888;'>學分</span></h2>", unsafe_allow_html=True)
            if needed_credits > 40: st.markdown("<span style='color: #C85A5A; font-weight: 600;'>💡 建議本學期再修 2-3 門必修課</span>", unsafe_allow_html=True)
            else: st.markdown("<span style='color: #4A7C59; font-weight: 600;'>✨ 進度領先！可以多探索興趣領域</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🚀 為您推薦的專屬課程")
    rc1, rc2, rc3 = st.columns(3)
    recommendations = [
        {"name": "人因工程與實驗設計", "prof": "王教授", "time": "(四) 02-04", "match": "95%", "tags": ["專業必修", "實作豐富"]},
        {"name": "系統動力學", "prof": "李教授", "time": "(二) 02-04", "match": "88%", "tags": ["專業選修", "邏輯訓練"]},
        {"name": "資料庫設計", "prof": "張教授", "time": "(三) 06-08", "match": "82%", "tags": ["專業選修", "軟體應用"]},
    ]
    for i, course in enumerate(recommendations):
        with [rc1, rc2, rc3][i]:
            with st.container(border=True):
                st.markdown(f"#### {course['name']}")
                st.markdown(f"👨‍🏫 {course['prof']} | 🕒 {course['time']}")
                st.markdown(f"<span class='tag tag-match'>{course['match']} 契合度</span><span class='tag'>{course['tags'][0]}</span><span class='tag'>{course['tags'][1]}</span>", unsafe_allow_html=True)
                st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
                st.button("查看詳情", key=f"btn_hm_{i}", use_container_width=True, on_click=navigate_to, args=("詳細課程", None, course['name']))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔥 全校熱門搶手課程")
    with st.container(border=True):
        hot_courses = [
            {"rank": 1, "name": "Python 程式設計與資料分析", "dept": "通識中心", "quota": "剩餘 2 名", "color": "#C85A5A"},
            {"rank": 2, "name": "人工智慧概論", "dept": "資訊工程學系", "quota": "剩餘 5 名", "color": "#C85A5A"},
            {"rank": 3, "name": "投資理財實務", "dept": "財務金融學系", "quota": "剩餘 12 名", "color": "#D4A373"},
            {"rank": 4, "name": "心理學導論", "dept": "通識中心", "quota": "剩餘 20 名", "color": "#4A7C59"}
        ]
        for course in hot_courses:
            st.markdown(f"<div style='display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-bottom: 1px solid #EAE6E3;'><div style='display: flex; align-items: center;'><div style='width: 30px; height: 30px; background-color: #F0EBE6; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; margin-right: 15px; color: #555;'>{course['rank']}</div><div><span style='font-size: 1.1rem; font-weight: 800; color: #222;'>{course['name']}</span><br><span style='font-size: 0.9rem; color: #777;'>{course['dept']}</span></div></div><div><span style='background-color: {course['color']}20; color: {course['color']}; padding: 5px 12px; border-radius: 20px; font-weight: 800; font-size: 0.9rem;'>⏳ {course['quota']}</span></div></div>", unsafe_allow_html=True)

elif st.session_state.current_page == "視覺化介面":
    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px;'>📊 視覺化分析中心</h2>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:10px;'>🔍 全站課程搜尋</div>", unsafe_allow_html=True)
        search_term = st.text_input("搜尋關鍵字", key="search_term", placeholder="請輸入課程名稱或選課代號 (輸入後將優先顯示搜尋結果)...", label_visibility="collapsed")
        
        st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:10px; margin-top:15px;'>📂 條件篩選面板</div>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 3, 1])

        if search_term:
            with c1: st.selectbox("1. 系所：", ["(搜尋模式)"], disabled=True)
            with c2: st.selectbox("2. 開課班級：", ["(搜尋模式)"], disabled=True)
            with c3: st.selectbox("3. 學期：", ["(搜尋模式)"], disabled=True)
            
            filtered_by_search = data[data["課程名稱"].str.contains(search_term, na=False, case=False) | data["選課代號"].astype(str).str.contains(search_term, na=False, case=False)]
            with c4:
                if not filtered_by_search.empty:
                    course_options = ["請選擇..."] + filtered_by_search["課程名稱"].tolist()
                    chart_state = st.session_state.get("scatter_chart")
                    if chart_state and len(chart_state.get("selection", {}).get("points", [])) > 0:
                        clicked_course_id = chart_state["selection"]["points"][0]["customdata"][0]
                        clicked_course = chart_state["selection"]["points"][0]["customdata"][1]
                        st.session_state.saved_course = clicked_course
                        st.session_state.target_course_id = clicked_course_id
                    
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
            with c1:
                dept_options = ["請選擇..."] + sorted(data[data["系所"] != "未知系所"]["系所"].unique().tolist())
                d_idx = dept_options.index(st.session_state.saved_dept) if st.session_state.saved_dept in dept_options else 0
                dept = st.selectbox("1. 系所：", dept_options, index=d_idx)
                st.session_state.saved_dept = dept

            with c2:
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

            with c3:
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

            with c4:
                if not filtered_by_semester.empty or (dept != "請選擇..." and '通識' in dept and class_sel != "請選擇..."):
                    course_options = ["請選擇..."] + filtered_by_semester["課程名稱"].tolist()
                    chart_state = st.session_state.get("scatter_chart")
                    
                    if chart_state and len(chart_state.get("selection", {}).get("points", [])) > 0:
                        clicked_course_id = chart_state["selection"]["points"][0]["customdata"][0]
                        clicked_course = chart_state["selection"]["points"][0]["customdata"][1]
                        st.session_state.saved_course = clicked_course
                        st.session_state.target_course_id = clicked_course_id
                    
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

        with c5:
            def reset_all():
                st.session_state.saved_dept = "請選擇..."
                st.session_state.saved_class = "請選擇..."
                st.session_state.saved_semester = "請選擇..."
                st.session_state.saved_course = "請選擇..."
                st.session_state.target_course_id = None
                st.session_state.search_term = ""
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) 
            st.button("🔄 重置", on_click=reset_all, use_container_width=True)

    with st.container(border=True):
        if not has_valid_filter:
            st.info("👈 請輸入關鍵字搜尋，或從上方依序完成選擇，系統才會載入分析資料。")
            fig_scatter = go.Figure().update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=20, r=20, t=20, b=20), xaxis=dict(showticklabels=False), yaxis=dict(showticklabels=False))
            st.plotly_chart(fig_scatter, use_container_width=True, key="empty_chart")
        else:
            fig_scatter = px.scatter(filtered, x="難度", y="滿意度", hover_name="課程名稱", hover_data={"難度": True, "滿意度": True, "選課代號": True, "學分數": True}, custom_data=["選課代號", "課程名稱"])
            selected_idx = np.where(filtered["課程名稱"] == selected_course)[0].tolist() if selected_course not in ["請選擇...", "先選學期...", "查無結果..."] else None
            fig_scatter.update_traces(selectedpoints=selected_idx, marker=dict(color='#D9534F', size=13, opacity=0.8, line=dict(width=1, color='white')))
            fig_scatter.update_layout(xaxis_title="課程難易度", yaxis_title="滿意度", xaxis=dict(range=[0.5, 5.5], gridcolor='#EFEFEF', fixedrange=True), yaxis=dict(range=[0.5, 5.5], gridcolor='#EFEFEF', fixedrange=True), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=20, r=20, t=20, b=20), clickmode='event+select', dragmode=False)
            st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points", config={'displayModeBar': False}, key="scatter_chart")

    target_course_name = selected_course if selected_course not in ["請選擇...", "先選學期...", "查無結果..."] else None

    with st.container(border=True):
        col_left, col_right = st.columns([1.2, 1])
        with col_left:
            if target_course_name:
                course_info = data[data["課程名稱"] == target_course_name].iloc[0]
                sat_text = "高滿意" if course_info['滿意度'] >= 4 else ("中滿意" if course_info['滿意度'] >= 3 else "低滿意")
                diff_text = "高難度" if course_info['難度'] >= 4 else ("中難度" if course_info['難度'] >= 2.5 else "低難度")
                
                c_title, c_btn = st.columns([3, 1.5])
                with c_title:
                    st.markdown(f"<div style='background-color: #DCD7D4; padding: 5px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; color: #333; display: inline-block; margin-bottom: 10px;'>{target_course_name}</div>", unsafe_allow_html=True)
                with c_btn:
                    st.button("查看詳細資訊 ➔", key="btn_to_detail", use_container_width=True, on_click=navigate_to, args=("詳細課程", course_info['選課代號'], target_course_name))

                st.markdown(f"""
                    <div style="background-color: #EFECE9; border-radius: 15px; padding: 15px; margin-bottom: 15px;">
                        <p style="margin: 0; font-size: 16px; color: #555;">📌 選課代號：{course_info['選課代號']} | 🎓 學分數：{course_info.get('學分', course_info.get('學分數', 2))} | 📅 {course_info['學期']}</p>
                        <p style="margin: 5px 0 0 0; color: #333; font-size: 18px; font-weight: bold;">授課教師：依校方系统公告</p>
                    </div>
                    <div style="background-color: #EFECE9; border-radius: 15px; padding: 15px;">
                        <p style="margin: 5px 0; font-size: 16px; color: #333;">🔥 綜合滿意度： <strong>{course_info['滿意度']}/5</strong></p>
                        <p style="margin: 5px 0; font-size: 16px; color: #333;">💦 課程難易度： <strong>{course_info['難度']}/5</strong></p>
                        <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">(位於：{sat_text}/{diff_text}區)</p>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                c_action1, c_action2 = st.columns(2)
                with c_action1:
                    if st.button("❤️ 加入收藏", key="vis_add_fav", use_container_width=True):
                        c_code = str(course_info['選課代號'])
                        if any(c['id'] == c_code for c in st.session_state.my_courses): 
                            st.toast(f"「{target_course_name}」已經在您的收藏清單中囉！", icon="⚠️")
                        else:
                            c_type_raw = str(course_info.get('必選修', '選修')).upper()
                            c_type = '必修' if c_type_raw == 'M' else '選修' if c_type_raw == 'O' else str(course_info.get('修別', '選修'))
                            try: credits = int(float(course_info.get('學分', course_info.get('學分數', 2))))
                            except: credits = 2
                            raw_time = str(course_info.get('上課時間', course_info.get('節次', ''))).replace(" ", "")
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
                            st.toast(f"已將「{target_course_name}」加入您的收藏清單！", icon="✨")
                with c_action2:
                    st.button("➕ 模擬排課", key="vis_sim_nav", use_container_width=True, on_click=navigate_to, args=("我的收藏",))

            else:
                st.markdown("""
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div style="background-color: #E8E2DE; padding: 5px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; color: #999;">等待選擇課程...</div>
                    </div>
                    <div style="background-color: #F5F5F5; border-radius: 15px; padding: 15px; margin-bottom: 15px;"><p style="margin: 0; font-size: 16px; color: #aaa;">📌 選課代號：--- | 🎓 學分數：--- | 📅 ---</p><p style="margin: 5px 0 0 0; color: #aaa; font-size: 18px; font-weight: bold;">授課教師：---</p></div>
                    <div style="background-color: #F5F5F5; border-radius: 15px; padding: 15px;"><p style="margin: 5px 0; font-size: 16px; color: #aaa;">🔥 綜合滿意度： <strong>- / 5</strong></p><p style="margin: 5px 0; font-size: 16px; color: #aaa;">💦 課程難易度： <strong>- / 5</strong></p><p style="margin: 5px 0 0 0; font-size: 14px; color: #aaa;">(位於：---)</p></div>
                """, unsafe_allow_html=True)

        with col_right:
            values_closed = radar_data.get(course_info['選課代號'] if target_course_name else None, [0, 0, 0, 0, 0]) + radar_data.get(course_info['選課代號'] if target_course_name else None, [0, 0, 0, 0, 0])[:1] if target_course_name else [0, 0, 0, 0, 0, 0]
            fill_color = 'rgba(135, 206, 250, 0.6)' if target_course_name else 'rgba(200, 200, 200, 0.2)'
            line_color = '#5BC0DE' if target_course_name else '#cccccc'
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=values_closed, theta=categories + [categories[0]], fill='toself', fillcolor=fill_color, line=dict(color=line_color), marker=dict(size=1)))
            fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0, 5], showticklabels=False), angularaxis=dict(tickfont=dict(size=12, color='#555' if target_course_name else '#aaa'))), showlegend=False, height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=30, r=30, t=20, b=20))
            st.plotly_chart(fig_radar, use_container_width=True)

elif st.session_state.current_page == "詳細課程":
    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 5px;'>📖 課程詳細資訊</h2>", unsafe_allow_html=True)
    
    col_back, _ = st.columns([1.5, 5])
    with col_back:
        st.button("🔙 返回前一頁", use_container_width=True, on_click=navigate_to, args=("視覺化介面",))

    target_id = st.session_state.get('target_course_id')
    target_name = st.session_state.get('saved_course', "請選擇...")
    matches = []
    
    if target_id and not df_courses.empty:
        matches = df_courses[df_courses['選課代號'].astype(str) == str(target_id)]['UID'].tolist()
        
    if not matches and target_name not in ["請選擇...", "先選學期...", "查無結果..."] and not df_courses.empty:
        matches = df_courses[df_courses['課程名稱'].astype(str).str.contains(target_name, na=False, regex=False)]['UID'].tolist()
    
    if not matches:
        if target_name not in ["請選擇...", "先選學期...", "查無結果..."]:
            st.info(f"💡 這是範例展示課程。請返回「視覺化介面」篩選真實課程以檢視完整數據與圖表！")
        else:
            st.warning("⚠️ 請先至「系統首頁」或「視覺化介面」選擇一門課程後，再查看詳細資訊。")
    else:
        selected_uid = matches[0]
        course_data = df_courses[df_courses['UID'] == selected_uid].iloc[0]
        current_code = str(course_data['選課代號'] if '選課代號' in course_data else "Unknown")
        
        if current_code not in st.session_state.comments_db: st.session_state.comments_db[current_code] = []
        current_comments = st.session_state.comments_db[current_code]

        with st.container(border=True):
            st.markdown(f"### 📌 課程完整資訊")
            st.markdown(f"<div style='background-color: #E2DCD5; padding: 6px 16px; border-radius: 8px; display: inline-block; margin-bottom: 18px; font-weight: bold; color: #222; border: 1px solid #D0C8C0;'>{selected_uid}</div>", unsafe_allow_html=True)
            exclude_cols = ['UID', '學期']
            col1, col2 = st.columns(2)
            display_index = 0
            for col_name in course_data.index:
                if col_name in exclude_cols: continue
                val = course_data[col_name]
                if col_name == '必選修':
                    val = '必修' if str(val).upper() == 'M' else '選修' if str(val).upper() == 'O' else val
                if isinstance(val, str) and len(val) > 25:
                    st.markdown(f"<div style='margin-bottom: 14px; background-color: #F8F6F1; padding: 16px; border-radius: 12px; border: 1px solid #E2DCD5;'><span style='font-weight: 800; color: #444; font-size: 1.05rem;'>📑 {col_name}：</span><br><span style='color: #222; font-weight: 600; font-size: 1rem; line-height: 1.6; display: inline-block; margin-top: 8px;'>{val}</span></div>", unsafe_allow_html=True)
                else:
                    content = f"<div style='margin-bottom: 12px;'><span style='font-weight: 600; color: #555;'>{col_name}：</span> <span style='color: #111; font-weight: 900; font-size: 1.05rem;'>{val}</span></div>"
                    if display_index % 2 == 0:
                        with col1: st.markdown(content, unsafe_allow_html=True)
                    else:
                        with col2: st.markdown(content, unsafe_allow_html=True)
                    display_index += 1

        with st.container(border=True):
            st.markdown("### 📈 歷年修課趨勢")
            trend_df = get_fixed_trend_data(current_code)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.AvgScore, name='平均成績 (分)', line=dict(color='#C85A5A', width=4), yaxis='y1')) 
            fig.add_trace(go.Scatter(x=trend_df.Year, y=trend_df.Students, name='修課人數 (人)', line=dict(color='#4A7C59', width=4), yaxis='y2')) 
            fig.update_layout(margin=dict(l=50, r=50, t=40, b=40), height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color="#000000", family="sans-serif", size=13), legend=dict(orientation="h", y=1.15, font=dict(color="#000000", size=14)), xaxis=dict(tickfont=dict(color="#000000", size=13), gridcolor='#DCD5CE', linecolor='#A09890', linewidth=1), yaxis=dict(title=dict(text="平均成績 (分)", font=dict(color="#000000", size=14)), range=[0, 100], dtick=10, tickfont=dict(color="#000000", size=13), gridcolor='#DCD5CE', linecolor='#A09890', linewidth=1), yaxis2=dict(title=dict(text="修課人數 (人)", font=dict(color="#000000", size=14)), range=[0, 150], dtick=30, tickfont=dict(color="#000000", size=13), overlaying='y', side='right', showgrid=False, linecolor='#A09890', linewidth=1), hoverlabel=dict(bgcolor="#FFFFFF", font=dict(color="#000000", size=13), bordercolor="#D4CCC5"))
            st.plotly_chart(fig, use_container_width=True, theme=None)

        with st.container(border=True):
            st.markdown("### 💬 留言板")
            if not current_comments: st.info("目前還沒有留言，來搶頭香吧！")
            else:
                for comment in current_comments: st.markdown(f'''<div style="background-color: #F8F6F1; padding: 16px; border-radius: 12px; margin-bottom: 14px; border: 1px solid #E2DCD5;"><span style="font-weight: 900; color: #222; font-size: 1.1rem;">👤 {comment['user']}</span><br><span style="color: #444; display: inline-block; margin-top: 8px; line-height: 1.6; font-size: 1.05rem;">{comment['content']}</span></div>''', unsafe_allow_html=True)
            with st.form(key='comment_form', clear_on_submit=True):
                new_comment = st.text_area("分享你的修課心得...", height=80)
                if st.form_submit_button("🚀 發送留言") and new_comment:
                    st.session_state.comments_db[current_code].append({"user": st.session_state.get("name", "目前使用者"), "content": new_comment})
                    st.success("留言已送出！"); st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: 
            if st.button("❤️ 加入收藏", use_container_width=True):
                c_name = str(course_data.get('課程名稱', target_name))
                if any(c['id'] == current_code for c in st.session_state.my_courses): st.toast(f"「{c_name}」已經在您的收藏清單中囉！", icon="⚠️")
                else:
                    c_type_raw = str(course_data.get('必選修', '選修')).upper()
                    c_type = '必修' if c_type_raw == 'M' else '選修' if c_type_raw == 'O' else str(course_data.get('修別', '選修'))
                    try: credits = int(float(course_data.get('學分', course_data.get('學分數', 2))))
                    except: credits = 2
                    raw_time = str(course_data.get('上課時間', course_data.get('節次', ''))).replace(" ", "")
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
                    st.session_state.my_courses.append({"id": current_code, "name": c_name, "time": time_slots, "credits": credits, "type": c_type, "enrolled": False})
                    st.toast(f"已將「{c_name}」加入您的收藏清單！", icon="✨")
        with c2: 
            st.button("➕ 前往模擬排課", use_container_width=True, on_click=navigate_to, args=("我的收藏",))
        with c3: 
            st.link_button("🔗 學校選課系統", url="https://course.fcu.edu.tw/", use_container_width=True)

elif st.session_state.current_page == "我的收藏":
    st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px;'>❤️ 我的收藏與模擬排課</h2>", unsafe_allow_html=True)
    all_favorites = st.session_state.my_courses
    enrolled_courses = [c for c in all_favorites if c["enrolled"]]

    if len(all_favorites) == 0:
        with st.container(border=True): st.markdown("<h3 style='text-align: center; color: #999; margin: 40px 0;'>📭 收藏清單空空如也</h3>", unsafe_allow_html=True)
    else:
        days, periods = ["一", "二", "三", "四", "五", "六", "日"], ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "A", "B", "C", "D"] 
        schedule_matrix = {d: {p: [] for p in periods} for d in days}
        conflicts, total_credits, credits_breakdown = [], 0, {"必修": 0, "選修": 0, "通識": 0}

        for course in enrolled_courses:
            total_credits += course["credits"]
            c_type = course["type"] if course["type"] in credits_breakdown else "選修"
            credits_breakdown[c_type] += course["credits"]
            for t in course["time"]:
                if len(t) >= 2:
                    day, p = t[0], str(int(t[1:])) if t[1:].isdigit() else t[1:]
                    if day in schedule_matrix and p in schedule_matrix[day]: schedule_matrix[day][p].append(course)

        with st.container(border=True):
            col_t1, col_t2 = st.columns([4, 1])
            col_t1.markdown(f"#### 📝 候選清單 <small style='color:#888;'>(已收藏 {len(all_favorites)} 門 / 已加選 {len(enrolled_courses)} 門)</small>", unsafe_allow_html=True)
            if col_t2.button("🗑️ 全部清空", use_container_width=True): st.session_state.my_courses = []; st.rerun()
            st.write("") 

            with st.container(height=450, border=False):
                for idx, course in enumerate(all_favorites):
                    is_enrolled = course["enrolled"]
                    if course["time"]:
                        d_map = defaultdict(list)
                        for t in course["time"]: d_map[t[0]].append(t[1:])
                        pretty = []
                        for d, pl in d_map.items():
                            sort_p = sorted(pl, key=lambda x: int(x) if x.isdigit() else ord(x)+100)
                            is_cont = len(sort_p)>1 and all(x.isdigit() for x in sort_p) and list(range(int(sort_p[0]), int(sort_p[-1])+1)) == [int(x) for x in sort_p]
                            if is_cont: pretty.append(f"({d}){int(sort_p[0]):02d}-{int(sort_p[-1]):02d}")
                            else: pretty.append(f"({d}){','.join([f'{int(x):02d}' if x.isdigit() else x for x in sort_p])}")
                        time_str = " ".join(pretty)
                    else: time_str = "未定"

                    is_conf = any(len(schedule_matrix[t[0]][str(int(t[1:])) if t[1:].isdigit() else t[1:]]) > 1 for t in course["time"]) if is_enrolled else False
                    status_txt = "⛔ 衝堂" if is_conf else ("✅ 已加" if is_enrolled else "⚪ 候選")
                    bg, brd = ("#FFFFFF", "2px solid #DCD7D4") if is_enrolled else ("#F8F6F4", "2px dashed #EAE6E3")

                    c_inf, c_sta, c_btn, c_del = st.columns([4.2, 1.2, 1.2, 0.6])
                    c_inf.markdown(f"""<div style="background-color: {bg}; border: {brd}; padding: 8px 15px; border-radius: 12px; height: 45px; display: flex; align-items: center; overflow: hidden;"><span style="font-weight: 800; color: #333; font-size: 14px; white-space: nowrap;">{course['name']}</span><span style='font-size: 12px; color: #666; background-color: #EAE6E3; padding: 2px 8px; border-radius: 10px; margin-left: 10px; white-space: nowrap;'>🕒 {time_str}</span></div>""", unsafe_allow_html=True)
                    c_sta.markdown(f'<div style="height: 45px; display: flex; align-items: center; justify-content: center; background-color: {bg}; border: {brd}; border-radius: 12px; font-weight: bold; font-size: 13px;">{status_txt}</div>', unsafe_allow_html=True)
                    if is_enrolled:
                        if c_btn.button("➖ 退選", key=f"d_{idx}", use_container_width=True): st.session_state.my_courses[idx]["enrolled"] = False; st.rerun()
                    else:
                        if c_btn.button("➕ 加選", key=f"a_{idx}", use_container_width=True): st.session_state.my_courses[idx]["enrolled"] = True; st.rerun()
                    if c_del.button("🗑️", key=f"x_{idx}", use_container_width=True): st.session_state.my_courses.pop(idx); st.rerun()

        col_main, col_side = st.columns([2.8, 1])
        with col_main:
            with st.container(border=True):
                st.markdown("<h4 style='text-align: center; margin-bottom: 15px;'>📅 預覽課表</h4>", unsafe_allow_html=True)
                active_p = [p for p in periods if any(len(schedule_matrix[d][p]) > 0 for d in days) or p in ["1", "2", "3", "4", "5", "6", "7", "8"]]
                disp_d = days if any(len(schedule_matrix[d][p]) > 0 for d in ["六", "日"] for p in active_p) else ["一", "二", "三", "四", "五"]
                table_html = f"<table class='timetable'><tr><th>節次</th>" + "".join([f"<th>{d}</th>" for d in disp_d]) + "</tr>"
                for p in active_p:
                    table_html += f"<tr><th>{p}</th>"
                    for d in disp_d:
                        cells = schedule_matrix[d][p]
                        if not cells: table_html += "<td></td>"
                        elif len(cells) == 1: table_html += f"<td class='filled'>{cells[0]['name']}</td>"
                        else:
                            names_html = "<br>".join([c['name'][:8] + ".." if len(c['name'])>8 else c['name'] for c in cells])
                            table_html += f"<td class='conflict'>{names_html}</td>"
                            msg = f"週{d} 第{p}節：{' & '.join([c['name'] for c in cells])}"
                            if msg not in conflicts: conflicts.append(msg)
                    table_html += "</tr>"
                st.markdown(table_html + "</table>", unsafe_allow_html=True)

        with col_side:
            with st.container(border=True):
                if conflicts:
                    st.markdown("<h4 style='color: #E74C3C; text-align: center;'>⚠️ 衝突警告</h4>", unsafe_allow_html=True)
                    for msg in conflicts: st.markdown(f"<div style='color: #C0392B; font-size: 12px; background-color: #FADBD8; padding: 8px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #E74C3C;'>{msg}</div>", unsafe_allow_html=True)
                else: st.markdown("<h4 style='color: #27AE60; text-align: center;'>✅ 狀態良好</h4><p style='text-align: center; color: #888; font-size: 13px;'>目前課表無重疊</p>", unsafe_allow_html=True)
            with st.container(border=True):
                st.markdown("<h4 style='text-align: center; margin-bottom: 15px;'>🎯 學分統計</h4>", unsafe_allow_html=True)
                c_color = "#E74C3C" if total_credits > 25 else "#333"
                st.markdown(f"""<div class="stats-card"><div style="text-align: center; margin-bottom: 10px;"><span style="font-size: 24px; font-weight: 900; color: {c_color};">{total_credits}</span><span style="color: #888;"> / 25 學分</span></div><div style="font-size: 14px; border-top: 1px solid #DDD; padding-top: 10px;"><p style="display: flex; justify-content: space-between;"><span>📌 必修</span><b>{credits_breakdown['必修']}</b></p><p style="display: flex; justify-content: space-between;"><span>✨ 選修</span><b>{credits_breakdown['選修']}</b></p><p style="display: flex; justify-content: space-between;"><span>🌍 通識</span><b>{credits_breakdown['通識']}</b></p></div></div>""", unsafe_allow_html=True)

elif st.session_state.current_page == "個人設定":
    st.markdown("<h2 style='margin-bottom: 20px; color: #333; font-weight: 800;'>👤 個人設定與偏好</h2>", unsafe_allow_html=True)

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
            # 🎯 頭像顯示與完美隱藏的上傳框
            st.image(st.session_state.avatar, width=120)
            if st.button("📸 更換頭像", use_container_width=True):
                st.session_state.show_uploader = not st.session_state.show_uploader
                st.rerun()
                
            if st.session_state.show_uploader:
                uploaded_file = st.file_uploader("上傳新頭像", type=["jpg", "png", "jpeg"], label_visibility="collapsed")
                if uploaded_file is not None:
                    st.session_state.avatar = uploaded_file.getvalue()
                    st.session_state.show_uploader = False  # 🎯 上傳成功後自動隱藏框框
                    st.rerun()

        with col2:
            if st.session_state.editing:
                with st.form("edit_profile"):
                    name_input = st.text_input("姓名", value=st.session_state.name)
                    id_input = st.text_input("學號", value=st.session_state.student_id)
                    dept_input = st.text_input("系級", value=st.session_state.department)
                    year_input = st.text_input("年級", value=st.session_state.year)
                    col_form1, col_form2 = st.columns(2)
                    with col_form1: submitted = st.form_submit_button("💾 儲存")
                    with col_form2: cancel = st.form_submit_button("❌ 取消")
                    if submitted:
                        st.session_state.name, st.session_state.student_id, st.session_state.department, st.session_state.year, st.session_state.editing = name_input, id_input, dept_input, year_input, False
                        st.rerun()
                    if cancel:
                        st.session_state.editing = False
                        st.rerun()
            else:
                st.markdown(f"#### {st.session_state.name}")
                st.write(f"**📌 學號：** {st.session_state.student_id}")
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
                # 🎯 從記憶體中讀取狀態，確保切換頁面不重置
                st.session_state.prefs["prof"][field] = st.checkbox(field, value=st.session_state.prefs["prof"][field])
                
        with col_interest_right:
            st.markdown("##### 跨域/通識偏好 (向度分類)")
            for field in st.session_state.prefs["cross"].keys(): 
                # 🎯 從記憶體中讀取狀態
                st.session_state.prefs["cross"][field] = st.checkbox(field, value=st.session_state.prefs["cross"][field])

    with st.container(border=True):
        st.markdown("### ⚙️ 課程偏好設定")
        col_pref1, col_pref2 = st.columns(2)
        with col_pref1:
            st.write("**偏好的作業負擔程度：**")
            workload_options = ["輕鬆 😌", "適中 😊", "充實 💪", "極具挑戰 🔥"]
            idx = workload_options.index(st.session_state.prefs["workload"])
            # 🎯 從記憶體中讀取 Radio 按鈕狀態
            st.session_state.prefs["workload"] = st.radio("選擇作業負擔程度", workload_options, index=idx, label_visibility="collapsed", horizontal=True)
            st.caption(f"目前狀態：{st.session_state.prefs['workload']}")
            
        with col_pref2:
            st.write("**課程類型偏好：**")
            course_types = ["理論課", "實驗課", "線上課程", "混合制"]
            cols_type = st.columns(4)
            for i, course in enumerate(course_types):
                with cols_type[i]: 
                    # 🎯 從記憶體中讀取狀態
                    st.session_state.prefs["course"][course] = st.checkbox(course, value=st.session_state.prefs["course"][course])

    st.write("") 
    col_save1, col_save2, col_save3 = st.columns([1, 1, 2])
    with col_save1:
        if st.button("💾 儲存所有設定", use_container_width=True): st.success("✅ 設定已存檔！")
    with col_save2:
        if st.button("🔄 重置偏好", on_click=reset_all_prefs, use_container_width=True): st.warning("⚠️ 已重置為預設興趣與課程偏好")