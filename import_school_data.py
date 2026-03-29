import pandas as pd
import sqlite3
import os

def import_and_clean_data():
    print("=== 🚀 啟動 Excel 專屬匯入程式 ===")
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = '逢甲工工_課程資料範例.xlsx'
    file_path = os.path.join(current_dir, file_name)

    if not os.path.exists(file_path):
        print(f"❌ 找不到檔案：{file_path}")
        return

    # 1. 讀取 Excel 檔案中的特定分頁
    try:
        print("讀取中，請稍候...")
        # 指定讀取名為 '1131-114開課' 的工作表
        df = pd.read_excel(file_path, sheet_name='1131-114開課')
        print("✅ 成功讀取 Excel 檔案！")
    except Exception as e:
        print(f"❌ 讀取失敗！詳細錯誤：{e}")
        return

    # 2. 印出欄位名稱，確認「課號」到底叫什麼
    print(f"\n👉 檔案中包含的欄位有：\n{df.columns.tolist()}\n")

    # ==========================================
    # ⚠️ 這裡非常重要！
    # 請根據上面印出來的清單，把 '選課代號' 換成真實的欄位名稱
    # ==========================================
    course_id_column = '選課代號' 
    
    if course_id_column not in df.columns:
        print(f"❌ 找不到名為「{course_id_column}」的欄位！")
        print("💡 請看上方的『欄位清單』，把程式碼第 31 行的 course_id_column 換成正確的名字再執行一次。")
        return
        
    # 3. 清洗資料：刪除重複的週次，保留乾淨的課程清單
    df_cleaned = df.drop_duplicates(subset=['yms_year', 'yms_smester', '選課代號'])
    
    print(f"📊 原始資料總筆數: {len(df)} 筆")
    print(f"✨ 去除重複後，真實的課程總數: {len(df_cleaned)} 筆")

    # 4. 寫入 SQLite
    db_path = os.path.join(current_dir, 'courses.db')
    with sqlite3.connect(db_path) as conn:
        df_cleaned.to_sql('official_courses', conn, if_exists='replace', index=False)
        
    print("\n✅ 完美！官方課程資料已經成功寫入 courses.db 裡的 official_courses 資料表！")

if __name__ == '__main__':
    import_and_clean_data()