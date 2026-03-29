import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import numpy as np

# ==========================
# 1. 讀取並轉換官方資料
# ==========================
@st.cache_data(ttl=3600)
def load_data():
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
    
    df = df.drop_duplicates(subset=['課程名稱', '學期']).reset_index(drop=True)
    
    np.random.seed(42)
    df['滿意度'] = np.random.uniform(2.5, 5.0, size=len(df)).round(1)
    df['難度'] = np.random.uniform(2.0, 5.0, size=len(df)).round(1)
    
    radar_dict = {}
    for _, row in df.iterrows():
        radar_dict[row['課程名稱']] = np.random.uniform(1.5, 5.0, 5).round(1).tolist()
        
    return df, radar_dict

data, radar_data = load_data()
categories = ["作業負擔", "考試難度", "實務性", "理論性", "互動程度"]

# ==========================
# 2. 頂部標題列
# ==========================
st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px;'>📊 視覺化分析中心</h2>", unsafe_allow_html=True)

# ==========================
# 3. 橫向篩選控制面板 (原本在側邊欄的東西，現在移到這裡！)
# ==========================
with st.container(border=True):
    st.markdown("<div style='font-weight:bold; color:#555; margin-bottom:10px;'>🔍 課程篩選面板</div>", unsafe_allow_html=True)
    
    # 🎯 魔法：把版面切成 5 等份的橫向欄位！
    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 3, 1])
    
    if 'dept_choice' not in st.session_state: st.session_state.dept_choice = "請選擇..."
    if 'semester_choice' not in st.session_state: st.session_state.semester_choice = "請選擇..."
    if 'course_selector' not in st.session_state: st.session_state.course_selector = "請選擇..."
    if 'last_chart_click' not in st.session_state: st.session_state.last_chart_click = None

    with c1:
        dept_options = ["請選擇..."] + sorted(data[data["系所"] != "未知系所"]["系所"].unique().tolist())
        dept = st.selectbox("1. 系所：", dept_options, key='dept_choice')

    with c2:
        if dept != "請選擇...":
            filtered_by_dept = data[data["系所"] == dept]
            raw_classes = filtered_by_dept["開課班級"].unique().tolist()
            def class_sort_logic(class_name):
                g_rank = 1 if '一' in class_name else (2 if '二' in class_name else (3 if '三' in class_name else (4 if '四' in class_name else 9)))
                c_rank = 1 if '甲' in class_name else (2 if '乙' in class_name else (3 if '合' in class_name else 9))
                return (g_rank, c_rank, class_name)
            sorted_classes = sorted(raw_classes, key=class_sort_logic)
            class_options = ["請選擇..."] + sorted_classes
            class_sel = st.selectbox("2. 開課班級：", class_options)
        else:
            class_sel = st.selectbox("2. 開課班級：", ["先選系所..."], disabled=True)

    with c3:
        if class_sel != "請選擇..." and class_sel != "先選系所...":
            filtered_by_class = filtered_by_dept[filtered_by_dept["開課班級"] == class_sel]
            is_gen_ed = '通識' in dept
            if is_gen_ed:
                semester_sel = st.selectbox("3. 學期：", ["(無)"], disabled=True)
                filtered_by_semester = filtered_by_class.drop_duplicates(subset=['課程名稱'])
            else:
                raw_semesters = filtered_by_class["學期"].unique().tolist()
                def semester_sort_logic(sem): return 1 if sem == '上學期' else (2 if sem == '下學期' else 3)
                sorted_semesters = sorted(raw_semesters, key=semester_sort_logic)
                semester_options = ["請選擇..."] + sorted_semesters 
                semester_sel = st.selectbox("3. 學期：", semester_options, key="semester_choice")
                if semester_sel != "請選擇...":
                    filtered_by_semester = filtered_by_class[filtered_by_class["學期"] == semester_sel]
                else:
                    filtered_by_semester = pd.DataFrame()
        else:
            semester_sel = st.selectbox("3. 學期：", ["先選班級..."], disabled=True)
            filtered_by_semester = pd.DataFrame()

    with c4:
        if not filtered_by_semester.empty or (dept != "請選擇..." and '通識' in dept and class_sel != "請選擇..."):
            course_options = ["請選擇..."] + filtered_by_semester["課程名稱"].tolist()
            
            chart_state = st.session_state.get("scatter_chart")
            clicked_course = None
            if chart_state and len(chart_state.get("selection", {}).get("points", [])) > 0:
                clicked_course = chart_state["selection"]["points"][0]["customdata"][0]
                
            if clicked_course and clicked_course != st.session_state.last_chart_click:
                st.session_state.course_selector = clicked_course
                st.session_state.last_chart_click = clicked_course
            elif not clicked_course and st.session_state.last_chart_click is not None:
                st.session_state.course_selector = "請選擇..."
                st.session_state.last_chart_click = None
                
            if st.session_state.course_selector not in course_options:
                st.session_state.course_selector = "請選擇..."
                
            selected_course = st.selectbox("4. 課程：", course_options, key="course_selector")
            has_valid_filter = True
            filtered = filtered_by_semester
        else:
            selected_course = st.selectbox("4. 課程：", ["先選學期..."], disabled=True)
            has_valid_filter = False
            filtered = pd.DataFrame()

    with c5:
        def reset_all():
            st.session_state.dept_choice = "請選擇..."
            if 'semester_choice' in st.session_state: st.session_state.semester_choice = "請選擇..."
            st.session_state.course_selector = "請選擇..."
            st.session_state.last_chart_click = None
        
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True) # 把按鈕往下推對齊下拉選單
        st.button("🔄 重置", on_click=reset_all, use_container_width=True)


# ==========================
# 4. 上方區塊：散佈圖
# ==========================
with st.container(border=True):
    if not has_valid_filter:
        st.info("👈 請先從上方依序完成「系所」、「班級」與「學期」選擇，系統才會載入分析資料。")
        fig_scatter = go.Figure()
        fig_scatter.update_layout(
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False), yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        st.plotly_chart(fig_scatter, use_container_width=True, key="empty_chart")
    else:
        fig_scatter = px.scatter(filtered, x="難度", y="滿意度", hover_name="課程名稱", hover_data={"難度": True, "滿意度": True, "選課代號": True, "學分數": True}, custom_data=["課程名稱"])
        selected_idx = np.where(filtered["課程名稱"] == selected_course)[0].tolist() if selected_course not in ["請選擇...", "先選學期..."] else None
        fig_scatter.update_traces(selectedpoints=selected_idx, marker=dict(color='#D9534F', size=13, opacity=0.8, line=dict(width=1, color='white')))
        fig_scatter.update_layout(
            xaxis_title="課程難易度", yaxis_title="滿意度",
            xaxis=dict(range=[0.5, 5.5], gridcolor='#EFEFEF', fixedrange=True), yaxis=dict(range=[0.5, 5.5], gridcolor='#EFEFEF', fixedrange=True),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', height=350, margin=dict(l=20, r=20, t=20, b=20),
            clickmode='event+select', dragmode=False  
        )
        st.plotly_chart(fig_scatter, use_container_width=True, on_select="rerun", selection_mode="points", config={'displayModeBar': False}, key="scatter_chart")

# ==========================
# 5. 下方區塊：詳細資訊與雷達圖
# ==========================
target_course_name = selected_course if selected_course not in ["請選擇...", "先選學期..."] else None

with st.container(border=True):
    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        if target_course_name:
            course_info = data[data["課程名稱"] == target_course_name].iloc[0]
            sat_text = "高滿意" if course_info['滿意度'] >= 4 else ("中滿意" if course_info['滿意度'] >= 3 else "低滿意")
            diff_text = "高難度" if course_info['難度'] >= 4 else ("中難度" if course_info['難度'] >= 2.5 else "低難度")
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="background-color: #DCD7D4; padding: 5px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; color: #333;">{target_course_name}</div>
                    <div style="background-color: #333; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px; cursor: pointer;">詳細資訊 ></div>
                </div>
                <div style="background-color: #EFECE9; border-radius: 15px; padding: 15px; margin-bottom: 15px;">
                    <p style="margin: 0; font-size: 16px; color: #555;">📌 選課代號：{course_info['選課代號']} | 🎓 學分數：{course_info['學分數']} | 📅 {course_info['學期']}</p>
                    <p style="margin: 5px 0 0 0; color: #333; font-size: 18px; font-weight: bold;">授課教師：依校方系統公告</p>
                </div>
                <div style="background-color: #EFECE9; border-radius: 15px; padding: 15px;">
                    <p style="margin: 5px 0; font-size: 16px; color: #333;">🔥 綜合滿意度： <strong>{course_info['滿意度']}/5</strong></p>
                    <p style="margin: 5px 0; font-size: 16px; color: #333;">💦 課程難易度： <strong>{course_info['難度']}/5</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">(位於：{sat_text}/{diff_text}區)</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div style="background-color: #E8E2DE; padding: 5px 20px; border-radius: 20px; font-weight: bold; font-size: 18px; color: #999;">等待選擇課程...</div>
                    <div style="background-color: #ccc; color: white; padding: 5px 15px; border-radius: 20px; font-size: 14px;">詳細資訊 ></div>
                </div>
                <div style="background-color: #F5F5F5; border-radius: 15px; padding: 15px; margin-bottom: 15px;">
                    <p style="margin: 0; font-size: 16px; color: #aaa;">📌 選課代號：--- | 🎓 學分數：--- | 📅 ---</p>
                    <p style="margin: 5px 0 0 0; color: #aaa; font-size: 18px; font-weight: bold;">授課教師：---</p>
                </div>
                <div style="background-color: #F5F5F5; border-radius: 15px; padding: 15px;">
                    <p style="margin: 5px 0; font-size: 16px; color: #aaa;">🔥 綜合滿意度： <strong>- / 5</strong></p>
                    <p style="margin: 5px 0; font-size: 16px; color: #aaa;">💦 課程難易度： <strong>- / 5</strong></p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #aaa;">(位於：---)</p>
                </div>
            """, unsafe_allow_html=True)

    with col_right:
        values_closed = radar_data.get(target_course_name, [0, 0, 0, 0, 0]) + radar_data.get(target_course_name, [0, 0, 0, 0, 0])[:1] if target_course_name else [0, 0, 0, 0, 0, 0]
        fill_color = 'rgba(135, 206, 250, 0.6)' if target_course_name else 'rgba(200, 200, 200, 0.2)'
        line_color = '#5BC0DE' if target_course_name else '#cccccc'
        
        fig_radar = go.Figure()
        fig_radar.add_trace(go.Scatterpolar(r=values_closed, theta=categories + [categories[0]], fill='toself', fillcolor=fill_color, line=dict(color=line_color), marker=dict(size=1)))
        fig_radar.update_layout(polar=dict(radialaxis=dict(range=[0, 5], showticklabels=False), angularaxis=dict(tickfont=dict(size=12, color='#555' if target_course_name else '#aaa'))), showlegend=False, height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=30, r=30, t=20, b=20))
        st.plotly_chart(fig_radar, use_container_width=True)