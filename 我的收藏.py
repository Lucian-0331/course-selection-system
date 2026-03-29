import streamlit as st
import pandas as pd
from collections import defaultdict

# ==========================
# 1. 核心 CSS 魔法 (修復對齊與間距)
# ==========================
st.markdown("""
<style>
    /* 基礎卡片樣式 */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: white; border-radius: 20px; border: none;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.05); padding: 20px; margin-bottom: 15px;
    }
    h1, h2, h3, h4 { color: #333333 !important; font-weight: 800 !important; }
    p, span, label { color: #444444 !important; }
    
    /* 課表樣式 */
    .timetable { width: 100%; border-collapse: collapse; text-align: center; font-family: sans-serif; font-size: 14px; }
    .timetable th, .timetable td { border: 2px solid #EAE6E3; padding: 12px 5px; width: 16%; }
    .timetable th { background-color: #F8F6F4; font-weight: 800; color: #555; border-radius: 5px; }
    .timetable td { color: #888; }
    .timetable td.filled { background-color: #DCD7D4; font-weight: 900; color: #222; border-radius: 8px; }
    .timetable td.conflict { background-color: #FADBD8; color: #C0392B; font-weight: 900; border: 2px solid #E74C3C; border-radius: 8px; }
    
    /* 🎯 解決對齊問題：讓右側統計框的間距與左側完全一致 */
    .stats-card {
        background-color: #F8F6F4; 
        padding: 15px; 
        border-radius: 15px;
        border: 1px solid #EAE6E3;
        margin-bottom: 10px;
    }
    
    /* 讓按鈕高度統一 */
    .stButton > button { height: 45px !important; border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# ==========================
# 2. 記憶體資料處理
# ==========================
if 'my_courses' not in st.session_state:
    st.session_state.my_courses = []

for c in st.session_state.my_courses:
    if "enrolled" not in c: c["enrolled"] = False

all_favorites = st.session_state.my_courses
enrolled_courses = [c for c in all_favorites if c["enrolled"]]

# ==========================
# 3. 標題與標題列
# ==========================
st.markdown("<h2 style='color: #333; font-weight: 800; margin-bottom: 20px;'>❤️ 我的收藏與模擬排課</h2>", unsafe_allow_html=True)

if len(all_favorites) == 0:
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center; color: #999; margin: 40px 0;'>📭 收藏清單空空如也</h3>", unsafe_allow_html=True)
else:
    # 核心計算邏輯 (略，與之前相同但保持嚴謹)
    days = ["一", "二", "三", "四", "五", "六", "日"]
    periods = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "A", "B", "C", "D"] 
    schedule_matrix = {d: {p: [] for p in periods} for d in days}
    conflicts, total_credits = [], 0
    credits_breakdown = {"必修": 0, "選修": 0, "通識": 0}

    for course in enrolled_courses:
        total_credits += course["credits"]
        c_type = course["type"] if course["type"] in credits_breakdown else "選修"
        credits_breakdown[c_type] += course["credits"]
        for t in course["time"]:
            if len(t) >= 2:
                day, p = t[0], str(int(t[1:])) if t[1:].isdigit() else t[1:]
                if day in schedule_matrix and p in schedule_matrix[day]: schedule_matrix[day][p].append(course)

    # ==========================
    # 🎯 解決要求 1：【官方原生滾動容器】
    # ==========================
    with st.container(border=True):
        col_t1, col_t2 = st.columns([4, 1])
        col_t1.markdown(f"#### 📝 候選清單 <small style='color:#888;'>(已收藏 {len(all_favorites)} 門 / 已加選 {len(enrolled_courses)} 門)</small>", unsafe_allow_html=True)
        if col_t2.button("🗑️ 全部清空", use_container_width=True):
            st.session_state.my_courses = []
            st.rerun()
            
        st.write("") # 留點間距

        # 🚀 這裡就是魔法：設定固定高度，Streamlit 會自動幫你加滾輪，且絕對有效！
        with st.container(height=450, border=False):
            for idx, course in enumerate(all_favorites):
                is_enrolled = course["enrolled"]
                
                # 時間格式美化器
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

                # 衝突檢查
                is_conf = any(len(schedule_matrix[t[0]][str(int(t[1:])) if t[1:].isdigit() else t[1:]]) > 1 for t in course["time"]) if is_enrolled else False
                status_txt = "⛔ 衝堂" if is_conf else ("✅ 已加" if is_enrolled else "⚪ 候選")
                bg, brd = ("#FFFFFF", "2px solid #DCD7D4") if is_enrolled else ("#F8F6F4", "2px dashed #EAE6E3")

                # 渲染列表行
                c_inf, c_sta, c_btn, c_del = st.columns([4.2, 1.2, 1.2, 0.6])
                c_inf.markdown(f"""
                <div style="background-color: {bg}; border: {brd}; padding: 8px 15px; border-radius: 12px; height: 45px; display: flex; align-items: center; overflow: hidden;">
                    <span style="font-weight: 800; color: #333; font-size: 14px; white-space: nowrap;">{course['name']}</span> 
                    <span style='font-size: 12px; color: #666; background-color: #EAE6E3; padding: 2px 8px; border-radius: 10px; margin-left: 10px; white-space: nowrap;'>🕒 {time_str}</span>
                </div>
                """, unsafe_allow_html=True)
                c_sta.markdown(f'<div style="height: 45px; display: flex; align-items: center; justify-content: center; background-color: {bg}; border: {brd}; border-radius: 12px; font-weight: bold; font-size: 13px;">{status_txt}</div>', unsafe_allow_html=True)
                
                if is_enrolled:
                    if c_btn.button("➖ 退選", key=f"d_{idx}", use_container_width=True):
                        st.session_state.my_courses[idx]["enrolled"] = False; st.rerun()
                else:
                    if c_btn.button("➕ 加選", key=f"a_{idx}", use_container_width=True):
                        st.session_state.my_courses[idx]["enrolled"] = True; st.rerun()
                
                if c_del.button("🗑️", key=f"x_{idx}", use_container_width=True):
                    st.session_state.my_courses.pop(idx); st.rerun()

    # ==========================
    # 🎯 解決要求 2：【完美對齊佈局】
    # ==========================
    col_main, col_side = st.columns([2.2, 1])

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
                    elif len(cells) == 1: table_html += f"<td class='filled' style='font-size: 12px;'>{cells[0]['name'][:6]}</td>"
                    else:
                        table_html += f"<td class='conflict' style='font-size: 11px;'>衝堂</td>"
                        msg = f"週{d} 第{p}節：{' & '.join([c['name'] for c in cells])}"
                        if msg not in conflicts: conflicts.append(msg)
                table_html += "</tr>"
            st.markdown(table_html + "</table>", unsafe_allow_html=True)

    with col_side:
        # 衝突警報框
        with st.container(border=True):
            if conflicts:
                st.markdown("<h4 style='color: #E74C3C; text-align: center;'>⚠️ 衝突警告</h4>", unsafe_allow_html=True)
                for msg in conflicts: 
                    st.markdown(f"<div style='color: #C0392B; font-size: 12px; background-color: #FADBD8; padding: 8px; border-radius: 8px; margin-bottom: 5px; border: 1px solid #E74C3C;'>{msg}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<h4 style='color: #27AE60; text-align: center;'>✅ 狀態良好</h4>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #888; font-size: 13px;'>目前課表無重疊</p>", unsafe_allow_html=True)
        
        # 🎯 統計資訊框 (加上自訂 class 確保與左側高度感覺對齊)
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center; margin-bottom: 15px;'>🎯 學分統計</h4>", unsafe_allow_html=True)
            c_color = "#E74C3C" if total_credits > 25 else "#333"
            st.markdown(f"""
            <div class="stats-card">
                <div style="text-align: center; margin-bottom: 10px;">
                    <span style="font-size: 24px; font-weight: 900; color: {c_color};">{total_credits}</span>
                    <span style="color: #888;"> / 25 學分</span>
                </div>
                <div style="font-size: 14px; border-top: 1px solid #DDD; padding-top: 10px;">
                    <p style="display: flex; justify-content: space-between;"><span>📌 必修</span><b>{credits_breakdown['必修']}</b></p>
                    <p style="display: flex; justify-content: space-between;"><span>✨ 選修</span><b>{credits_breakdown['選修']}</b></p>
                    <p style="display: flex; justify-content: space-between;"><span>🌍 通識</span><b>{credits_breakdown['通識']}</b></p>
                </div>
            </div>
            """, unsafe_allow_html=True)