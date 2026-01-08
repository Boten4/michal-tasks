import streamlit as st
import time

# הגדרת הדף
st.set_page_config(page_title="משימות למיכל", page_icon="✅")

# --- חלק העיצוב (CSS) המתוקן והחזק יותר ---
st.markdown("""
<style>
    /* כיוון כללי של הדף */
    .stApp {
        direction: rtl;
        text-align: right;
    }
    
    /* יישור טקסטים וכותרות לימין */
    h1, h2, h3, p, div, label {
        text-align: right !important;
    }
    
    /* הפיכת כיוון הצ'ק-בוקס: הריבוע יהיה מימין לטקסט */
    .stCheckbox {
        direction: rtl;
        flex-direction: row-reverse;
        justify-content: right;
    }
    
    /* יישור הטקסט בתוך התיבה */
    .stCheckbox p {
        text-align: right;
        margin-right: 10px; /* רווח קטן בין הריבוע לטקסט */
    }
    
    /* יישור תיבת ההקלדה */
    .stTextInput input {
        direction: rtl;
        text-align: right;
    }
    
    /* הסתרת התפריט של סטרימליט למראה נקי יותר */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- לוגיקה (המוח) ---

if 'tasks' not in st.session_state:
    st.session_state.tasks = []

def add_task():
    task = st.session_state.new_task
    if task:
        st.session_state.tasks.append({"name": task, "done": False})
        st.session_state.new_task = "" 

def update_task_state(index):
    """פונקציה שמעדכנת את הרשימה לפי המצב של הצ'ק-בוקס"""
    # אנחנו בודקים מה מצב הצ'קבוקס כרגע ומעדכנים את הרשימה בהתאם
    key = f"task_{index}"
    is_checked = st.session_state[key]
    st.session_state.tasks[index]['done'] = is_checked
    
    # אם זה סומן כרגע כ"בוצע" - תעיף בלונים
    if is_checked:
        st.balloons()
        st.toast('אלופה! כל הכבוד! 🎉')

# --- הממשק ---

st.title("משימות למיכל 💪")
st.write("יאללה, מפרקים את היום הזה!")

st.text_input("הוסיפי משימה חדשה:", key="new_task", on_change=add_task)

if st.session_state.tasks:
    st.write("---")
    
    # חישוב התקדמות
    total = len(st.session_state.tasks)
    # ספירה מחדש מוודאת שהמספרים תמיד נכונים
    completed = sum(t['done'] for t in st.session_state.tasks)
    
    if total > 0:
        bar_val = completed / total
    else:
        bar_val = 0
    
    st.progress(bar_val)
    st.caption(f"הושלמו {completed} מתוך {total} משימות")

    # הצגת הרשימה
    for i, task in enumerate(st.session_state.tasks):
        task_name = task['name']
        
        # אם בוצע - מוסיפים קו חוצה
        if task['done']:
            label = f"~~{task_name}~~"
        else:
            label = task_name
            
        # הצ'ק בוקס המחובר ישירות לפונקציית העדכון
        st.checkbox(
            label,
            value=task['done'],
            key=f"task_{i}",
            on_change=update_task_state,
            args=(i,)
        )
            
    if completed == total and total > 0:
        time.sleep(0.5) # המתנה קטנה כדי שהבלונים לא יופיעו לפני שהטקסט מתעדכן
        st.success("אין עוד משימות! את חופשייה! 😎")

else:
    st.info("הלוח ריק. זה הזמן להוסיף משימה ראשונה.")