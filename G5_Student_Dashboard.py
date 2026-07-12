import streamlit as st
from st_supabase_connection import SupabaseConnection
import datetime

st.set_page_config(
    page_title="Grade 5 Weekly Study Dashboard", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Initialize Secure Supabase Connection
try:
    conn = st.connection("supabase", type=SupabaseConnection)
except Exception as conn_error:
    st.error("🔒 Connection Error: Could not connect to the database securely.")
    st.info("💡 **Tatay's Admin Tip:** Double-check that your `supabase_url` and `supabase_key` are pasted correctly into the Streamlit Cloud Secrets settings panel.")
    st.stop()

st.title("🎓 Grade 5 Daily Learning Dashboard")
st.write("Review your focus areas for today, then complete the quick retrieval quiz to lock in what you learned.")
st.markdown("---")

# 2. Automatically Calculate Current Week's Package Date (Sunday Anchor)
today = datetime.date.today()
# weekday() returns 0 for Monday, 6 for Sunday
# This math anchors our lookup to the most recent Sunday
sunday_offset = (today.weekday() + 1) % 7
current_sunday = today - datetime.timedelta(days=sunday_offset)

# 3. Fetch the Weekly Master Package Data from Supabase
try:
    package_query = conn.table("weekly_packages")\
        .select("package_data")\
        .eq("week_starting_date", str(current_sunday))\
        .execute()
except Exception as db_error:
    st.error("⚠️ Database Error: Failed to fetch study records.")
    st.code(str(db_error))
    st.stop()

# 4. Handle Empty Package States Safely
if not package_query.data:
    st.info(f"✨ Great job checking in! Your study package for the week of **{current_sunday.strftime('%B %d, %Y')}** is currently being prepared. Enjoy your break time!")
    st.stop()

weekly_data = package_query.data[0]['package_data']

# 5. Map Weekdays to Block Schedule Categories
weekday_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday"}
current_weekday_idx = today.weekday()

st.sidebar.header("🕹️ Control Panel")

# Auto-route based on the day of the week, or let them switch if it's the weekend
if current_weekday_idx in weekday_map:
    target_day = weekday_map[current_weekday_idx]
    st.sidebar.success(f"📆 Today is {target_day}")
else:
    st.sidebar.info("🏡 Weekend / General Review Mode")
    target_day = st.sidebar.selectbox("Choose Day to Review", list(weekday_map.values()))

# 6. Isolate the Active Day's Target Subjects
day_data = weekly_data.get(target_day, {})

if not day_data:
    st.warning(f"No subject data scheduled for {target_day} in this week's payload.")
    st.stop()

selected_subject = st.sidebar.selectbox("Choose a Subject", list(day_data.keys()))

# 7. Render Lesson Summary & Dynamic Form Quiz Interface
if selected_subject:
    subject_data = day_data[selected_subject]
    
    # Dual-column responsive layout splits learning materials from testing items
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader(f"📖 {selected_subject} Core Points")
        # Clean up any potential double-escaped linebreaks coming from automated models
        clean_markdown = subject_data['summary_markdown'].replace(r'\n', '\n')
        st.markdown(clean_markdown)
        
    with col2:
        st.subheader("🧠 Quick Check-In Quiz")
        quiz_data = subject_data.get('quiz', [])
        
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
            # Wrap standard inputs inside an isolated form component to prevent frame recalculation cycles
            with st.form(key=f"quiz_form_{target_day}_{selected_subject}"):
                user_answers = {}
                
                for i, q in enumerate(quiz_data):
                    st.write(f"**Q{i+1}: {q['question']}**")
                    user_answers[i] = st.radio(
                        "Select the best option:", 
                        options=q['options'], 
                        key=f"q_{target_day}_{selected_subject}_{i}", 
                        index=None
                    )
                    st.write("---")
                    
                submit_button = st.form_submit_button(label="Submit Answers")
                
                if submit_button:
                    # Evaluate Answers
                    score = 0
                    total = len(quiz_data)
                    unanswered = any(ans is None for ans in user_answers.values())
                    
                    if unanswered:
                        st.warning("⚠️ Please answer all the questions before clicking submit.")
                    else:
                        for i, q in enumerate(quiz_data):
                            if user_answers[i] == q['correct_answer']:
                                score += 1
                        
                        # Provide Immediate Performance Feedback loops
                        if score == total:
                            st.balloons()
                            st.success(f"🎉 Perfect Score! {score}/{total}. Outstanding retention!")
                        elif score >= (total / 2):
                            st.success(f"👍 Good effort! You scored {score}/{total}. Go over what you missed with Tatay.")
                        else:
                            st.warning(f"📚 You scored {score}/{total}. Let's read over today's core summary points on the left one more time together.")
