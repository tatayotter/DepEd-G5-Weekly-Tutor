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

# 7. Render Lesson Summary & Dynamic Quiz Form with Anti-Cheat & Instant Feedback
if selected_subject:
    subject_data = day_data[selected_subject]
    quiz_data = subject_data.get('quiz', [])
    
    # Initialize session state keys unique to this specific subject segment
    submitted_key = f"submitted_{target_day}_{selected_subject}"
    score_key = f"score_{target_day}_{selected_subject}"
    feedback_key = f"feedback_{target_day}_{selected_subject}"
    saved_answers_key = f"saved_answers_{target_day}_{selected_subject}"
    
    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False
        st.session_state[score_key] = 0
        st.session_state[feedback_key] = []
        st.session_state[saved_answers_key] = {}

    checkbox_key = f"toggle_{target_day}_{selected_subject}"
    
    # Anti-Peeking Enforcement: Lock the view if the quiz has started but isn't submitted yet
    if checkbox_key in st.session_state and st.session_state[checkbox_key] and not st.session_state[submitted_key]:
        start_quiz = st.sidebar.checkbox("📝 Ready? Hide Notes & Start Quiz", value=True, disabled=True, key=f"disabled_{checkbox_key}")
        st.sidebar.caption("🔒 Notes are locked until you submit your answers.")
    else:
        start_quiz = st.sidebar.checkbox("📝 Ready? Hide Notes & Start Quiz", key=checkbox_key)
        st.sidebar.markdown("---")
    
    # Layout State A: Reading Mode (Quiz Hidden, Notes Visible)
    if not start_quiz:
        st.subheader(f"📖 Reviewing: {selected_subject}")
        st.info("💡 Read through these core concepts and concrete examples carefully. When you are ready, check the box in the left sidebar to hide the notes and unlock your quiz!")
        
        clean_markdown = subject_data['summary_markdown'].replace(r'\n', '\n')
        st.markdown(clean_markdown)
        
    # Layout State B: Testing Mode (Notes Hidden, Quiz Visible)
    else:
        st.subheader(f"🧠 Quiz Time: {selected_subject}")
        
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
            with st.form(key=f"secure_quiz_form_{target_day}_{selected_subject}"):
                user_answers = {}
                
                for i, q in enumerate(quiz_data):
                    st.write(f"**Q{i+1}: {q['question']}**")
                    
                    # If already submitted, read the saved selection out of memory; otherwise render fresh
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
                    
                if not st.session_state[submitted_key]:
                    submit_button = st.form_submit_button(label="Submit Answers")
                else:
                    submit_button = False
                    st.info("✅ You have completed this quiz. Uncheck the sidebar box if you want to review the study notes again.")
                
                # Grade the quiz immediately upon submission before state resets
                if submit_button:
                    unanswered = any(ans is None for ans in user_answers.values())
                    
                    if unanswered:
                        st.warning("⚠️ Please answer all questions before clicking submit.")
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
                        
                        # Save everything explicitly to session state
                        st.session_state[score_key] = score
                        st.session_state[feedback_key] = wrong_items
                        st.session_state[saved_answers_key] = user_answers
                        st.session_state[submitted_key] = True
                        st.rerun()

            # Display Results Panel (Persists flawlessly because data resides in session_state)
            if st.session_state[submitted_key]:
                final_score = st.session_state[score_key]
                total_q = len(quiz_data)
                missed_list = st.session_state[feedback_key]
                
                st.markdown("### 📊 Quiz Results")
                if final_score == total_q:
                    st.balloons()
                    st.success(f"🎉 Perfect Score! {final_score}/{total_q}. Outstanding retention!")
                elif final_score >= 3:
                    st.success(f"👍 Good effort! You scored {final_score}/{total_q}. Let's look closely at what to improve:")
                else:
                    st.warning(f"📚 You scored {final_score}/{total_q}. Let's treat this as a great practice run. Review the items below:")
                
                # Detailed Correction Breakdown Layout
                if missed_list:
                    st.markdown("### 🔍 Reviewing Missed Questions")
                    for item in missed_list:
                        with st.expander(f"❌ Question {item['num']}: {item['question']}"):
                            st.write(f"**Your Answer:** `{item['your_ans']}`")
                            st.write(f"**Correct Answer:** `{item['correct_ans']}`")
