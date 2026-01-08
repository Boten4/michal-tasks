import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# הגדרות דף ועיצוב
st.set_page_config(page_title="משימות למיכל", page_icon="✅")

st.markdown("""
<style>
    .stApp { direction: rtl; text-align: right; }
    h1, h2, h3, p, div, label, input { text-align: right !important; }
    .stCheckbox { direction: rtl; flex-direction: row-reverse; justify-content: right; }
    .stCheckbox p { text-align: right; margin-right: 10px; }
    /* כפתור מחיקה קטן אם נרצה בעתיד */
    .stButton button { float: right; }
</style>
""", unsafe_allow_html=True)

# --- חיבור לגוגל שיטס ---
# הפונקציה הזו מתחברת לגיליון באמצעות המפתח שנשים ב"כספת" (Secrets)
def get_worksheet():
    # הגדרת הרשאות
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # טעינת המפתח מתוך הסודות של סטרימליט
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    
    # חיבור ופתיחת הגיליון
    client = gspread.authorize(credentials)
    return client.open("michal_db").sheet1

# --- פונקציות לניהול משימות ---

def add_new_task():
    """הוספת משימה חדשה לגיליון"""
    new_task_text = st.session_state.new_task_input
    if new_task_text:
        try:
            sh = get_worksheet()
            # הוספת שורה חדשה: [משימה, לא בוצע]
            sh.append_row([new_task_text, "FALSE"])
            st.session_state.new_task_input = ""  # ניקוי השדה
            st.toast("המשימה נוספה ללוח! 📝")
        except Exception as e:
            st.error(f"אופס, היתה בעיה בחיבור: {e}")

def update_status(row_index, current_status):
    """עדכון סטטוס משימה בגיליון"""
    try:
        sh = get_worksheet()
        # גוגל שיטס מתחיל משורה 1, והכותרת היא שורה 1.
        # לכן המשימה הראשונה (אינדקס 0) נמצאת בשורה 2.
        cell_row = row_index + 2
        cell_col = 2  # עמודה B היא הסטטוס
        
        new_value = "TRUE" if not current_status else "FALSE"
        sh.update_cell(cell_row, cell_col, new_value)
        
        if new_value == "TRUE":
            st.balloons()
            st.toast("אלופה! מחקתי מהרשימה 🎉")
            
    except Exception as e:
        st.error(f"שגיאה בעדכון: {e}")

# --- הממשק הראשי ---

st.title("משימות למיכל 💪")
st.write("הלוח המשותף שלנו - כל מה שקורה פה, נשמר ב-Google Sheets!")

# תיבת הוספה
st.text_input("הוסיפי משימה חדשה:", key="new_task_input", on_change=add_new_task)

st.write("---")

# טעינת המשימות מהגיליון
try:
    sh = get_worksheet()
    # קריאת כל הנתונים
    all_records = sh.get_all_records()
    
    # אם אין משימות בכלל
    if not all_records:
        st.info("הלוח ריק כרגע. תוסיפי משהו!")
    
    else:
        # חישוב התקדמות
        total = len(all_records)
        # המרה של הטקסט 'TRUE'/'FALSE' לבוליאני אמיתי
        completed = sum(1 for item in all_records if str(item['is_done']).upper() == 'TRUE')
        
        if total > 0:
            st.progress(completed / total)
            st.caption(f"הושלמו {completed} מתוך {total} משימות")

        # הצגת הרשימה
        for i, record in enumerate(all_records):
            task_name = record['task']
            is_done = str(record['is_done']).upper() == 'TRUE'
            
            # עיצוב טקסט (קו חוצה)
            display_text = f"~~{task_name}~~" if is_done else task_name
            
            # יצירת צ'קבוקס
            # שימי לב: אנחנו לא משתמשים ב-session_state רגיל אלא מעדכנים ישירות את הגיליון בלחיצה
            col1, col2 = st.columns([0.95, 0.05])
            with col1:
                if st.checkbox(display_text, value=is_done, key=f"task_{i}"):
                    # אם המצב השתנה לעומת מה שיש בגיליון -> נעדכן
                    if not is_done: 
                        update_status(i, is_done)
                        st.rerun() # רענון הדף כדי לראות את השינוי
                else:
                    # אם המשתמש ביטל את ה-V
                    if is_done:
                        update_status(i, is_done)
                        st.rerun()

except Exception as e:
    # טיפול במצב שהקובץ סודות עדיין לא מוגדר
    st.warning("האפליקציה מחכה למפתח החיבור. (האם הגדרת את Secrets בענן?)")
    # st.error(e) # אפשר להדליק את זה כדי לראות את השגיאה המלאה