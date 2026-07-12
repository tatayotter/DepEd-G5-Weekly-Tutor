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

# 7. Render Lesson Summary & Dynamic Quiz Form with Fixed Memory Logic
if selected_subject:
    subject_data = day_data[selected_subject]
    quiz_data = subject_data.get('quiz', [])
    
    # Define distinct, persistent state keys
    quiz_active_key = f"active_{target_day}_{selected_subject}"
    submitted_key = f"submitted_{target_day}_{selected_subject}"
    score_key = f"score_{target_day}_{selected_subject}"
    feedback_key = f"feedback_{target_day}_{selected_subject}"
    saved_answers_key = f"saved_answers_{target_day}_{selected_subject}"
    
    # Initialize keys if missing from session state
    if quiz_active_key not in st.session_state:
        st.session_state[quiz_active_key] = False
    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False
        st.session_state[score_key] = 0
        st.session_state[feedback_key] = []
        st.session_state[saved_answers_key] = {}

    # Sidebar Controller Layout
    st.sidebar.markdown("### 🕹️ Quiz Status")
    
    if st.session_state[submitted_key]:
        st.sidebar.success("✅ Quiz Completed!")
        if st.sidebar.button("🔓 Open Study Notes Again"):
            st.session_state[quiz_active_key] = False
            st.session_state[submitted_key] = False  # Reset for clean slate
            st.rerun()
    elif st.session_state[quiz_active_key]:
        st.sidebar.warning("🔒 Quiz In Progress...")
        st.sidebar.caption("Study notes are locked until submission.")
    else:
        if st.sidebar.button("📝 Hide Notes & Start Quiz"):
            st.session_state[quiz_active_key] = True
            st.rerun()
            
    st.sidebar.markdown("---")

    # SCREEN ROUTING LOGIC (Using strict memory states instead of UI variables)
    
    # LAYOUT A: Reading Mode
    if not st.session_state[quiz_active_key] and not st.session_state[submitted_key]:
        st.subheader(f"📖 Reviewing: {selected_subject}")
        st.info("💡 Read through these core concepts and concrete examples carefully. When you are ready, click the button in the left sidebar to hide the notes and unlock your quiz!")
        
        clean_markdown = subject_data['summary_markdown'].replace(r'\n', '\n')
        st.markdown(clean_markdown)
        
    # LAYOUT B: Testing & Feedback Mode
    else:
        st.subheader(f"🧠 Quiz Performance: {selected_subject}")
        
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
            # Main Interactive Evaluation Frame
            with st.container():
                user_answers = {}
                
                # Loop through all 5 items
                for i, q in enumerate(quiz_data):
                    st.write(f"**Q{i+1}: {q['question']}**")
                    
                    # Lock input index if submitted, otherwise leave blank
                    default_idx = None
                    if st.session_state[submitted_key]:
                        saved_val = st.session_state[saved_answers_key].get(i)
                        if saved_val in q['options']:
                            default_idx = q['options'].index(saved_val)
                    
                    user_answers[i] = st.radio(
                        "Select the best option:", 
                        options=q['options'], 
                        key=f"q_{target_day}_{selected_subject}_{i}", 
                        index=default_idx,
                        disabled=st.session_state[submitted_key]
                    )
                    st.write("---")
                
                # Bottom Action Button Handling
                if not st.session_state[submitted_key]:
                    if st.button("🚀 Submit Final Answers"):
                        unanswered = any(ans is None for ans in user_answers.values())
                        
                        if unanswered:
                            st.warning("⚠️ Please select an answer for all 5 questions before submitting.")
                        else:
                            score = 0
                            wrong_items = []
                            
                            for i, q in enumerate(quiz_data):
                                if user_answers[i] == q['correct_answer']:
                                    score += 1
                                else:
                                    wrong_items.append({
                                        "num": i + 1,
                                        "question": q['question'],
                                        "your_ans": user_answers[i],
                                        "correct_ans": q['correct_answer']
                                    })
                            
                            # Lock values directly into persistent memory matrices
                            st.session_state[score_key] = score
                            st.session_state[feedback_key] = wrong_items
                            st.session_state[saved_answers_key] = user_answers
                            st.session_state[submitted_key] = True
                            st.rerun()

            # PERSISTENT SCORE & FEEDBACK VIEW PANEL
            if st.session_state[submitted_key]:
                final_score = st.session_state[score_key]
                total_q = len(quiz_data)
                missed_list = st.session_state[feedback_key]
                
                st.markdown("### 📊 Your Results Breakdown")
                if final_score == total_q:
                    st.balloons()
                    st.success(f"🎉 Perfect Score! {final_score}/{total_q}. Outstanding retention!")
                elif final_score >= 3:
                    st.success(f"👍 Good effort! You scored {final_score}/{total_q}. Review the items missed below:")
                else:
                    st.warning(f"📚 You scored {final_score}/{total_q}. Let's read back through the lesson points after checking your answers below.")
                
                # Dynamic Expander List for Wrong Options
                if missed_list:
                    st.markdown("#### 🔍 Reviewing Missed Questions")
                    for item in missed_list:
                        with st.expander(f"❌ Question {item['num']}: {item['question']}"):
                            st.write(f"**Your Answer:** `{item['your_ans']}`")
                            st.write(f"**Correct Answer:** `{item['correct_ans']}`")
