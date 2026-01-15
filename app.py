import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import time
from datetime import datetime, date # <--- הוספנו ספרייה לעבודה עם תאריכים

# הגדרות דף ועיצוב
st.set_page_config(page_title="משימות למיכל", page_icon="✅")

st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    h1, h2, h3, p, div, label, input { text-align: right !important; }
    .stCheckbox { direction: rtl; flex-direction: row-reverse; justify-content: right; }
    .stCheckbox p { text-align: right; margin-right: 10px; }
    .stButton button { float: right; }
</style>
""", unsafe_allow_html=True)

# --- חיבור לגוגל שיטס ---
def get_worksheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client.open("michal_db").sheet1

# --- פונקציות לניהול משימות ---

def add_new_task():
    """הוספת משימה חדשה לגיליון"""
    new_task_text = st.session_state.new_task_input
    if new_task_text:
        try:
            sh = get_worksheet()
            # הוספת שורה: [משימה, לא בוצע, תאריך ריק]
            # אנחנו מוסיפים תא ריק בסוף כדי לשמור על סדר העמודות
            sh.append_row([new_task_text, "FALSE", ""])
            st.session_state.new_task_input = "" 
            st.toast("המשימה נוספה ללוח! 📝")
        except Exception as e:
            st.error(f"אופס, היתה בעיה בחיבור: {e}")

def update_status(row_index, current_status):
    """עדכון סטטוס משימה + תאריך ביצוע"""
    try:
        sh = get_worksheet()
        cell_row = row_index + 2
        
        # אם המשימה לא הייתה מבוצעת ועכשיו סיימנו אותה
        if not current_status:
            new_status = "TRUE"
            today_date = str(date.today()) # התאריך של היום (למשל 2024-05-20)
            
            # עדכון עמודה B (סטטוס) ל-TRUE
            sh.update_cell(cell_row, 2, new_status)
            # עדכון עמודה C (תאריך) לתאריך של היום
            sh.update_cell(cell_row, 3, today_date)
            
            st.balloons()
            st.toast("אלופה! המשימה בוצעה 🎉")
            time.sleep(2)

        # אם המשימה הייתה מבוצעת וביטלנו אותה (החזרנו ללא בוצע)
        else:
            new_status = "FALSE"
            # עדכון עמודה B ל-FALSE
            sh.update_cell(cell_row, 2, new_status)
            # מחיקת התאריך מעמודה C (כי היא כבר לא בוצעה)
            sh.update_cell(cell_row, 3, "")
            
    except Exception as e:
        st.error(f"שגיאה בעדכון: {e}")

# --- הממשק הראשי ---

st.title("משימות למיכל 💪")

st.text_input("הוסיפי משימה חדשה:", key="new_task_input", on_change=add_new_task)
st.write("---")

try:
    sh = get_worksheet()
    all_records = sh.get_all_records()
    
    if not all_records:
        st.info("הלוח ריק כרגע. תוסיפי משהו!")
    
    else:
        # רשימה שתחזיק רק את המשימות שצריך להציג
        visible_tasks = []
        
        # --- שלב הסינון: בודקים אילו משימות להציג ---
        for i, record in enumerate(all_records):
            is_done = str(record['is_done']).upper() == 'TRUE'
            completed_date_str = str(record.get('CompletedDate', '')) # שליפת התאריך
            
            show_task = True # ברירת מחדל: מציגים את המשימה
            
            # אם המשימה בוצעה, נבדוק מתי
            if is_done and completed_date_str:
                try:
                    # המרת הטקסט לתאריך אמיתי
                    comp_date = datetime.strptime(completed_date_str, "%Y-%m-%d").date()
                    # חישוב כמה ימים עברו
                    days_passed = (date.today() - comp_date).days
                    
                    if days_passed > 7:
                        show_task = False # עבר יותר משבוע - לא מציגים!
                except:
                    # אם היה בלאגן בתאריך, נציג ליתר ביטחון
                    pass
            
            if show_task:
                # שומרים את האינדקס המקורי (i) כדי שנוכל למחוק את השורה הנכונה בגיליון
                visible_tasks.append((i, record))

        # --- חישוב התקדמות (רק למשימות שמוצגות) ---
        total_visible = len(visible_tasks)
        completed_visible = sum(1 for i, r in visible_tasks if str(r['is_done']).upper() == 'TRUE')
        
        if total_visible > 0:
            st.progress(completed_visible / total_visible)
            st.caption(f"הושלמו {completed_visible} מתוך {total_visible} משימות השבוע")

        # --- הצגת המשימות ---
        # אנחנו רצים על הרשימה המסוננת שלנו
        for original_index, record in visible_tasks:
            task_name = record['task']
            is_done = str(record['is_done']).upper() == 'TRUE'
            
            display_text = f"~~{task_name}~~" if is_done else task_name
            
            col1, col2 = st.columns([0.95, 0.05])
            with col1:
                # המפתח (key) חייב להיות ייחודי, נשתמש באינדקס המקורי
                if st.checkbox(display_text, value=is_done, key=f"task_{original_index}"):
                    if not is_done: 
                        update_status(original_index, is_done)
                        st.rerun()
                else:
                    if is_done:
                        update_status(original_index, is_done)
                        st.rerun()

except Exception as e:
    st.warning("האפליקציה מחכה לחיבור ראשוני...")
    # st.error(e)
