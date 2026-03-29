import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import random
import re

# 1. 頁面設定
#st.set_page_config(page_title="課程詳細資訊", layout="centered")

# 2. CSS 魔法與防自動翻譯防護罩
st.markdown("""
<meta name="google" content="notranslate">
<style>
    .stApp { background-color: #E6E1DC; }
    header { background-color: transparent !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 20px;
        border: 1px solid #D4CCC5;
        box-shadow: 0px 8px 24px rgba(160, 150, 140, 0.25);
        padding: 24px;
        margin-bottom: 24px;
    }
    h1, h2, h3 { color: #222222 !important; font-weight: 800 !important; }
    p, span, label { color: #444444 !important; }
    h1 { font-size: 2.2rem !important; margin-bottom: 1.5rem !important; }
    .stTextInput input, .stTextArea textarea, .stSelectbox > div > div { 
        background-color: #FDFDFD !important; 
        color: #222222 !important; 
        border-radius: 12px !important;
        border: 1px solid #C4BCB5 !important; 
    }
    ul[role="listbox"] li { color: #222222 !important; }
    .stButton>button, .stFormSubmitButton>button { 
        width: 100%; 
        border-radius: 20px; 
        font-weight: 800;
        background-color: #F0EBE6 !important;
        border: 1px solid #D4CCC5 !important;
        color: #222222 !important;
        letter-spacing: 1px;
        transition: all 0.3s ease; 
        box-shadow: 0 4px 10px rgba(0,0,0,0.06);
    }
    .stButton>button:hover, .stFormSubmitButton>button:hover { 
        background-color: #E2D7CE !important;
        border-color: #C2B5A8 !important;
        color: #000000 !important;
        box-shadow: 0 6px 15px rgba(180, 170, 160, 0.4);
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

# 3. 讀取並清洗資料
@st.cache_data
def load_and_clean_data():
    try:
        try:
            df = pd.read_excel("data.xlsx", sheet_name="1131-114開課")
        except:
            df = pd.read_csv("data.xlsx - 1131-114開課.csv")
            
        df.columns = df.columns.astype(str).str.strip()
        
        # 移除不需要的欄位 (新增：EMI註記、配當年、進度內容)
        cols_to_drop = ['sub_id', 'scr_dup', '配當系所', '課程編碼', '工具分類', 'seq_no', '周次', 'EMI註記', '配當年', '進度內容']
        df = df.drop(columns=[c for c in cols_to_drop if c in df.columns])
        
        # 重新命名欄位
        rename_dict = {
            'yms_year': '年次',
            'yms_smester': '學期',
            'cls_id': '課程代碼',
            '開課班級簡稱': '開課班級',
            '科目簡稱': '課程名稱',
            '配當系所.1': '配當系所'
        }
        df = df.rename(columns=rename_dict)
        
        # 學期轉換 (1 -> 上學期, 2 -> 下學期)
        if '學期' in df.columns:
            df['學期'] = df['學期'].astype(str).replace({'1': '上學期', '2': '下學期', '1.0': '上學期', '2.0': '下學期'})
        
        name_col = '課程名稱' if '課程名稱' in df.columns else df.columns[7]
        code_col = '選課代號' if '選課代號' in df.columns else df.columns[5]
        
        # 確保不會刪到不同學期的同代號課程
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
        st.error(f"資料讀取錯誤: {e}")
        return pd.DataFrame()

# 🔑 趨勢圖資料快取
@st.cache_data
def get_fixed_trend_data(course_code):
    random.seed(course_code)
    return pd.DataFrame({
        "Year": ['109', '110', '111', '112', '113'],
        "Students": [random.randint(40, 120) for _ in range(5)],
        "AvgScore": [random.randint(65, 95) for _ in range(5)]
    })

df_courses = load_and_clean_data()

# 4. 初始化留言板
if 'comments_db' not in st.session_state:
    st.session_state.comments_db = {}

# --- 介面開始 ---
st.title("📚 課程決策系統")

if not df_courses.empty:
    course_uids = df_courses['UID'].tolist()
    selected_uid = st.selectbox("選擇課程", course_uids, label_visibility="collapsed")
    
    course_data = df_courses[df_courses['UID'] == selected_uid].iloc[0]
    current_code = str(course_data['選課代號'] if '選課代號' in course_data else "Unknown")
    
    if current_code not in st.session_state.comments_db:
        st.session_state.comments_db[current_code] = []
    current_comments = st.session_state.comments_db[current_code]

    # ==========================================
    # [1] 基本資訊卡片
    # ==========================================
    with st.container(border=True):
        st.markdown(f"### 📌 課程完整資訊")
        st.markdown(f"<div style='background-color: #E2DCD5; padding: 6px 16px; border-radius: 8px; display: inline-block; margin-bottom: 18px; font-weight: bold; color: #222; border: 1px solid #D0C8C0;'>{selected_uid}</div>", unsafe_allow_html=True)
        
        # 排除顯示 UID 與 學期
        exclude_cols = ['UID', '學期']
        col1, col2 = st.columns(2)
        display_index = 0
        
        for col_name in course_data.index:
            if col_name in exclude_cols:
                continue
                
            val = course_data[col_name]
            
            if col_name == '必選修':
                if str(val).upper() == 'M': val = '必修'
                elif str(val).upper() == 'O': val = '選修'
                
            if isinstance(val, str) and len(val) > 25:
                st.markdown(f"<div style='margin-bottom: 14px; background-color: #F8F6F1; padding: 16px; border-radius: 12px; border: 1px solid #E2DCD5;'><span style='font-weight: 800; color: #444; font-size: 1.05rem;'>📑 {col_name}：</span><br><span style='color: #222; font-weight: 600; font-size: 1rem; line-height: 1.6; display: inline-block; margin-top: 8px;'>{val}</span></div>", unsafe_allow_html=True)
            else:
                content = f"<div style='margin-bottom: 12px;'><span style='font-weight: 600; color: #555;'>{col_name}：</span> <span style='color: #111; font-weight: 900; font-size: 1.05rem;'>{val}</span></div>"
                if display_index % 2 == 0:
                    with col1: st.markdown(content, unsafe_allow_html=True)
                else:
                    with col2: st.markdown(content, unsafe_allow_html=True)
                display_index += 1

    # ==========================================
    # [2] 趨勢圖卡片
    # ==========================================
    with st.container(border=True):
        st.markdown("### 📈 歷年修課趨勢")
        trend_df = get_fixed_trend_data(current_code)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_df.Year, y=trend_df.AvgScore, 
            name='平均成績 (分)', 
            line=dict(color='#C85A5A', width=4),
            yaxis='y1'
        )) 
        
        fig.add_trace(go.Scatter(
            x=trend_df.Year, y=trend_df.Students, 
            name='修課人數 (人)', 
            line=dict(color='#4A7C59', width=4),
            yaxis='y2'
        )) 
        
        fig.update_layout(
            margin=dict(l=50, r=50, t=40, b=40), 
            height=300, 
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#000000", family="sans-serif", size=13),
            legend=dict(orientation="h", y=1.15, font=dict(color="#000000", size=14)),
            
            xaxis=dict(
                tickfont=dict(color="#000000", size=13), 
                gridcolor='#DCD5CE', 
                linecolor='#A09890', 
                linewidth=1
            ),
            
            yaxis=dict(
                title=dict(text="平均成績 (分)", font=dict(color="#000000", size=14)),
                range=[0, 100], 
                dtick=10,
                tickfont=dict(color="#000000", size=13), 
                gridcolor='#DCD5CE', 
                linecolor='#A09890', 
                linewidth=1
            ),
            
            yaxis2=dict(
                title=dict(text="修課人數 (人)", font=dict(color="#000000", size=14)),
                range=[0, 150], 
                dtick=30,
                tickfont=dict(color="#000000", size=13),
                overlaying='y',
                side='right',
                showgrid=False,
                linecolor='#A09890',
                linewidth=1
            ),
            
            hoverlabel=dict(
                bgcolor="#FFFFFF",
                font=dict(color="#000000", size=13),
                bordercolor="#D4CCC5"
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, theme=None)

    # ==========================================
    # [3] 留言板卡片
    # ==========================================
    with st.container(border=True):
        st.markdown("### 💬 留言板")
        if not current_comments:
            st.info("目前還沒有留言，來搶頭香吧！")
        else:
            for comment in current_comments:
                st.markdown(f'''
                <div style="background-color: #F8F6F1; padding: 16px; border-radius: 12px; margin-bottom: 14px; border: 1px solid #E2DCD5;">
                    <span style="font-weight: 900; color: #222; font-size: 1.1rem;">👤 {comment['user']}</span> 
                    <br><span style="color: #444; display: inline-block; margin-top: 8px; line-height: 1.6; font-size: 1.05rem;">{comment['content']}</span>
                </div>
                ''', unsafe_allow_html=True)

        with st.form(key='comment_form', clear_on_submit=True):
            new_comment = st.text_area("分享你的修課心得...", height=80)
            submit_btn = st.form_submit_button("🚀 發送留言")
            if submit_btn and new_comment:
                st.session_state.comments_db[current_code].append({"user": "目前使用者", "content": new_comment})
                st.success("留言已送出！")
                st.rerun()

    # ==========================================
    # [4] 底部動作按鈕 (完美串接「我的收藏」排課系統)
    # ==========================================
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)

    with c1: 
        if st.button("❤️ 加入收藏", use_container_width=True):
            if 'my_courses' not in st.session_state:
                st.session_state.my_courses = []
                
            already_added = any(c['id'] == current_code for c in st.session_state.my_courses)
            
            # 安全抓取課程名稱 (你原本的欄位名稱處理)
            c_name = str(course_data.get('課程名稱', course_data.get('科目簡稱', selected_uid)))
            
            if already_added:
                st.toast(f"「{c_name}」已經在您的收藏清單中囉！", icon="⚠️")
            else:
                # 安全抓取必選修狀態
                c_type_raw = str(course_data.get('必選修', '選修')).upper()
                if c_type_raw == 'M': c_type = '必修'
                elif c_type_raw == 'O': c_type = '選修'
                else: c_type = str(course_data.get('修別', '選修'))
                
                # 安全抓取學分數
                try:
                    credits = int(float(course_data.get('學分', course_data.get('學分數', 2))))
                except:
                    credits = 2
                
                # 自動解析真實上課時間格式 (完美相容你原本資料庫的時間)
                # 修改後：
                # 自動解析真實上課時間格式 (完美相容你原本資料庫的時間)
                # ⚠️ 記得把 '上課時間' 換成你 Excel 裡真實的欄位名稱喔！
               # 自動解析真實上課時間格式：完美破解「(一)06-08」區間格式！
                # ⚠️ 記得把 '上課時間' 換成你 Excel 裡真實的欄位名稱喔！
                raw_time = str(course_data.get('上課時間', course_data.get('節次', ''))) 
                
                import re
                time_slots = []
                
                # 去除空白，避免干擾
                raw_time = raw_time.replace(" ", "")
                
                # 抓取「星期幾」配上「後面的時間字串」
                # 例如 "(一)06-08" 會被抓成 day='一', periods='06-08'
                matches = re.finditer(r'\(?([一二三四五六日])\)?([0-9A-Za-z,\-~]+)', raw_time)
                
                for match in matches:
                    day = match.group(1)
                    periods_str = match.group(2)
                    
                    # 用逗號或頓號切開 (對付 "02,03" 這種格式)
                    parts = re.split(r'[,、]', periods_str)
                    
                    for part in parts:
                        if '-' in part or '~' in part:
                            # 🎯 核心魔法：對付 "06-08" 這種連續區間，自動把它展開！
                            sep = '-' if '-' in part else '~'
                            try:
                                start_str, end_str = part.split(sep)
                                if start_str.isdigit() and end_str.isdigit():
                                    for p in range(int(start_str), int(end_str) + 1):
                                        time_slots.append(f"{day}{p}")
                                else:
                                    time_slots.append(f"{day}{start_str.upper()}")
                                    time_slots.append(f"{day}{end_str.upper()}")
                            except ValueError:
                                pass # 防呆：萬一格式長得很奇怪就跳過
                        else:
                            # 處理單一數字或字母 (例如 "06" 變成 "6", "A" 變成 "A")
                            if part.isdigit():
                                time_slots.append(f"{day}{int(part)}")
                            elif part:
                                time_slots.append(f"{day}{part.upper()}")
                
                new_course = {
                    "id": current_code,
                    "name": c_name,
                    "time": time_slots,
                    "credits": credits,
                    "type": c_type,
                    "enrolled": False  # 預設為只加入清單，等待使用者手動加選排入
                }
                
                st.session_state.my_courses.append(new_course)
                st.toast(f"已將「{c_name}」加入您的收藏清單！", icon="✨")
            
    with c2: 
        if st.button("➕ 前往模擬排課", use_container_width=True):
            st.toast("💡 請從左側導覽列點擊「❤️ 我的收藏」頁面，就可以進行自定義排課囉！", icon="💡")
        
    with c3: 
        st.button("🔗 學校選課系統", use_container_width=True)