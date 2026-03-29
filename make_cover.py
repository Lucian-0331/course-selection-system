import streamlit as st
import pandas as pd

# 1. 頁面設定 (改為寬版佈局，適合儀表板顯示)
st.set_page_config(page_title="選課決策支援系統 - 首頁", layout="wide", initial_sidebar_state="expanded")

# 2. CSS 魔法與防自動翻譯防護罩 (完全保留你的設計)
st.markdown("""
<meta name="google" content="notranslate">
<style>
    /* 整體背景與側邊欄背景 */
    .stApp { background-color: #E6E1DC; }
    [data-testid="stSidebar"] { background-color: #F8F6F1; border-right: 1px solid #D4CCC5; }
    
    /* 隱藏頂部預設 header */
    header { background-color: transparent !important; }
    
    /* 🎯 核心魔法：白底圓角陰影卡片 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 16px;
        border: 1px solid #D4CCC5;
        box-shadow: 0px 6px 16px rgba(160, 150, 140, 0.15);
        padding: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    /* 讓卡片有微微浮起的懸停效果 */
    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-2px);
        box-shadow: 0px 10px 24px rgba(160, 150, 140, 0.25);
    }
    
    /* 字體顏色設定 */
    h1, h2, h3, h4 { color: #222222 !important; font-weight: 800 !important; font-family: 'sans-serif'; }
    p, span, label { color: #444444 !important; font-family: 'sans-serif'; }
    
    /* 側邊欄按鈕設計 */
    [data-testid="stSidebar"] .stButton>button {
        width: 100%;
        text-align: left;
        border: none;
        background-color: transparent !important;
        box-shadow: none;
        color: #333333 !important;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 10px 15px;
        justify-content: flex-start;
    }
    [data-testid="stSidebar"] .stButton>button:hover {
        background-color: #EAE3DC !important;
        border-radius: 10px;
        color: #000000 !important;
    }

    /* 推薦標籤 (Tag) 樣式 */
    .tag {
        display: inline-block;
        background-color: #F0EBE6;
        color: #555555;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 8px;
        margin-top: 8px;
    }
    .tag-match {
        background-color: #4A7C59; /* 森林綠 */
        color: white;
    }
    .tag-hot {
        background-color: #C85A5A; /* 磚紅 */
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🎯 核心資料連動運算 (在這裡悄悄幫你算學分)
# ==========================================
if 'my_courses' not in st.session_state:
    st.session_state.my_courses = []

# 計算「已加選」的真實學分
current_enrolled_credits = sum(c['credits'] for c in st.session_state.my_courses if c.get('enrolled', False))

# 假設歷史累積學分
accumulated_credits = 85 
total_after_this_sem = accumulated_credits + current_enrolled_credits
needed_credits = max(128 - total_after_this_sem, 0)

# ==========================================
# 左側導覽列 (Sidebar) - 原封不動還給你！
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; margin-bottom: 30px;'>🎓 選課決策系統</h2>", unsafe_allow_html=True)
    st.button("🏠 系統首頁", use_container_width=True)
    st.button("🔍 課程探索", use_container_width=True)
    st.button("❤️ 我的收藏", use_container_width=True)
    st.button("📅 模擬課表", use_container_width=True)
    st.button("📈 學習歷程分析", use_container_width=True)
    st.markdown("---")
    st.button("⚙️ 系統設定", use_container_width=True)
    st.button("🚪 登出", use_container_width=True)

# ==========================================
# 主畫面 (Main Content)
# ==========================================
st.title("👋 歡迎回來！")
st.markdown("<p style='font-size: 1.1rem; margin-bottom: 30px;'>在這裡掌握您的學習進度與最新課程動態，為新學期做好完美規劃。</p>", unsafe_allow_html=True)

# ------------------------------------------
# 區塊 1：畢業學分進度 (Metrics) - 🎯 這裡換成連動變數
# ------------------------------------------
st.markdown("### 📊 畢業學分進度")
col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True):
        st.markdown("<h4 style='color: #666;'>本學期預選學分</h4>", unsafe_allow_html=True)
        # 把原本的 18 換成動態變數
        st.markdown(f"<h2 style='font-size: 2.5rem; color: #4A7C59;'>{current_enrolled_credits} <span style='font-size: 1.2rem; color: #888;'>學分</span></h2>", unsafe_allow_html=True)
        st.progress(min(current_enrolled_credits / 25, 1.0)) # 假設上限 25

with col2:
    with st.container(border=True):
        st.markdown("<h4 style='color: #666;'>累積畢業學分</h4>", unsafe_allow_html=True)
        # 把原本的 85 換成動態變數
        st.markdown(f"<h2 style='font-size: 2.5rem; color: #222;'>{total_after_this_sem} <span style='font-size: 1.2rem; color: #888;'>/ 128</span></h2>", unsafe_allow_html=True)
        st.progress(min(total_after_this_sem / 128, 1.0))

with col3:
    with st.container(border=True):
        st.markdown("<h4 style='color: #666;'>距離畢業還需</h4>", unsafe_allow_html=True)
        # 把原本的 43 換成動態變數
        st.markdown(f"<h2 style='font-size: 2.5rem; color: #C85A5A;'>{needed_credits} <span style='font-size: 1.2rem; color: #888;'>學分</span></h2>", unsafe_allow_html=True)
        st.markdown("<span style='color: #888; font-weight: 600;'>💡 建議本學期再修 2-3 門必修課</span>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------
# 區塊 2：個人化推薦 (Personalized Recommendations) - 原封不動
# ------------------------------------------
st.markdown("### 🚀 為您推薦的專屬課程")
rc1, rc2, rc3 = st.columns(3)

with rc1:
    with st.container(border=True):
        st.markdown("#### 人因工程與實驗設計")
        st.markdown("👨‍🏫 王教授 | 🕒 (四) 02-04")
        st.markdown("""
            <span class='tag tag-match'>95% 契合度</span>
            <span class='tag'>專業必修</span>
            <span class='tag'>實作豐富</span>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.button("查看詳情", key="btn1", use_container_width=True)

with rc2:
    with st.container(border=True):
        st.markdown("#### 系統動力學")
        st.markdown("👩‍🏫 李教授 | 🕒 (二) 02-04")
        st.markdown("""
            <span class='tag tag-match'>88% 契合度</span>
            <span class='tag'>專業選修</span>
            <span class='tag'>邏輯訓練</span>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.button("查看詳情", key="btn2", use_container_width=True)

with rc3:
    with st.container(border=True):
        st.markdown("#### 資料庫設計")
        st.markdown("👨‍🏫 張教授 | 🕒 (三) 06-08")
        st.markdown("""
            <span class='tag tag-match'>82% 契合度</span>
            <span class='tag'>專業選修</span>
            <span class='tag'>軟體應用</span>
        """, unsafe_allow_html=True)
        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
        st.button("查看詳情", key="btn3", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ------------------------------------------
# 區塊 3：熱門排行與名額警示 (Popular Courses) - 原封不動
# ------------------------------------------
st.markdown("### 🔥 全校熱門搶手課程")

with st.container(border=True):
    hot_courses = [
        {"rank": 1, "name": "Python 程式設計與資料分析", "dept": "通識中心", "quota": "剩餘 2 名", "color": "#C85A5A"},
        {"rank": 2, "name": "人工智慧概論", "dept": "資訊工程學系", "quota": "剩餘 5 名", "color": "#C85A5A"},
        {"rank": 3, "name": "投資理財實務", "dept": "財務金融學系", "quota": "剩餘 12 名", "color": "#D4A373"},
        {"rank": 4, "name": "心理學導論", "dept": "通識中心", "quota": "剩餘 20 名", "color": "#4A7C59"}
    ]
    
    for course in hot_courses:
        st.markdown(f"""
        <div style='display: flex; justify-content: space-between; align-items: center; padding: 12px 15px; border-bottom: 1px solid #EAE6E3;'>
            <div style='display: flex; align-items: center;'>
                <div style='width: 30px; height: 30px; background-color: #F0EBE6; border-radius: 50%; display: flex; justify-content: center; align-items: center; font-weight: bold; margin-right: 15px; color: #555;'>{course['rank']}</div>
                <div>
                    <span style='font-size: 1.1rem; font-weight: 800; color: #222;'>{course['name']}</span><br>
                    <span style='font-size: 0.9rem; color: #777;'>{course['dept']}</span>
                </div>
            </div>
            <div>
                <span style='background-color: {course['color']}20; color: {course['color']}; padding: 5px 12px; border-radius: 20px; font-weight: 800; font-size: 0.9rem;'>⏳ {course['quota']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='text-align: center; margin-top: 15px;'><a href='#' style='color: #4A7C59; font-weight: bold; text-decoration: none;'>查看完整排行榜 ➔</a></div>", unsafe_allow_html=True)