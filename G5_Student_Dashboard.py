import streamlit as st
from supabase import create_client, Client
import datetime

st.set_page_config(
    page_title="Grade 5 Weekly Study Dashboard", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# 1. Initialize Direct Supabase Connection via Streamlit Secrets
try:
    # Pulling directly from the TOML header block you set up
    url = st.secrets["connections"]["supabase"]["supabase_url"]
    key = st.secrets["connections"]["supabase"]["supabase_key"]
    supabase: Client = create_client(url, key)
except Exception as conn_error:
    st.error("🔒 Secrets Configuration Error: Could not read credentials.")
    st.info("💡 **Tatay's Admin Tip:** Ensure your Streamlit Cloud Secrets text box contains the exact fields required.")
    st.code(str(conn_error))
    st.stop()

st.title("🎓 Grade 5 Daily Learning Dashboard")
st.write("Review your focus areas for today, then complete the quick retrieval quiz to lock in what you learned.")
st.markdown("---")

# 2. Calculate Current Week's Package Date (Sunday Anchor)
today = datetime.date.today()
sunday_offset = (today.weekday() + 1) % 7
current_sunday = today - datetime.timedelta(days=sunday_offset)

# 3. Fetch Data using Direct Client Syntax
try:
    response = supabase.table("weekly_packages")\
        .select("package_data")\
        .eq("week_starting_date", str(current_sunday))\
        .execute()
    package_data_list = response.data
except Exception as db_error:
    st.error("⚠️ Database Error: Failed to fetch study records from the cloud table.")
    st.code(str(db_error))
    st.stop()

# 4. Handle Empty Package States Safely
weekly_data = {}  # Safe default initialization to prevent NameErrors

if not package_data_list:
    st.info(f"✨ Great job checking in! Your study package for the week of **{current_sunday.strftime('%B %d, %Y')}** is currently being prepared. Enjoy your break time!")
    st.warning(f"🔧 Technical Debug: The app is looking for a row in Supabase where week_starting_date = '{str(current_sunday)}'")
    st.stop()
else:
    # Ensure package_data is read safely
    raw_data = package_data_list[0].get('package_data', {})
    
    # If Supabase stores it as a raw string text, parse it; otherwise use it directly
    if isinstance(raw_data, str):
        import json
        try:
            weekly_data = json.loads(raw_data)
        except Exception:
            weekly_data = {}
    else:
        weekly_data = raw_data

# 5. Map Weekdays to Block Schedule Categories
weekday_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday"}
current_weekday_idx = today.weekday()

st.sidebar.header("🕹️ Control Panel")

if current_weekday_idx in weekday_map:
    target_day = weekday_map[current_weekday_idx]
    st.sidebar.success(f"%s Today is {target_day}" % "📆")
else:
    st.sidebar.info("🏡 Weekend / General Review Mode")
    target_day = st.sidebar.selectbox("Choose Day to Review", list(weekday_map.values()))

# 6. Isolate the Active Day's Target Subjects
day_data = weekly_data.get(target_day, {})

if not day_data:
    st.warning(f"No subject data scheduled for {target_day} in this week's payload.")
    st.stop()

selected_subject = st.sidebar.selectbox("Choose a Subject", list(day_data.keys()))

# 7. Render Lesson Summary & Dynamic Quiz Form
if selected_subject:
    subject_data = day_data[selected_subject]
    col1, col2 = st.columns([1, 1], gap="large")
    
    with col1:
        st.subheader(f"📖 {selected_subject} Core Points")
        clean_markdown = subject_data['summary_markdown'].replace(r'\n', '\n')
        st.markdown(clean_markdown)
        
    with col2:
        st.subheader("🧠 Quick Check-In Quiz")
        quiz_data = subject_data.get('quiz', [])
        
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
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
                    score = 0
                    total = len(quiz_data)
                    unanswered = any(ans is None for ans in user_answers.values())
                    
                    if unanswered:
                        st.warning("⚠️ Please answer all the questions before clicking submit.")
                    else:
                        for i, q in enumerate(quiz_data):
                            if user_answers[i] == q['correct_answer']:
                                score += 1
                        
                        if score == total:
                            st.balloons()
                            st.success(f"🎉 Perfect Score! {score}/{total}. Outstanding retention!")
                        elif score >= (total / 2):
                            st.success(f"👍 Good effort! You scored {score}/{total}. Go over what you missed with Tatay.")
                        else:
                            st.warning(f"📚 You scored {score}/{total}. Let's read over today's core summary points on the left one more time together.")
