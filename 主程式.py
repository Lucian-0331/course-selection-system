import streamlit as st

# ==========================
# 1. 系統全域設定 (必須是整個系統的第一行)
# ==========================
st.set_page_config(page_title="智慧選課系統", page_icon="🎓", layout="wide")

# ==========================
# 2. 全域 CSS 魔法 (解決反白、按鈕太小、選單消失的三大 Bug)
# ==========================
st.markdown("""
<style>
    /* 🎯 [修復 Bug 1] 強制鎖死全域背景與側邊欄顏色，避免切換頁面時反白 */
    .stApp { background-color: #EAE6E3 !important; }
    [data-testid="stSidebar"] { background-color: #DCD7D4 !important; }

    /* 🎯 [修復 Bug 3] 讓頂部標題列透明，但「保留」左上角的展開按鈕！ */
    /* 千萬別用 visibility: hidden，否則選單收合後那個 > 按鈕會不見！ */
    header { background-color: transparent !important; }

    /* 🎯 [修復 Bug 2] 將原本死板的導覽列，爆改為「高質感大型膠囊按鈕」 */
    /* 1. 隱藏預設的標題線 */
    [data-testid="stSidebarNavSeparator"] { display: none !important; }
    
    /* 2. 設定每一個導覽按鈕的樣式 (完全對齊你的設計圖) */
    [data-testid="stSidebarNav"] a {
        background-color: #EFEBE8 !important; /* 燕麥奶底色 */
        border-radius: 25px !important;       /* 大圓角膠囊形狀 */
        margin: 15px 20px !important;         /* 增加按鈕間距與左右留白 */
        padding: 15px 20px !important;        /* 💥 把按鈕撐大！ */
        font-size: 18px !important;           /* 💥 字體放大 */
        font-weight: 800 !important;          /* 字體加粗 */
        color: #555555 !important;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05) !important;
        transition: all 0.3s ease !important;
        display: flex !important;
        align-items: center !important;
        gap: 15px !important;                 /* 圖示跟文字拉開一點 */
    }
    
    /* 3. 滑鼠懸停時的特效 */
    [data-testid="stSidebarNav"] a:hover {
        background-color: #A3968C !important;
        color: white !important;
        transform: translateY(-2px);
        box-shadow: 0px 6px 15px rgba(0,0,0,0.1) !important;
    }
    
    /* 4. 目前所在頁面的「啟用中 (Active)」按鈕樣式 */
    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #333333 !important; /* 深灰色高對比 */
        box-shadow: 0px 4px 15px rgba(0,0,0,0.2) !important;
    }
    /* 🎯 精準打擊：強迫裡面的圖示跟文字都變成白色！ */
    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: white !important;
    }
    
    /* 5. 把原本預設醜醜的 focus 外框拿掉 */
    [data-testid="stSidebarNav"] a:focus {
        outline: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================
# 3. 註冊你的所有功能頁面
# ==========================
page_analysis = st.Page("視覺化.py", title="圖表分析", icon="📊")
page_details  = st.Page("詳細資訊.py", title="課程詳細資訊", icon="📖") 
page_favorite = st.Page("我的收藏.py", title="我的收藏", icon="❤️")
page_settings = st.Page("個人資訊.py", title="個人設定", icon="⚙️")

# ==========================
# 4. 建立左側導覽選單
# ==========================
pg = st.navigation(
    {
        "系統功能": [page_analysis, page_details, page_favorite, page_settings]
    }
)

# ==========================
# 5. 啟動路由
# ==========================
pg.run()