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

# 3. Fetch Weekly Package from Supabase (FIXED TO PULL ALL COLUMNS)
response = supabase.table("weekly_packages") \
    .select("*") \
    .eq("week_starting_date", str(current_sunday)) \
    .execute()

package_data_list = response.data

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

# 6. Dynamic Subject Selection with "✅ DONE" Labels
selected_subject = None
if selected_day and day_data:
    # Pull current mastered list from database payload
    row_data = package_data_list[0] if package_data_list else {}
    db_mastered = row_data.get('mastered_quizzes', [])
    if not isinstance(db_mastered, list):
        db_mastered = []

    # Build a clean mapping list of display labels
    subject_options = []
    subject_mapping = {} # Maps display text back to the clean subject name

    for sub in day_data.keys():
        subject_uid = f"{selected_day}_{sub}"
        if subject_uid in db_mastered:
            display_label = f"{sub} ✅ DONE"
        else:
            display_label = sub
        
        subject_options.append(display_label)
        subject_mapping[display_label] = sub

    # Render the selector dropdown
    selected_display = st.sidebar.selectbox("📚 Choose Subject", options=subject_options)
    
    # Resolve clean subject string key for data lookups
    if selected_display:
        selected_subject = subject_mapping[selected_display]

# ==========================================
# 7. Render Lesson Summary & Gamified Dynamic Quiz Form (FULL ARCHITECTURE)
# ==========================================
if selected_subject:
    subject_data = day_data[selected_subject]
    quiz_data = subject_data.get('quiz', [])
    
    # Define persistent keys unique to this subject and day
    subject_uid = f"{target_day}_{selected_subject}"
    quiz_active_key = f"active_{subject_uid}"
    submitted_key = f"submitted_{subject_uid}"
    score_key = f"score_{subject_uid}"
    feedback_key = f"feedback_{subject_uid}"
    saved_answers_key = f"saved_answers_{subject_uid}"
    attempt_count_key = f"attempts_{subject_uid}"
    
    # Initialize basic quiz session states
    if quiz_active_key not in st.session_state:
        st.session_state[quiz_active_key] = False
    if submitted_key not in st.session_state:
        st.session_state[submitted_key] = False
        st.session_state[score_key] = 0
        st.session_state[feedback_key] = []
        st.session_state[saved_answers_key] = {}
        st.session_state[attempt_count_key] = 0

    # 🎮 FETCH DATA: Load fresh tracking records from current database row payload
    row_data = package_data_list[0] if package_data_list else {}
    
    # Read Character Stats Safely
    char_stats = row_data.get('character_stats', {"level": 1, "xp": 0, "gold": 0})
    if not isinstance(char_stats, dict):
        char_stats = {"level": 1, "xp": 0, "gold": 0}
        
    # Read Quiz Attempts Safely
    db_attempts = row_data.get('quiz_attempts', {})
    if not isinstance(db_attempts, dict):
        db_attempts = {}

    # Read Mastered Quizzes List Array Safely
    db_mastered = row_data.get('mastered_quizzes', [])
    if not isinstance(db_mastered, list):
        db_mastered = []
    
    # Determine mastery state
    is_already_mastered = subject_uid in db_mastered

    # Sync attempts database state to active local viewing session memory
    if st.session_state[attempt_count_key] == 0:
        st.session_state[attempt_count_key] = db_attempts.get(subject_uid, 0)

    # 🎮 SIDEBAR HUD: Render Character Sheet Widget (Using Live Database Values)
    st.sidebar.markdown("### 🛡️ Character Sheet")
    col_lvl, col_xp, col_gld = st.sidebar.columns(3)
    col_lvl.metric("Level", f"Lvl {char_stats.get('level', 1)}")
    col_xp.metric("XP", f"{char_stats.get('xp', 0)} / 1000")
    col_gld.metric("Gold", f"🪙 {char_stats.get('gold', 0)}")
    
    # Visual Experience Level Progress Bar
    st.sidebar.progress(min(char_stats.get('xp', 0) / 1000, 1.0))
    st.sidebar.markdown(f"🔢 Attempts Made for this subject: **{st.session_state[attempt_count_key]}**")
    st.sidebar.markdown("---")

    # SIDEBAR CONTROLLER: Manage Quiz Navigation States & Mastery Rules
    st.sidebar.markdown("### 🕹️ Quiz Status")
    if is_already_mastered:
        st.sidebar.success("🏆 Topic Mastered!")
        st.sidebar.caption("Maximum gold and XP already claimed for this quest!")
        # Force active state off to guarantee he stays in summary reading mode
        st.session_state[quiz_active_key] = False 
    elif st.session_state[submitted_key]:
        st.sidebar.success("✅ Evaluation Complete!")
        if st.sidebar.button("🔓 Open Study Notes Again"):
            st.session_state[quiz_active_key] = False
            st.session_state[submitted_key] = False  
            st.rerun()
    elif st.session_state[quiz_active_key]:
        st.sidebar.warning("🔒 Testing Mode Active")
        st.sidebar.caption("Study notes are locked away.")
    else:
        if st.sidebar.button("⚔️ Start Quest (Hide Notes)"):
            st.session_state[quiz_active_key] = True
            st.rerun()
            
    st.sidebar.markdown("---")

    # ==========================================
    # SCREEN ROUTING CONTROLLER
    # ==========================================
    
    # LAYOUT STATE A: Reading / Study Mode (Or View Mastered Mode)
    if is_already_mastered or (not st.session_state[quiz_active_key] and not st.session_state[submitted_key]):
        st.subheader(f"📖 Reviewing: {selected_subject}")
        if is_already_mastered:
            st.warning("✨ Excellent work! You unlocked a perfect score on this challenge and completed the quest! Review the information below as much as you like.")
        else:
            st.info("💡 Read through these core concepts and examples carefully. When you are ready to earn rewards, hit the sidebar button to lock the notes and start your quest!")
        
        clean_markdown = subject_data['summary_markdown'].replace(r'\n', '\n')
        st.markdown(clean_markdown)
        
    # LAYOUT STATE B: Active Testing / Feedback Mode
    else:
        st.subheader(f"⚔️ Active Quest: {selected_subject} Challenge")
        
        if not quiz_data:
            st.info("No quiz items found for this specific subject segment.")
        else:
            with st.container():
                user_answers = {}
                
                # Render Quiz Questions
                for i, q in enumerate(quiz_data):
                    st.write(f"**Q{i+1}: {q['question']}**")
                    
                    # Read saved choice if form is frozen after submission
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
                
                # Dynamic Submission Button Controls
                if not st.session_state[submitted_key]:
                    submit_button = st.button("🚀 Submit Final Answers")
                else:
                    submit_button = False
                
                # ==========================================
                # EVALUATION ENGINE (ON SUBMIT CLICK)
                # ==========================================
                if submit_button:
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
                        
                        # Process and record the attempt locally and for the DB
                        st.session_state[attempt_count_key] += 1
                        db_attempts[subject_uid] = st.session_state[attempt_count_key]
                        
                        level_up_occurred = False
                        xp_earned = 0
                        gold_earned = 0
                        
                        # Process rewards ONLY if they hit 5/5 and haven't mastered it before
                        if score == len(quiz_data) and not is_already_mastered:
                            xp_earned = 200
                            gold_earned = 50
                            
                            # First-Try Swift Mastery Payout
                            if st.session_state[attempt_count_key] == 1:
                                xp_earned += 100
                                gold_earned += 25  
                            # Second-Try Mastery Payout
                            elif st.session_state[attempt_count_key] == 2:
                                xp_earned += 50
                            
                            # Calculate new scaling totals
                            new_xp = char_stats.get('xp', 0) + xp_earned
                            new_gold = char_stats.get('gold', 0) + gold_earned
                            current_level = char_stats.get('level', 1)
                            
                            # Level up threshold limits (Every 1000 XP)
                            if new_xp >= 1000:
                                current_level += 1
                                new_xp = new_xp - 1000
                                level_up_occurred = True
                            
                            char_stats['xp'] = new_xp
                            char_stats['gold'] = new_gold
                            char_stats['level'] = current_level
                            
                            # Add this unique subject key to the mastery collection array
                            db_mastered.append(subject_uid)
                            
                            # Set flash notification state metrics
                            st.session_state[f"levelup_{subject_uid}"] = level_up_occurred
                            st.session_state[f"loot_xp_{subject_uid}"] = xp_earned
                            st.session_state[f"loot_gold_{subject_uid}"] = gold_earned
                        
                        # Commits all localized tracking arrays instantly to Supabase
                        try:
                            supabase.table("weekly_packages")\
                                .update({
                                    "quiz_attempts": db_attempts,
                                    "character_stats": char_stats,
                                    "mastered_quizzes": db_mastered
                                })\
                                .eq("week_starting_date", str(current_sunday))\
                                .execute()
                        except Exception as upload_err:
                            st.sidebar.error("⚠️ Failed to synchronize rewards to cloud database.")
                        
                        # Seal session parameters
                        st.session_state[score_key] = score
                        st.session_state[feedback_key] = wrong_items
                        st.session_state[saved_answers_key] = user_answers
                        st.session_state[submitted_key] = True
                        
                        # Hard refresh forces the layout to rebuild instantly with matching sidebar metrics
                        st.rerun()

            # ==========================================
            # PERSISTENT SCORE & CORRECTION FEEDBACK SCREEN
            # ==========================================
            if st.session_state[submitted_key]:
                final_score = st.session_state[score_key]
                total_q = len(quiz_data)
                missed_list = st.session_state[feedback_key]
                
                st.markdown("### 📊 Quest Summary")
                
                if final_score == total_q:
                    if st.session_state.get(f"levelup_{subject_uid}", False):
                        st.balloons()
                        st.success(f"👑 **LEVEL UP! You reached Level {char_stats.get('level')}!** Outstanding growth!")
                    else:
                        st.balloons()
                        st.success(f"🎉 **Perfect Mastery! Score: {final_score}/{total_q}**")
                    
                    xp_got = st.session_state.get(f"loot_xp_{subject_uid}", 200)
                    gold_got = st.session_state.get(f"loot_gold_{subject_uid}", 50)
                    
                    st.markdown(f"""
                    ### 🎁 Quest Loot Awarded:
                    * **✨ Experience:** `+{xp_got} XP`
                    * **🪙 Gold Tokens:** `+{gold_got} Gold`
                    """)
                elif final_score >= 3:
                    st.success(f"👍 Good effort! You scored {final_score}/{total_q}. Review your mistakes below, open the notes, and try again to unlock the gold reward!")
                else:
                    st.warning(f"📚 You scored {final_score}/{total_q}. Let's re-read the study material closely before your next challenge attempt.")
                
                # Render expanding mistake panels if errors exist
                if missed_list:
                    st.markdown("#### 🔍 Quest Logs: Missed Targets")
                    for item in missed_list:
                        with st.expander(f"❌ Question {item['num']}: {item['question']}"):
                            st.write(f"**Your Answer:** `{item['your_ans']}`")
                            st.write(f"**Correct Answer:** `{item['correct_ans']}`")
