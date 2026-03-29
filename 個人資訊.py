import streamlit as st
import pandas as pd
import random

def show_profile():
    #st.set_page_config(page_title="個人設定", layout="wide")
    
    # ==================== 1. CSS 視覺統一魔法 ====================
    st.markdown("""
    <style>
        /* 頁面背景色 (奶茶色) */
        .stApp { background-color: #EAE6E3; }
        
        /* 隱藏頂部預設 header */
        header { background-color: transparent !important; }
        
        /* 核心魔法：將 st.container(border=True) 變成高質感白底卡片 */
        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: white;
            border-radius: 20px;
            border: none;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.05);
            padding: 20px;
            margin-bottom: 20px;
        }
        
        /* 標題與內文顏色優化 */
        h1, h2, h3 { color: #333333 !important; font-weight: 800 !important; }
        p, span, label { color: #555555 !important; }
        
        /* 下拉選單與輸入框樣式優化 */
        .stTextInput input, .stTextArea textarea, .stSelectbox > div > div { 
            background-color: #F8F6F4 !important; 
            color: #333333 !important; 
            border-radius: 10px !important;
            border: 1px solid #EAE6E3 !important; 
        }
        
        /* ========================================= */
        /* 按鈕樣式：法式奶油白 / 淺燕麥色 (高對比清晰版) */
        /* ========================================= */
        .stButton>button, .stFormSubmitButton>button { 
            width: 100%; 
            border-radius: 20px; 
            font-weight: 800;                      
            background-color: #EFEBE8 !important;  
            border: 1px solid #DCD5CE !important;  
            color: #333333 !important;             
            letter-spacing: 1px;                   
            transition: all 0.3s ease; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.04);
        }
        .stButton>button:hover, .stFormSubmitButton>button:hover { 
            background-color: #E4DCD3 !important;  
            border-color: #D2C8BE !important;
            color: #111111 !important;             
            box-shadow: 0 4px 12px rgba(180, 170, 160, 0.3); 
            transform: translateY(-2px);
        }
        
        /* 進度條顏色優化 */
        .stProgress > div > div > div > div {
            background-color: #A3968C;
        }
    </style>
    """, unsafe_allow_html=True)

    # ==================== 2. 初始化狀態 ====================
    if "name" not in st.session_state:
        st.session_state.name = "王小明 (Ming Wang)"
        st.session_state.student_id = "B110565033"
        st.session_state.department = "工工系"
        st.session_state.year = "三年級"
    if "editing" not in st.session_state:
        st.session_state.editing = False

    st.markdown("<h2 style='margin-bottom: 20px;'>👤 個人設定與偏好</h2>", unsafe_allow_html=True)

    # ==================== 3. 卡片 1：個人資料與進度 ====================
    with st.container(border=True):
        col_header_left, col_header_right = st.columns([5, 1])
        with col_header_left:
            st.markdown("### 基本資料")
        with col_header_right:
            if st.button("✏️ 編輯", use_container_width=True):
                st.session_state.editing = True
                
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.image("https://www.w3schools.com/howto/img_avatar.png", width=120)
            if st.button("📸 更換頭像", use_container_width=True):
                uploaded_file = st.file_uploader("上傳新頭像", type=["jpg", "png"], label_visibility="collapsed")
                if uploaded_file:
                    st.success(f"👍 頭像已上傳：{uploaded_file.name}")
        
        with col2:
            if st.session_state.editing:
                with st.form("edit_profile"):
                    name_input = st.text_input("姓名", value=st.session_state.name)
                    id_input = st.text_input("學號", value=st.session_state.student_id)
                    dept_input = st.text_input("系級", value=st.session_state.department)
                    year_input = st.text_input("年級", value=st.session_state.year)
                    
                    col_form1, col_form2 = st.columns(2)
                    with col_form1:
                        submitted = st.form_submit_button("💾 儲存")
                    with col_form2:
                        cancel = st.form_submit_button("❌ 取消")
                        
                    if submitted:
                        st.session_state.name = name_input
                        st.session_state.student_id = id_input
                        st.session_state.department = dept_input
                        st.session_state.year = year_input
                        st.session_state.editing = False
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
            st.write("**🎓 畢業門檻進度：**")
            col_grad1, col_grad2 = st.columns(2)
            with col_grad1:
                st.write("**必修 (75%)**")
                st.progress(0.75)
            with col_grad2:
                st.write("**選修 (85%)**")
                st.progress(0.85)

    # 🎯 密碼安全區塊已徹底刪除

    # ==================== 4. 卡片 2：興趣探索 (大學常見標籤版) ====================
    with st.container(border=True):
        st.markdown("### ⭐ 興趣與跨域探索")
        st.caption("下列選項將影響系統為您推薦的智能排課結果")
        
        col_interest_left, col_interest_right = st.columns(2)
        
        with col_interest_left:
            st.markdown("##### 專業領域 (系內課群)")
            # 換成工工/商管/科技 常見課群
            prof_fields = {
                "🏭 生產與製造": False, 
                "📈 品質管理": False, 
                "💻 程式與資訊": False, 
                "📊 數據分析": False, 
                "⚙️ 系統模擬": False, 
                "💼 科技管理": False
            }
            for field, selected in prof_fields.items():
                st.checkbox(field, value=selected, key=f"prof_{field}")
        
        with col_interest_right:
            st.markdown("##### 跨域/通識偏好 (向度分類)")
            # 換成大學通識常見向度
            cross_fields = {
                "🌍 人文與歷史": False, 
                "🎨 藝術與美學": False, 
                "🏛️ 社會與心理": False, 
                "⚖️ 法律與政治": False, 
                "💰 經濟與商管": False, 
                "🌱 自然與環境": False, 
                "🗣️ 外語能力": False
            }
            for field, selected in cross_fields.items():
                st.checkbox(field, value=selected, key=f"cross_{field}")

   # ==================== 6. 卡片 3：課程偏好 ====================
    with st.container(border=True):
        st.markdown("### ⚙️ 課程偏好設定")
        col_pref1, col_pref2 = st.columns(2)
        
        with col_pref1:
            st.write("**偏好的作業負擔程度：**")
            workload_options = ["輕鬆 😌", "適中 😊", "充實 💪", "極具挑戰 🔥"]
            # 🎯 修復 1：加上 key="workload_choice"，讓系統可以精準控制它
            workload = st.radio("選擇作業負擔程度", workload_options, index=1, key="workload_choice", label_visibility="collapsed", horizontal=True)
            st.caption(f"目前狀態：{workload}")
        
        with col_pref2:
            st.write("**課程類型偏好：**")
            course_types = ["理論課", "實驗課", "線上課程", "混合制"]
            cols_type = st.columns(4)
            for i, course in enumerate(course_types):
                with cols_type[i]:
                    st.checkbox(course, value=False, key=f"course_{course}")

    # ==================== 7. 底部動作按鈕 ====================
    st.write("") 
    col_save1, col_save2, col_save3 = st.columns([1, 1, 2])
    
    # 🎯 修復 2：建立專屬的 Callback 函數，在背景強迫把所有按鈕「切回原始狀態」
    def reset_all_prefs():
        for key in list(st.session_state.keys()):
            # 把所有興趣跟課程類型的勾選框，強制改成 False (未勾選)
            if key.startswith("prof_") or key.startswith("cross_") or key.startswith("course_"):
                st.session_state[key] = False
        # 把作業負擔單選框，強制改回預設值
        st.session_state['workload_choice'] = "適中 😊"

    with col_save1:
        if st.button("💾 儲存所有設定", use_container_width=True):
            st.success("✅ 設定已存檔！")
    with col_save2:
        # 🎯 修復 3：改用 on_click 觸發我們剛剛寫的強制清理函數
        if st.button("🔄 重置偏好", on_click=reset_all_prefs, use_container_width=True):
            st.warning("⚠️ 已重置為預設興趣與課程偏好")

# 測試運行
if __name__ == "__main__":
    show_profile()

# ==================== 打開本地網站 ====================
def open_website():
    """
    自動打開瀏覽器訪問本地 Streamlit 應用
    """
    import webbrowser
    import time
    
    url = "http://localhost:8501/"
    time.sleep(3)
    webbrowser.open(url)
    print(f"✅ 已在預設瀏覽器打開: {url}")
    print("💡 如果沒有自動打開，請手動在瀏覽器輸入上述地址")