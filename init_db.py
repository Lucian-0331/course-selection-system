import sqlite3
import pandas as pd

def create_database():
    print("開始建立資料庫...")
    
    # 1. 準備原本的模擬資料
    data = pd.DataFrame({
        "課程名稱": ["CS305 App開發", "資料結構", "人工智慧", "經濟學", "統計學"],
        "難度": [3.24, 4.48, 4.76, 3.02, 3.87],
        "滿意度": [4.8, 4.2, 4.6, 4.1, 3.5],
        "學分": [3, 3, 3, 2, 3],
        "教師": ["王小明", "李大華", "陳教授", "林老師", "張教授"],
        "系所": ["資工", "資工", "資工", "商管", "理學"],
        "年級": ["大三", "大二", "大四", "大一", "大二"]
    })

    radar_df = pd.DataFrame({
        "課程名稱": ["CS305 App開發", "資料結構", "人工智慧", "經濟學", "統計學"],
        "作業負擔": [4, 5, 5, 3, 4],
        "考試難度": [3, 5, 5, 2, 4],
        "實務性": [5, 3, 4, 4, 3],
        "理論性": [2, 4, 4, 3, 5],
        "互動程度": [4, 3, 3, 5, 2]
    })

    # 2. 連接並建立 SQLite 資料庫 (檔案會自動產生在同一資料夾)
    with sqlite3.connect('courses.db') as conn:
        # 3. 將 DataFrame 直接寫入資料庫變成資料表 (Table)
        data.to_sql('course_info', conn, if_exists='replace', index=False)
        radar_df.to_sql('course_radar', conn, if_exists='replace', index=False)
        
    print("成功！資料庫 courses.db 與資料表已建立完成。")

if __name__ == '__main__':
    create_database()